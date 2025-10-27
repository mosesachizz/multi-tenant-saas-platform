"""
Billing service for tracking usage and generating invoices.
"""

import boto3
import json
from typing import Dict
from ..utils.logger import setup_logger
from ..utils.config import Config
from ..utils.metrics import MetricsCollector

class BillingService:
    """Manages usage tracking and billing for tenants."""
    
    def __init__(self):
        """Initialize the billing service."""
        self.logger = setup_logger(__name__)
        self.config = Config()
        self.dynamodb = boto3.client("dynamodb")
        self.sqs = boto3.client("sqs")
        self.table_name = self.config.get("dynamodb.billing_table", "saas-billing")
        self.queue_url = self.config.get("sqs.billing_queue", "")
        self.metrics = MetricsCollector()

    def track_usage(self, tenant_id: str, record: Dict):
        """Track tenant usage from DynamoDB Streams.
        
        Args:
            tenant_id: Tenant identifier.
            record: DynamoDB Stream record.
        """
        try:
            usage = record.get("NewImage", {}).get("usage", {}).get("N", "0")
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={"tenant_id": {"S": tenant_id}},
                UpdateExpression="SET usage_count = usage_count + :val",
                ExpressionAttributeValues={":val": {"N": usage}},
                ReturnValues="UPDATED_NEW"
            )
            # Send to SQS for async invoice generation
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps({"tenant_id": tenant_id, "usage": int(usage)})
            )
            self.logger.info("Tracked usage for tenant %s: %s", tenant_id, usage)
            self.metrics.record_billing_update()
        except Exception as e:
            self.logger.error("Failed to track usage for tenant %s: %s", tenant_id, str(e))
            self.metrics.record_error()
            raise

    def get_billing_summary(self, tenant_id: str) -> Dict:
        """Retrieve billing summary for a tenant.
        
        Args:
            tenant_id: Tenant identifier.
        
        Returns:
            Dict: Billing summary.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={"tenant_id": {"S": tenant_id}}
            )
            item = response.get("Item", {})
            usage_count = int(item.get("usage_count", {}).get("N", "0"))
            cost_per_unit = self.config.get("billing.cost_per_unit", 0.01)
            total_cost = usage_count * cost_per_unit
            summary = {
                "tenant_id": tenant_id,
                "usage_count": usage_count,
                "total_cost": round(total_cost, 2)
            }
            self.logger.info("Billing summary for tenant %s: %s", tenant_id, summary)
            return summary
        except Exception as e:
            self.logger.error("Failed to retrieve billing summary for tenant %s: %s", tenant_id, str(e))
            self.metrics.record_error()
            raise