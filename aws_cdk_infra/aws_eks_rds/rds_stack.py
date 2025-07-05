import os
from typing import Any

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()


class RDSStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs: Any):
        super().__init__(scope, id, **kwargs)

        credentials = rds.Credentials.from_generated_secret(os.getenv("POSTGRES_USER"))

        security_group = ec2.SecurityGroup(
            self,
            "RDSSecurityGroup",
            vpc=vpc,
            description="Allow internal access to PostgreSQL",
            allow_all_outbound=True,
        )

        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
        )

        # Allow access only from your specific IP (use your real public IP here)
        my_public_ip = os.getenv("MY_PUBLIC_IP")
        if my_public_ip:
            security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(f"{my_public_ip}/32"),
                connection=ec2.Port.tcp(5432),
                description="Allow external access to PostgreSQL from my IP",
            )
        else:
            raise ValueError("Environment variable MY_PUBLIC_IP is not set.")

        rds.DatabaseInstance(
            self,
            "PostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16_3),
            vpc=vpc,
            credentials=credentials,
            # vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[security_group],
            database_name=os.getenv("POSTGRES_DB"),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            allocated_storage=20,
            max_allocated_storage=100,
            # publicly_accessible=False,
            publicly_accessible=True,
            multi_az=False,
            backup_retention=Duration.days(7),
            removal_policy=RemovalPolicy.DESTROY,
        )
