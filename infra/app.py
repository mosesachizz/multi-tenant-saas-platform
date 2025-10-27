"""
AWS CDK application for the Multi-Tenant SaaS Platform.
"""

from aws_cdk import App
from stacks.saas_stack import SaaSStack

app = App()
SaaSStack(app, "SaaSPlatformStack")
app.synth()