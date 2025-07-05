import os

import aws_cdk.lambda_layer_kubectl_v33
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()


class EKSStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs: object) -> None:
        super().__init__(scope, id, **kwargs)

        # Define the EKS Cluster (Fargate)
        eks_cluster = eks.Cluster(
            self,
            "EKSCluster",
            version=eks.KubernetesVersion.V1_32,
            vpc=vpc,
            default_capacity=0,  # No default EC2 worker nodes
            kubectl_layer=aws_cdk.lambda_layer_kubectl_v33.KubectlV33Layer(self, "KubectlLayer"),
        )

        # Define the IAM user
        admin_user = iam.User.from_user_arn(
            self, "AdminUser", f"arn:aws:iam::{os.getenv('AWS_ACCOUNT_ID')}:user/{os.getenv('IAM_USER')}"
        )

        # Add the IAM user to the 'system:masters' Kubernetes group for admin access
        eks_cluster.aws_auth.add_user_mapping(
            admin_user,  # Use admin_user here
            groups=["system:masters"],
        )

        # Create the Pod Execution Role for Fargate Profile
        pod_execution_role = iam.Role(
            self,
            "PodExecutionRole",
            assumed_by=iam.ServicePrincipal("eks-fargate-pods.amazonaws.com"),
            managed_policies=[
                # Required for Fargate pod execution
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSFargatePodExecutionRolePolicy"),
                # # Allow full EC2 access
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                # Allow CloudWatch logging (if you're logging)
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
                # Access to ECR (if pulling container images from ECR)
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                # Permissions for EKS networking
                iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
            ],
        )

        # Define Fargate Profile for system pods (CoreDNS, etc.)
        eks_cluster.add_fargate_profile(
            "SystemFargateProfile",
            selectors=[{"namespace": "kube-system"}],
            pod_execution_role=pod_execution_role,
        )

        # Define Fargate Profile for FastAPI app
        eks_cluster.add_fargate_profile(
            "AppFargateProfile",
            selectors=[{"namespace": "my-app", "labels": {"app": "fastapi"}}],
            pod_execution_role=pod_execution_role,
        )

        # # Add ConfigMap and Secrets for the FastAPI app
        # eks_cluster.add_manifest(
        #     "AppConfigMap",
        #     {
        #         "apiVersion": "v1",
        #         "kind": "ConfigMap",
        #         "metadata": {
        #             "name": "app-config",
        #             "namespace": "my-app"
        #         },
        #         "data": {
        #             "APP_ENV": "prod",
        #             "AWS_REGION": os.getenv("AWS_REGION"),
        #             "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        #             "POSTGRES_PORT": os.getenv("POSTGRES_PORT"),
        #             "ADMINER_PORT": os.getenv("ADMINER_PORT"),
        #             "ISSUES_TABLE_NAME": os.getenv("ISSUES_TABLE_NAME"),
        #             "COMMENTS_TABLE_NAME": os.getenv("COMMENTS_TABLE_NAME"),
        #             "DENSE_MODEL_NAME": os.getenv("DENSE_MODEL_NAME"),
        #             "SPARSE_MODEL_NAME": os.getenv("SPARSE_MODEL_NAME"),
        #             "LEN_EMBEDDINGS": os.getenv("LEN_EMBEDDINGS"),
        #             "COLLECTION_NAME": os.getenv("COLLECTION_NAME"),
        #             "CHUNK_SIZE": os.getenv("CHUNK_SIZE"),
        #             "BATCH_SIZE": os.getenv("BATCH_SIZE"),
        #             "CONCURRENT_COMMENTS": os.getenv("CONCURRENT_COMMENTS"),
        #             "LLM_MODEL_NAME": os.getenv("LLM_MODEL_NAME"),
        #             "TEMPERATURE": os.getenv("TEMPERATURE"),
        #             "REPOS_CONFIG": "src/config/repos.yaml",
        #             "GUARDRAILS_CONFIG": "src/config/guardrails.yaml",
        #         }
        #     }
        # )

        # # Add this after creating your `eks_cluster`
        # eks_cluster.add_manifest(
        #     "AppSecrets",
        #     {
        #         "apiVersion": "v1",
        #         "kind": "Secret",
        #         "metadata": {
        #             "name": "app-secrets",
        #             "namespace": "my-app"
        #         },
        #         "type": "Opaque",
        #         "stringData": {
        #             "GH_TOKEN": os.getenv("GH_TOKEN"),
        #             "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        #             "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        #             "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        #             "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
        #             "QDRANT_URL": os.getenv("QDRANT_URL"),
        #             "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY"),
        #             "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        #             "GUARDRAILS_API_KEY": os.getenv("GUARDRAILS_API_KEY"),
        #             "SECRET_NAME": os.getenv("SECRET_NAME"),
        #         }
        #     }
        # )
