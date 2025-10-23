"""
Onboarding service for registering new tenants with Cognito.
"""

import boto3
import uuid
from typing import Dict
from ..utils.logger import setup_logger
from ..utils.config import Config
from ..utils.metrics import MetricsCollector

class OnboardingService:
    """Manages tenant registration and Cognito user creation."""
    
    def __init__(self):
        """Initialize the onboarding service."""
        self.logger = setup_logger(__name__)
        self.config = Config()
        self.cognito = boto3.client("cognito-idp")
        self.dynamodb = boto3.client("dynamodb")
        self.user_pool_id = self.config.get("auth.cognito_user_pool_id", "")
        self.table_name = self.config.get("dynamodb.table_name", "saas-tenant-data")
        self.metrics = MetricsCollector()

    def register_tenant(self, tenant_name: str, email: str, password: str) -> str:
        """Register a new tenant and create Cognito user.
        
        Args:
            tenant_name: Name of the tenant.
            email: Admin email for the tenant.
            password: Admin password.
        
        Returns:
            str: Generated tenant ID.
        """
        try:
            tenant_id = str(uuid.uuid4())
            # Create Cognito user
            self.cognito.sign_up(
                ClientId=self.config.get("auth.cognito_client_id", ""),
                Username=email,
                Password=password,
                UserAttributes=[
                    {"Name": "custom:tenant_id", "Value": tenant_id},
                    {"Name": "email", "Value": email}
                ]
            )
            # Confirm user (admin flow for simplicity)
            self.cognito.admin_confirm_sign_up(
                UserPoolId=self.user_pool_id,
                Username=email
            )
            # Initialize tenant in DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    "tenant_id": {"S": tenant_id},
                    "item_id": {"S": "tenant_info"},
                    "data": {"S": json.dumps({"tenant_name": tenant_name, "created_at": str(datetime.now())})}
                }
            )
            self.logger.info("Registered tenant %s with ID %s", tenant_name, tenant_id)
            return tenant_id
        except Exception as e:
            self.logger.error("Failed to register tenant %s: %s", tenant_name, str(e))
            self.metrics.record_error()
            raise