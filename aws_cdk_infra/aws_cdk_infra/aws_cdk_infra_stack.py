import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_rds as rds,
)
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")


class GithubIssuesIntelligenceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a VPC for your resources
        # A VPC is essential for networking the database. Here we create a new one.
        vpc = ec2.Vpc(
            self,
            "GithubIssuesIntelligenceVPC",
            max_azs=2,  # Deploy across two Availability Zones for high availability
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),  # Example CIDR range
            subnet_configuration=[
                ec2.SubnetConfiguration(name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,  # Subnet for the database
                    cidr_mask=24,
                ),
            ],
        )

        # 2. Create a Security Group for the RDS instance
        # This controls what network traffic can reach the database
        db_security_group = ec2.SecurityGroup(
            self,
            "RDS-SecurityGroup",
            vpc=vpc,
            description="Allow access to RDS PostgreSQL",
            allow_all_outbound=True,  # Allow all outbound connections from the database
        )

        # Allow inbound connections on PostgreSQL default port (5432) from within the VPC.
        # For a "production" environment, we would usually restrict this to specific EC2 instances
        # or services that need to connect to the database. For showcase, we open
        # it up more broadly within the VPC or even to your local IP for testing (temporarily).
        # For a truly secure setup, you would connect via a bastion host or a VPN.
        db_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),  # Allow access from any IP in your VPC
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from VPC",
        )

        ## vpc_subnets MUST BE ALSO CHANGED TO PUBLIC AND publicly_accessible TO TRUE in the database_instance
        # If you need to access from your local machine *for testing/showcase purposes only*,
        # you can temporarily add your public IP address (find yours by searching "what is my ip").
        # REMOVE THIS FOR A REAL PRODUCTION ENVIRONMENT.
        # db_security_group.add_ingress_rule(
        #     peer=ec2.Peer.ipv4("XXX.XXX.XXX.XX/32"),
        #     connection=ec2.Port.tcp(5432),
        #     description="Allow PostgreSQL access from my local IP"
        # )

        credentials = rds.Credentials.from_generated_secret(POSTGRES_USER)

        # 3. Create the RDS PostgreSQL Database Instance
        database_instance = rds.DatabaseInstance(
            self,
            "GithubIssuesDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3  # Choose a suitable PostgreSQL version
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),  # Place in private subnets
            # vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,  # Cost-effective
                ec2.InstanceSize.MICRO,  # Or MEDIUM if expected more load later
            ),
            security_groups=[db_security_group],
            database_name=POSTGRES_DB,
            credentials=credentials,  # Managed secret for credentials
            allocated_storage=20,  # GB, minimum for PostgreSQL
            max_allocated_storage=100,  # Allow storage to scale up to 100 GB
            multi_az=False,  # Set to True for higher availability (more costly)
            allow_major_version_upgrade=False,
            auto_minor_version_upgrade=True,
            backup_retention=cdk.Duration.days(7),  # noqa # Retain backups for 7 days
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self,
                "PostgresParamGroup",
                "default.postgres16",  # Use the default parameter group for Postgres 15
            ),
            publicly_accessible=False,  # Keep database private for security
            # publicly_accessible=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,  # noqa  # CAUTION: DESTROYS DATABASE ON CDK DESTROY. USE RETAIN FOR PRODUCTION.
        )

        # Output the database endpoint for your reference
        CfnOutput(self, "DBEndpoint", value=database_instance.db_instance_endpoint_address)
        CfnOutput(self, "DBPort", value=str(database_instance.db_instance_endpoint_port))
        CfnOutput(self, "DBUser", value="github-issues-db-credentials")  # This is the secret name, not the username
        # The actual username and password will be in the secret.
