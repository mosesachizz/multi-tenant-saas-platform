#!/bin/bash
# Deploy the CDK stack
cd infra
pip install -r requirements.txt
cdk deploy --require-approval never