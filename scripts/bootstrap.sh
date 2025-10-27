#!/bin/bash
# Bootstrap the CDK environment
cd infra
pip install -r requirements.txt
cdk bootstrap