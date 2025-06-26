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

        # Define the EKS Cluster
        eks_cluster = eks.Cluster(
            self,
            "EKSCluster",
            version=eks.KubernetesVersion.V1_30,
            vpc=vpc,
            default_capacity=2,
            kubectl_layer=aws_cdk.lambda_layer_kubectl_v33.KubectlV33Layer(self, "KubectlLayer"),
        )

        # Define the IAM user 'bmschool'
        admin_user = iam.User.from_user_arn(self, "AdminUser", "arn:aws:iam::os:user/bmlschool")

        # Add the IAM user to the 'system:masters' Kubernetes group for admin access
        eks_cluster.aws_auth.add_user_mapping(
            admin_user,  # Use admin_user here
            groups=["system:masters"],
        )

        # Define the IAM Role for the node group
        nodegroup_role = iam.Role(
            self,
            "NodeGroupRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
            ],
        )

        # Add a managed node group
        eks_cluster.add_nodegroup_capacity(
            "ExtraNodeGroup",
            desired_size=2,
            min_size=1,
            max_size=3,
            instance_types=[ec2.InstanceType("t3.medium")],
            disk_size=20,
            node_role=nodegroup_role,
        )
