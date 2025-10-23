"""
CDK stack for defining the SaaS platform infrastructure.
"""

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda_event_sources as event_sources
)
from constructs import Construct

class SaaSStack(Stack):
    """CDK stack for the Multi-Tenant SaaS Platform."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        """Initialize the stack."""
        super().__init__(scope, construct_id, **kwargs)
        
        # DynamoDB table for tenant data
        tenant_table = dynamodb.Table(
            self, "TenantDataTable",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="item_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # DynamoDB table for billing
        billing_table = dynamodb.Table(
            self, "BillingTable",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        # SQS queue for billing
        billing_queue = sqs.Queue(self, "BillingQueue")
        
        # SNS topic for notifications
        notification_topic = sns.Topic(self, "NotificationTopic")
        
        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "UserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            user_pool_name="SaaSUserPool",
            custom_attributes={
                "tenant_id": cognito.StringAttribute(mutable=True)
            }
        )
        client = user_pool.add_client("AppClient")
        
        # Lambda functions
        tenant_lambda = _lambda.Function(
            self, "TenantManagementFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda/tenant_management"),
            environment={
                "TABLE_NAME": tenant_table.table_name,
                "USER_POOL_ID": user_pool.user_pool_id
            }
        )
        billing_lambda = _lambda.Function(
            self, "BillingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda/billing"),
            environment={
                "BILLING_TABLE": billing_table.table_name,
                "SQS_QUEUE_URL": billing_queue.queue_url
            }
        )
        onboarding_lambda = _lambda.Function(
            self, "OnboardingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda/onboarding"),
            environment={
                "TABLE_NAME": tenant_table.table_name,
                "USER_POOL_ID": user_pool.user_pool_id,
                "COGNITO_CLIENT_ID": client.user_pool_client_id
            }
        )
        
        # Grant permissions
        tenant_table.grant_read_write_data(tenant_lambda)
        billing_table.grant_read_write_data(billing_lambda)
        tenant_table.grant_read_write_data(onboarding_lambda)
        billing_queue.grant_send_messages(billing_lambda)
        user_pool.grant(onboarding_lambda, "cognito-idp:AdminConfirmSignUp")
        billing_lambda.add_event_source(event_sources.DynamoEventSource(
            table=tenant_table,
            starting_position=_lambda.StartingPosition.LATEST
        ))
        
        # API Gateway
        api = apigateway.RestApi(self, "SaaSApi")
        api.root.add_resource("tenants").add_resource("{tenant_id}").add_resource("data").add_resource("{item_id}").add_method(
            "GET", apigateway.LambdaIntegration(tenant_lambda),
            authorizer=apigateway.CognitoUserPoolsAuthorizer(
                self, "CognitoAuthorizer",
                cognito_user_pools=[user_pool]
            )
        )
        api.root.add_resource("tenants").add_resource("{tenant_id}").add_resource("data").add_method(
            "POST", apigateway.LambdaIntegration(tenant_lambda),
            authorizer=apigateway.CognitoUserPoolsAuthorizer(
                self, "CognitoAuthorizer2",
                cognito_user_pools=[user_pool]
            )
        )
        api.root.add_resource("billing").add_resource("{tenant_id}").add_method(
            "GET", apigateway.LambdaIntegration(billing_lambda),
            authorizer=apigateway.CognitoUserPoolsAuthorizer(
                self, "CognitoAuthorizer3",
                cognito_user_pools=[user_pool]
            )
        )
        api.root.add_resource("onboarding").add_method(
            "POST", apigateway.LambdaIntegration(onboarding_lambda)
        )