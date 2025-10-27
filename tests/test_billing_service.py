"""
Unit tests for the BillingService class.
"""

import pytest
import boto3
from moto import mock_dynamodb, mock_sqs
from src.lambda.billing.billing_service import BillingService
from src.utils.config import Config

@pytest.fixture
def billing_service():
    """Fixture for BillingService instance."""
    with mock_dynamodb(), mock_sqs():
        dynamodb = boto3.client("dynamodb")
        sqs = boto3.client("sqs")
        dynamodb.create_table(
            TableName="saas-billing",
            KeySchema=[{"AttributeName": "tenant_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "tenant_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        queue = sqs.create_queue(QueueName="billing-queue")
        Config().config["sqs"] = {"billing_queue": queue["QueueUrl"]}
        return BillingService()

def test_track_usage(billing_service):
    """Test tracking usage for a tenant."""
    record = {
        "NewImage": {
            "tenant_id": {"S": "tenant1"},
            "usage": {"N": "10"}
        }
    }
    billing_service.track_usage("tenant1", record)
    summary = billing_service.get_billing_summary("tenant1")
    assert summary["usage_count"] == 10
    assert summary["total_cost"] == 0.1  # 10 * 0.01