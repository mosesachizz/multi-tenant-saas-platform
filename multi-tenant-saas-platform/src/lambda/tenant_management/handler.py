"""
Lambda handler for tenant management operations.
"""

import json
from typing import Dict, Any
from .tenant_service import TenantService
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()
tenant_service = TenantService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle tenant management API requests.
    
    Args:
        event: API Gateway event.
        context: Lambda context.
    
    Returns:
        Dict: API response.
    """
    try:
        http_method = event["httpMethod"]
        path = event["path"]
        user = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
        
        if http_method == "GET" and "/tenants/{tenant_id}/data/{item_id}" in path:
            tenant_id = event["pathParameters"]["tenant_id"]
            item_id = event["pathParameters"]["item_id"]
            result = tenant_service.get_tenant_data(tenant_id, item_id, user)
            if result is None:
                return {"statusCode": 404, "body": json.dumps({"error": "Item not found"})}
            return {"statusCode": 200, "body": json.dumps(result)}
        
        elif http_method == "POST" and "/tenants/{tenant_id}/data" in path:
            tenant_id = event["pathParameters"]["tenant_id"]
            body = json.loads(event["body"])
            item_id = body["item_id"]
            data = body["data"]
            tenant_service.store_tenant_data(tenant_id, item_id, data, user)
            metrics.record_data_access_success()
            return {"statusCode": 201, "body": json.dumps({"message": "Data stored"})}
        
        else:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid request"})}
    
    except Exception as e:
        logger.error("Tenant management error: %s", str(e))
        metrics.record_error()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}