"""
Metrics collection for performance monitoring with CloudWatch.
"""

import boto3
from typing import Dict
from ..utils.logger import setup_logger

class MetricsCollector:
    """Collects and sends metrics to CloudWatch."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = setup_logger(__name__)
        self.cloudwatch = boto3.client("cloudwatch")
        self.namespace = "SaaSPlatform"

    def record_data_access_success(self):
        """Record successful data access."""
        self._put_metric("DataAccessSuccess", 1)

    def record_data_access_failure(self):
        """Record failed data access."""
        self._put_metric("DataAccessFailure", 1)

    def record_billing_update(self):
        """Record billing update."""
        self._put_metric("BillingUpdates", 1)

    def record_onboarding_success(self):
        """Record successful tenant onboarding."""
        self._put_metric("OnboardingSuccess", 1)

    def record_error(self):
        """Record error occurrence."""
        self._put_metric("Errors", 1)

    def _put_metric(self, metric_name: str, value: int):
        """Send metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric.
            value: Metric value.
        """
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": "Count"
                }]
            )
            self.logger.debug("Recorded metric %s: %d", metric_name, value)
        except Exception as e:
            self.logger.error("Failed to record metric %s: %s", metric_name, str(e))