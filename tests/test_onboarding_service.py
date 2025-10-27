"""
Unit tests for the OnboardingService class.
"""

import pytest
import boto3
from moto import mock_dynamodb, mock_cognitoidp
from src.lambda.onboarding.onboarding_service import OnboardingService
from src.utils.config import Config

@pytest.fixture
def onboarding_service():
    """Fixture for OnboardingService instance."""
    with mock_dynamodb(), mock_cognitoidp():
        dynamodb = boto3.client("dynamodb")
        cognito = boto3.client("cognito-idp")
        dynamodb.create_table(
            TableName="saas-tenant-data",
            KeySchema=[
                {"AttributeName": "tenant_id", "KeyType": "HASH"},
                {"AttributeName": "item_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "tenant_id", "AttributeType": "S"},
                {"AttributeName": "item_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        user_pool = cognito.create_user_pool(PoolName="SaaSUserPool")
        client = cognito.create_user_pool_client(UserPoolId=user_pool["UserPool"]["Id"], ClientName="AppClient")
        Config().config["auth"] = {
            "cognito_user_pool_id": user_pool["UserPool"]["Id"],
            "cognito_client_id": client["UserPoolClient"]["ClientId"]
        }
        return OnboardingService()

def test_register_tenant(onboarding_service):
    """Test tenant registration."""
    tenant_id = onboarding_service.register_tenant("Acme Corp", "admin@acme.com", "SecurePassword123!")
    assert tenant_id is not None
    response = onboarding_service.dynamodb.get_item(
        TableName="saas-tenant-data",
        Key={"tenant_id": {"S": tenant_id}, "item_id": {"S": "tenant_info"}}
    )
    assert response.get("Item") is not None