from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs: object) -> None:
        super().__init__(scope, id, **kwargs)

        # Define a VPC with smaller CIDR block and optimize for smaller-scale use cases
        self.vpc = ec2.Vpc(
            self,
            "SharedVPC",
            max_azs=2,  # 2 Availability Zones for fault tolerance, you can change to 3 for more resiliency
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/20"),  # A smaller CIDR block (4,096 IP addresses)
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,  # This subnet will have 256 IP addresses
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,  # This subnet will also have 256 IP addresses
                ),
            ],
        )
