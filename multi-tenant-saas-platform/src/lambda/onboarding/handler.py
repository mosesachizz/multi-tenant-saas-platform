"""
Lambda handler for tenant onboarding operations.
"""

import json
from typing import Dict, Any
from .onboarding_service import OnboardingService
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()
onboarding_service = OnboardingService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle tenant onboarding API requests.
    
    Args:
        event: API Gateway event.
        context: Lambda context.
    
    Returns:
        Dict: API response.
    """
    try:
        http_method = event["httpMethod"]
        if http_method == "POST" and event["path"] == "/onboarding":
            body = json.loads(event["body"])
            tenant_id = onboarding_service.register_tenant(
                tenant_name=body["tenant_name"],
                email=body["email"],
                password=body["password"]
            )
            metrics.record_onboarding_success()
            return {"statusCode": 201, "body": json.dumps({"tenant_id": tenant_id})}
        
        else:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid request"})}
    
    except Exception as e:
        logger.error("Onboarding error: %s", str(e))
        metrics.record_error()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}