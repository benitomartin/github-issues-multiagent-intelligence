import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_cdk_infra.aws_cdk_infra_stack import GithubIssuesIntelligenceStack


# example tests. To run these tests, uncomment this file along with the example
# resource in aws_cdk_infra/aws_cdk_infra_stack.py
def test_sqs_queue_created() -> None:
    app = core.App()
    stack = GithubIssuesIntelligenceStack(app, "aws-cdk-infra")
    template = assertions.Template.from_stack(stack)  # noqa


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
