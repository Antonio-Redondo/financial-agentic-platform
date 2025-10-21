# Financial Forecast AI - Infrastructure Deployment Guide

This directory contains the complete CloudFormation infrastructure for the Financial Forecast AI application.

## 📁 Infrastructure Files

### 🎯 **Single Consolidated Template**

#### **`cloudformation.yaml`** - Complete Infrastructure
- **Resources**: 
  - ✅ VPC with public/private subnets across 2 AZs
  - ✅ PostgreSQL RDS database (db.t3.medium)  
  - ✅ Security groups for ALB and database
  - ✅ Secrets Manager for database credentials
  - ✅ Internet Gateway and Route Tables
  - ✅ IAM policy for full Bedrock access
  - ✅ CloudWatch Logs permissions
- **Parameters**: 
  - Environment (dev/prod)
  - UserName (default: Antonio)
- **Capabilities**: Requires CAPABILITY_IAM

## 🚀 **Deploy Infrastructure**

### Deploy Complete Infrastructure
```powershell
# Create new consolidated stack
aws cloudformation create-stack `
  --stack-name financial-forecast-complete `
  --template-body file://infra/cloudformation.yaml `
  --capabilities CAPABILITY_IAM `
  --parameters ParameterKey=Environment,ParameterValue=dev ParameterKey=UserName,ParameterValue=Antonio

# Update existing consolidated stack
aws cloudformation update-stack `
  --stack-name financial-forecast-complete `
  --template-body file://infra/cloudformation.yaml `
  --capabilities CAPABILITY_IAM `
  --parameters ParameterKey=Environment,ParameterValue=dev ParameterKey=UserName,ParameterValue=Antonio
```

## 📊 **Architecture Overview**

```
🖥️ Local Machine (Windows)
├── PowerShell Terminal
├── Python Virtual Environment (.venv)
├── Streamlit Server (localhost:8516+)
└── Financial Forecast AI App
    ├── 🧠 Amazon Titan Text (AWS Bedrock)
    │   └── 🔐 IAM Policy: BedrockFullAccess
    └── 🗄️ PostgreSQL Database
        └── 📍 RDS: financial_forecast
```

### 🔍 **Validation & Monitoring Commands**

```powershell
# Validate template
aws cloudformation validate-template --template-body file://infra/cloudformation.yaml

# Check stack status
aws cloudformation describe-stacks --stack-name financial-forecast-complete --query "Stacks[0].StackStatus"

# Monitor deployment progress
aws cloudformation describe-stack-events --stack-name financial-forecast-complete

# Get stack outputs
aws cloudformation describe-stacks --stack-name financial-forecast-complete --query "Stacks[0].Outputs"
```

## 🏗️ **What Gets Deployed**

- **Network**: Complete VPC with public/private subnets across 2 AZs
- **Database**: PostgreSQL 13.15 database with automated backups and encryption
- **Security**: Proper security groups and IAM policies
- **Secrets**: Managed database credentials via AWS Secrets Manager  
- **AI Access**: Full Bedrock permissions for Amazon Titan Text models
- **Monitoring**: CloudWatch logs integration

## ✨ **Benefits of Consolidated Template**

- **Simplified Management**: Single stack to deploy and maintain
- **Atomic Operations**: All resources created/updated together
- **Consistent Naming**: Unified resource naming scheme
- **Dependency Management**: Proper resource dependencies handled automatically
- **Easier Cleanup**: Single stack deletion removes all resources

## 🔧 **Migration from Legacy Stacks**

If you have existing separate stacks (`financial-forecast-vpc-dev` and `antonio-bedrock-permissions`), you can either:

1. **Keep existing stacks** - They will continue to work
2. **Migrate to consolidated stack** - Delete old stacks and deploy the new one

```powershell
# Option 2: Clean migration (optional)
aws cloudformation delete-stack --stack-name antonio-bedrock-permissions
aws cloudformation delete-stack --stack-name financial-forecast-vpc-dev

# Wait for deletion, then deploy new stack
aws cloudformation create-stack `
  --stack-name financial-forecast-complete `
  --template-body file://infra/cloudformation.yaml `
  --capabilities CAPABILITY_IAM `
  --parameters ParameterKey=Environment,ParameterValue=dev ParameterKey=UserName,ParameterValue=Antonio
```

---

*This infrastructure supports both local development and production cloud deployment of the Financial Forecast AI application.*