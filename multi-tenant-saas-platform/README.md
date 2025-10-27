# Multi-Tenant SaaS Platform

A serverless, scalable, and secure multi-tenant SaaS backend built on AWS, enforcing strict data isolation, automated usage-based billing, and self-service onboarding.

---

## Problem Statement
Modern SaaS platforms require strict tenant isolation, automated billing, and seamless onboarding to support thousands of users with minimal operational overhead. Traditional systems often face challenges with data segregation, manual billing processes, and complex onboarding, leading to inefficiencies and security risks.

---

## Solution

This project implements a **Multi-Tenant SaaS Platform** that:

- **Enforces strict data isolation** using DynamoDB tenant partitioning and AWS IAM policies.
- **Automates usage-based billing** with real-time tracking via DynamoDB Streams and Lambda.
- **Enables self-service onboarding** through a secure API with Cognito authentication.
- **Scales serverlessly** with AWS Lambda and API Gateway to handle variable workloads.
- **Provides monitoring** with AWS CloudWatch for performance and billing metrics.
- **Ensures code quality** with CI/CD pipelines and Flake8 linting.

| Technology | Purpose |
|-------------|----------|
| **Python** | Core language for Lambda functions and scripts |
| **AWS Lambda** | Serverless compute for business logic and billing |
| **AWS API Gateway** | REST API for tenant interactions and onboarding |
| **AWS DynamoDB** | NoSQL database with tenant-based partitioning |
| **AWS Cognito** | User authentication and authorization |
| **AWS SQS/SNS** | Asynchronous messaging for billing and notifications |
| **AWS CloudWatch** | Monitoring and logging for system metrics |
| **PyTest** | Unit and integration testing |
| **GitHub Actions** | CI/CD for automated deployment |
| **Flake8** | Code linting for style and quality |
| **AWS CDK** | Infrastructure-as-Code for reproducible deployments |

---

## Architecture Decisions

- **Serverless Architecture**: Lambda and API Gateway eliminate server management and ensure scalability.
- **DynamoDB Partitioning**: Uses tenant IDs as partition keys for data isolation.
- **Cognito Authentication**: Secures APIs with JWT tokens for user management.
- **Event-Driven Billing**: DynamoDB Streams and SQS trigger billing calculations.
- **AWS CDK**: Defines infrastructure programmatically for consistency.
- **Modular Design**: Separates tenant management, billing, and onboarding logic.
- **Monitoring**: CloudWatch tracks API latency, errors, and billing metrics.

---

## Key Feature: Tenant Data Isolation

Below is a code snippet from `src/lambda/tenant_management/tenant_service.py`, showcasing type hints, error handling, and tenant isolation.

```python
def get_tenant_data(self, tenant_id: str, item_id: str, user: dict) -> Optional[dict]:
    """Retrieve tenant-specific data with strict isolation."""
    try:
        # Verify tenant access
        if user["tenant_id"] != tenant_id:
            self.logger.error("Unauthorized access to tenant %s by user %s", tenant_id, user["sub"])
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
```

#**Explanation**:
- **Tenant Isolation:** Enforces access control with tenant ID checks.  
- **Robustness:** Comprehensive error handling and logging.  
- **Monitoring:** Tracks access success/failure with CloudWatch metrics.  
- **Security:** Integrates with Cognito user context for authorization.

---

## Setup Instructions

Follow these steps to set up and deploy the Multi-Tenant SaaS Platform locally and on AWS.

### 1. Clone the Repository
```bash
git clone https://github.com/mosesachizz/multi-tenant-saas-platform.git
cd multi-tenant-saas-platform
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r infra/requirements.txt
```

### 3. Set Up AWS CLI
```bash
pip install awscli
aws configure
```

### 4. Bootstrap CDK (First-Time Setup)
```bash
./scripts/bootstrap.sh
```

### 5. Deploy Infrastructure
```bash
./scripts/deploy.sh
```

### 6. Run Tests
```bash
pytest tests/
```

### 7. Access the API
- Onboarding: Register a new tenant via POST to <API_GATEWAY_URL>/onboarding with JSON payload:
```json
{
  "tenant_name": "acme_corp",
  "email": "admin@acme.com",
  "password": "SecurePassword123!"
}
```

-  **Tenant Data:** Access tenant data via `GET` to `<API_GATEWAY_URL>/tenants/{tenant_id}/data/{item_id}` with Cognito JWT token in header: `Authorization: Bearer <token>`
-  **Billing:** View billing summary via `GET` to `<API_GATEWAY_URL>/billing/{tenant_id}`
-  **CloudWatch Dashboard:** Monitor metrics at:
`AWS Console → CloudWatch → Dashboards`

---

### 8. CI/CD Setup
The GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests, linting, and CDK deployment on push or pull requests to the main branch.

---

### Production Notes

- **Security:** Update `auth.cognito_user_pool_id` in `configs/config.yaml` with your Cognito User Pool ID.
- **Scalability:** Adjust DynamoDB capacity modes (on-demand/provisioned) based on load.
- **Monitoring:** Customize CloudWatch dashboards for tenant-specific metrics.
- **Billing:** Integrate with Stripe or AWS Marketplace for production billing.
- **Testing:** Add integration tests for real AWS resources using `moto`.

## License
This project is licensed under the **MIT License** - see the [MIT License](LICENSE) file for details.


