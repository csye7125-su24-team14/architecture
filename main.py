from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Deploy, Pod, StatefulSet, Job, DaemonSet
from diagrams.k8s.network import Ing, SVC, NetworkPolicy
from diagrams.k8s.storage import PV
from diagrams.k8s.others import CRD
from diagrams.onprem.queue import Kafka
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.network import Istio
from diagrams.aws.network import ELB, Route53
from diagrams.aws.security import SecretsManager
from diagrams.aws.management import Cloudwatch
from diagrams.onprem.vcs import Github
from diagrams.onprem.ci import Jenkins
from diagrams.onprem.container import Docker
from diagrams.onprem.iac import Terraform
from diagrams.aws.compute import EC2, EC2Ami, EC2AutoScaling
from diagrams.generic.device import Mobile
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white"
}

with Diagram("K8s-VulnSage", show=False, direction="TB", graph_attr=graph_attr):
    # External User
    user = Mobile("User")

    # AWS Route 53
    route53 = Route53("Route 53")

    # Part 1 and 2: Development and Infrastructure
    with Cluster("Development and Infrastructure"):
        developer = Custom("Developer", "resources/developer.png")
        fork_repo = Github("Fork Repo")
        pr_checks = Jenkins("PR Checks")
        org_repo = Github("Org Repo")
        ci_job = Jenkins("CI Job")
        docker_hub = Docker("Docker Hub")
        github_release = Github("GitHub Release")
        
        helm_charts = Custom("Helm Charts","resources/helm.png")
        
        packer = Custom("Packer", "resources/packer.png")
        jenkins_ami = EC2Ami("Jenkins AMI")
        terraform_jenkins = Terraform("Terraform (Jenkins)")
        jenkins_ec2 = EC2("Jenkins EC2")
        
        developer >> fork_repo >> pr_checks >> org_repo >> ci_job
        ci_job >> docker_hub
        ci_job >> Edge(label="Semantic Release") >> github_release
        ci_job >> Edge(label="Publish Package") >> github_release
        
        packer >> jenkins_ami >> terraform_jenkins >> jenkins_ec2

    # Part 3: EKS Cluster
    with Cluster("EKS Cluster"):
        terraform_eks = Terraform("Terraform (EKS)")
        
        cluster_autoscaler = EC2AutoScaling("Cluster Autoscaler")
        
        with Cluster("EKS Nodes"):
            with Cluster("Node 1"):
                with Cluster("istio-system"):
                    istio_ingress = Ing("Istio Ingress")
                    istio_gateway = Istio("Istio Gateway")
                    virtual_service = Istio("Virtual Service")
                    cert_manager = Deploy("Cert Manager")
                    external_dns = Deploy("External DNS")
                    envoy_istio = Custom("Envoy", "resources/envoy.png")

                with Cluster("webapp-cve-producer"):
                    cve_operator = Deploy("CVE Operator")
                    github_monitor = CRD("GithubReleaseMonitor CRD")
                    github_release_cr = CRD("GithubRelease CR")
                    github_release_job = Job("GithubRelease Job")
                    envoy_producer = Custom("Envoy", "resources/envoy.png")

                with Cluster("kafka"):
                    kafka = Kafka("Kafka")
                    kafka_hpa = Deploy("Kafka HPA")
                    envoy_kafka = Custom("Envoy", "resources/envoy.png")

                with Cluster("webapp-cve-consumer"):
                    consumer = Deploy("Consumer")
                    consumer_hpa = Deploy("Consumer HPA")
                    envoy_consumer = Custom("Envoy", "resources/envoy.png")

                with Cluster("postgres"):
                    postgres = StatefulSet("PostgreSQL")
                    postgres_pv = PV("Persistent Volume")
                    postgres_netpol = NetworkPolicy("Network Policy")
                    envoy_postgres = Custom("Envoy", "resources/envoy.png")

                with Cluster("monitoring"):
                    grafana = Grafana("Grafana")
                    kiali = Custom("Kiali", "./kiali.png")
                    prometheus = Prometheus("Prometheus")
                    tempo = Jaeger("Tempo")
                    envoy_monitoring = Custom("Envoy", "resources/envoy.png")

                with Cluster("cve-rag-app"):
                    embedding_job = Job("Embedding Job")
                    cve_rag_app = Deploy("CVE RAG App")
                    cve_rag_hpa = Deploy("CVE RAG HPA")
                    streamlit = Custom("Streamlit App", "resources/streamlit.png")
                    envoy_rag = Custom("Envoy", "./envoy.png")

                with Cluster("amazon-cloudwatch"):
                    fluent_bit = DaemonSet("Fluent Bit")
                    envoy_cloudwatch = Custom("Envoy", "resources/envoy.png")

            node2 = EC2("Node 2\n(Similar to Node 1)")
            node3 = EC2("Node 3\n(Similar to Node 1)")

        # External Services
        nlb = ELB("AWS NLB")
        cloudwatch = Cloudwatch("CloudWatch")
        github_ext = Github("GitHub")
        pinecone = Custom("Pinecone", "resources/pincone.png")
        groq = Custom("Groq (LLama3)", "resources/groq.png")

        # AWS Secrets Manager
        secrets_manager = SecretsManager("Secrets Manager")

    # Connections
    terraform_eks >> [node2, node3]
    terraform_eks >> cluster_autoscaler
    
    # Updated user flow
    user >> route53
    route53 >> Edge(color="darkgreen", style="bold") >> user
    user >> Edge(color="darkgreen", style="bold") >> nlb
    
    nlb >> istio_ingress >> istio_gateway >> virtual_service
    virtual_service >> Edge(color="red") >> grafana
    virtual_service >> Edge(color="green") >> kiali
    virtual_service >> Edge(color="blue") >> streamlit

    # Data flow
    github_ext >> github_monitor >> github_release_cr >> github_release_job >> kafka >> consumer >> postgres
    kafka >> embedding_job
    
    embedding_job >> pinecone
    cve_rag_app >> groq
    fluent_bit >> cloudwatch

    # Helm charts
    helm_charts >> Edge(label="Pull Helm Charts", style="dashed") >> terraform_eks

    # Secrets Manager
    secrets_manager >> Edge(label="Fetch Secrets", style="dashed") >> terraform_eks