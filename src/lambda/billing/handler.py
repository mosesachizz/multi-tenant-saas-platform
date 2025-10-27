"""
Lambda handler for usage-based billing operations.
"""

import json
from typing import Dict, Any
from .billing_service import BillingService
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()
billing_service = BillingService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle billing-related API and DynamoDB Streams events.
    
    Args:
        event: API Gateway or DynamoDB Streams event.
        context: Lambda context.
    
    Returns:
        Dict: API response or None for stream processing.
    """
    try:
        # Handle DynamoDB Streams event for usage tracking
        if "Records" in event:
            for record in event["Records"]:
                if record["eventName"] in ["INSERT", "MODIFY"]:
                    tenant_id = record["dynamodb"]["Keys"]["tenant_id"]["S"]
                    billing_service.track_usage(tenant_id, record["dynamodb"])
            return {"statusCode": 200, "body": json.dumps({"message": "Usage processed"})}
        
        # Handle API Gateway request
        http_method = event["httpMethod"]
        path = event["path"]
        user = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
        
        if http_method == "GET" and "/billing/{tenant_id}" in path:
            tenant_id = event["pathParameters"]["tenant_id"]
            if user.get("tenant_id") != tenant_id:
                return {"statusCode": 403, "body": json.dumps({"error": "Unauthorized"})}
            billing_summary = billing_service.get_billing_summary(tenant_id)
            return {"statusCode": 200, "body": json.dumps(billing_summary)}
        
        else:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid request"})}
    
    except Exception as e:
        logger.error("Billing error: %s", str(e))
        metrics.record_error()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}