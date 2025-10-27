"""
Unit tests for the TenantService class.
"""

import pytest
import boto3
from moto import mock_dynamodb
from src.lambda.tenant_management.tenant_service import TenantService
from src.utils.config import Config

@pytest.fixture
def tenant_service():
    """Fixture for TenantService instance."""
    with mock_dynamodb():
        dynamodb = boto3.client("dynamodb")
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
        return TenantService()

def test_get_tenant_data_valid(tenant_service):
    """Test retrieving tenant data with valid access."""
    tenant_service.dynamodb.put_item(
        TableName="saas-tenant-data",
        Item={"tenant_id": {"S": "tenant1"}, "item_id": {"S": "item1"}, "data": {"S": "{}"}}
    )
    user = {"tenant_id": "tenant1", "sub": "user1"}
    result = tenant_service.get_tenant_data("tenant1", "item1", user)
    assert result is not None
    assert result["tenant_id"]["S"] == "tenant1"

def test_get_tenant_data_unauthorized(tenant_service):
    """Test unauthorized tenant access."""
    user = {"tenant_id": "tenant2", "sub": "user1"}
    with pytest.raises(ValueError, match="Unauthorized tenant access"):
        tenant_service.get_tenant_data("tenant1", "item1", user)