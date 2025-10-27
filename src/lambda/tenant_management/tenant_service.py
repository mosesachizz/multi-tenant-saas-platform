"""
Tenant service for managing tenant-specific data with strict isolation.
"""

import boto3
from typing import Dict, Optional
from ..utils.logger import setup_logger
from ..utils.config import Config
from ..utils.metrics import MetricsCollector

class TenantService:
    """Manages tenant data with DynamoDB and strict isolation."""
    
    def __init__(self):
        """Initialize the tenant service."""
        self.logger = setup_logger(__name__)
        self.config = Config()
        self.dynamodb = boto3.client("dynamodb")
        self.table_name = self.config.get("dynamodb.table_name", "saas-tenant-data")
        self.metrics = MetricsCollector()

    def get_tenant_data(self, tenant_id: str, item_id: str, user: dict) -> Optional[dict]:
        """Retrieve tenant-specific data with strict isolation.
        
        Args:
            tenant_id: Tenant identifier.
            item_id: Item identifier.
            user: Cognito user claims.
        
        Returns:
            Optional[dict]: Retrieved item or None if not found.
        """
        try:
            # Verify tenant access
            if user.get("tenant_id") != tenant_id:
                self.logger.error("Unauthorized access to tenant %s by user %s", tenant_id, user.get("sub"))
                raise ValueError("Unauthorized tenant access")
            
            # Query DynamoDB with tenant partition key
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={"tenant_id": {"S": tenant_id}, "item_id": {"S": item_id}}
            )
            item = response.get("Item")
            if not item:
                self.logger.warning("Item %s not found for tenant %s", item_id, tenant_id)
                self.metrics.record_data_access_failure()
                return None
            
            # Log metrics
            self.metrics.record_data_access_success()
            self.logger.info("Retrieved item %s for tenant %s", item_id, tenant_id)
            return item
        except Exception as e:
            self.logger.error("Failed to retrieve tenant data: %s", str(e))
            self.metrics.record_error()
            raise

    def store_tenant_data(self, tenant_id: str, item_id: str, data: dict, user: dict):
        """Store tenant-specific data.
        
        Args:
            tenant_id: Tenant identifier.
            item_id: Item identifier.
            data: Data to store.
            user: Cognito user claims.
        """
        try:
            if user.get("tenant_id") != tenant_id:
                self.logger.error("Unauthorized store to tenant %s by user %s", tenant_id, user.get("sub"))
                raise ValueError("Unauthorized tenant access")
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    "tenant_id": {"S": tenant_id},
                    "item_id": {"S": item_id},
                    "data": {"S": json.dumps(data)}
                }
            )
            self.logger.info("Stored item %s for tenant %s", item_id, tenant_id)
            self.metrics.record_data_access_success()
        except Exception as e:
            self.logger.error("Failed to store tenant data: %s", str(e))
            self.metrics.record_error()
            raise