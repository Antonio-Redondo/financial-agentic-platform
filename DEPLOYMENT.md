# 🚀 Financial Forecast AI - Deployment Guide

This guide walks you through deploying the Financial Forecast AI application locally with AWS Bedrock integration. The application uses Streamlit frontend running locally with AWS Bedrock (Amazon Titan models) for AI processing.

## 📋 Prerequisites Checklist

### 🖥️ Local System Requirements
- [ ] **Windows 10/11** with PowerShell 5.1+
- [ ] **Python 3.11+** installed and accessible via command line
- [ ] **Git** for version control and repository cloning
- [ ] **Internet connection** for downloading dependencies and AWS API access
- [ ] **Text editor** (VS Code recommended) for configuration files

### ☁️ AWS Account Requirements
- [ ] **Active AWS Account** with billing enabled
- [ ] **AWS CLI** installed and configured
- [ ] **IAM permissions** for Bedrock access
- [ ] **Bedrock model access** approved for us-east-1 region

---

## 🚀 Local Deployment with AWS Bedrock

### Step 1: System Preparation

#### 1.1 Verify Python Installation
```powershell
# Check Python version (should be 3.11 or higher)
python --version

# If Python is not installed, download from:
# https://www.python.org/downloads/windows/
```

#### 1.2 Install Git (if not already installed)
```powershell
# Check if Git is installed
git --version

# If not installed, download from:
# https://git-scm.com/download/win
```

#### 1.3 Install AWS CLI
```powershell
# Download and install AWS CLI v2 from:
# https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version
```

### Step 2: Clone and Setup Project

#### 2.1 Clone Repository
```powershell
# Navigate to your desired directory
cd C:\Users\$env:USERNAME\Desktop

# Clone the repository
git clone https://github.com/Antonio-Redondo/financial-forecast-ai.git
cd financial-forecast-ai

# Or if already cloned, navigate to it
cd c:\Users\anton\OneDrive\Desktop\AI\finalcial_forecast_ia_app
```

#### 2.2 Create Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify activation (should show (.venv) in prompt)
# (.venv) PS C:\path\to\project>
```

#### 2.3 Install Dependencies
```powershell
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify key packages are installed
pip list | Select-String "streamlit|boto3|langchain"
```

### Step 3: AWS Configuration

#### 3.1 Configure AWS Credentials
```powershell
# Configure AWS CLI with your credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

#### 3.2 Verify AWS Access
```powershell
# Test AWS connectivity
aws sts get-caller-identity

# Expected output should show your UserId, Account, and Arn
```

**✅ Verify Access:**
```powershell
# Check available models
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId, 'titan')]"
```

### Step 4: Environment Configuration

#### 4.1 Create Environment File
```powershell
# Create .env file in project root
New-Item -Path ".env" -ItemType File -Force
```

#### 4.2 Configure Environment Variables
Add the following content to `.env` file:

```env
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Application Settings
USE_LOCAL_STORAGE=false
DEBUG_MODE=false

# Optional: Custom port (default is 8501)
STREAMLIT_SERVER_PORT=8520
```

### Step 5: Launch Application

#### 5.1 Start the Application
```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Start Streamlit application
streamlit run src\ui\app.py --server.port 8520

# Alternative with environment variable
$env:STREAMLIT_SERVER_PORT=8520; streamlit run src\ui\app.py
```

#### 5.2 Access Application
- **Local URL**: http://localhost:8520
- **Network URL**: http://[your-ip]:8520 (for other devices on same network)

### Step 6: Verification and Testing

#### 6.1 Application Health Check
```powershell
# Check if application is running
Invoke-WebRequest -Uri "http://localhost:8520" -Method GET
```

#### 6.2 Test AI Functionality
1. **Upload a test document** (PDF, Word, Excel)
2. **Ask a simple question**: "What is this document about?"
3. **Verify AI response** using Amazon Titan models
4. **Check console logs** for any errors

---

## 🏗️ Hybrid Deployment: Local Streamlit + AWS Infrastructure

This approach combines the best of both worlds: **local Streamlit development** with **AWS managed infrastructure** for production-grade data storage and security.

### Architecture Overview
```
Local Machine                    AWS Services
┌─────────────────┐             ┌─────────────────────┐
│ 🖥️ Streamlit App │ ────────── │ 🧠 Bedrock API      │
│ 🐍 Python Code  │             │ 🤖 Titan Models     │
│ 💻 Dev Tools    │             │ 🗄️ RDS PostgreSQL   │
│ 🔧 Hot Reload   │             │ 🔒 VPC Security     │
└─────────────────┘             │ 🔑 IAM Permissions  │
                                └─────────────────────┘
```

### Step 1: Deploy AWS Infrastructure

First, deploy the AWS infrastructure that will support your local application:

```powershell
# Navigate to project directory
cd c:\Users\anton\OneDrive\Desktop\AI\finalcial_forecast_ia_app

# Deploy AWS infrastructure stack
aws cloudformation create-stack `
  --stack-name financial-forecast-infrastructure `
  --template-body file://infra/cloudformation.yaml `
  --capabilities CAPABILITY_IAM `
  --parameters ParameterKey=Environment,ParameterValue=hybrid `
               ParameterKey=UserName,ParameterValue=Antonio `
  --region us-east-1

# Monitor deployment progress
aws cloudformation describe-stacks `
  --stack-name financial-forecast-infrastructure `
  --query "Stacks[0].StackStatus"
```

### Step 2: Wait for Infrastructure Deployment

```powershell
# Wait for stack creation (takes 10-15 minutes)
aws cloudformation wait stack-create-complete `
  --stack-name financial-forecast-infrastructure `
  --region us-east-1

Write-Host "AWS Infrastructure ready for hybrid deployment!" -ForegroundColor Green
```

### Step 3: Retrieve Infrastructure Configuration

```powershell
# Get database connection details and other outputs
aws cloudformation describe-stacks `
  --stack-name financial-forecast-infrastructure `
  --region us-east-1 `
  --query "Stacks[0].Outputs" `
  --output table

# Save these values for environment configuration
```

### Step 4: Configure Hybrid Environment

Create a hybrid `.env` file that connects your local app to AWS services:

```powershell
# Create hybrid environment configuration
@"
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Hybrid Configuration - Local App + AWS Infrastructure
USE_LOCAL_STORAGE=false
DEPLOYMENT_MODE=hybrid

# Database Configuration (from CloudFormation outputs)
POSTGRES_CONNECTION=postgresql://username:password@your-rds-endpoint.region.rds.amazonaws.com:5432/financial_forecast_db

# Local Development Settings
DEBUG_MODE=true
STREAMLIT_SERVER_PORT=8520
ENABLE_HOT_RELOAD=true

# Performance Settings for Hybrid Mode
DATABASE_POOL_SIZE=5
CACHE_TTL=300
"@ | Out-File -FilePath ".env" -Encoding UTF8
```

### Step 5: Install Hybrid Dependencies

```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Install additional packages for AWS database connectivity
pip install psycopg2-binary sqlalchemy

# Verify PostgreSQL connection tools
pip list | Select-String "psycopg2|sqlalchemy"
```

### Step 6: Test Database Connectivity

Before starting the application, verify the connection to AWS infrastructure:

```powershell
# Test database connection
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn_string = os.getenv('POSTGRES_CONNECTION')
try:
    conn = psycopg2.connect(conn_string)
    print('✅ Database connection successful!')
    print(f'Connected to: {conn.get_dsn_parameters()[\"host\"]}')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Step 7: Launch Hybrid Application

Start the Streamlit application with AWS backend:

```powershell
# Start hybrid application
streamlit run src\ui\app.py `
  --server.port 8520 `
  --server.runOnSave true `
  --browser.serverAddress localhost

# The application will now use:
# - Local Streamlit server (http://localhost:8520)
# - AWS RDS PostgreSQL for data storage
# - AWS Bedrock for AI processing
# - Local file uploads with cloud persistence
```

### Step 8: Verify Hybrid Deployment

Test all components of the hybrid setup:

```powershell
# 1. Check application health
Invoke-WebRequest -Uri "http://localhost:8520" -Method GET

# 2. Test AWS Bedrock connectivity
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId, 'titan')]"

# 3. Verify database tables creation (first run)
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn_string = os.getenv('POSTGRES_CONNECTION')
conn = psycopg2.connect(conn_string)
cur = conn.cursor()
cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = ''public'';')
tables = cur.fetchall()
print(f'Database tables: {[table[0] for table in tables]}')
conn.close()
"
```

### Benefits of Hybrid Deployment

#### ✅ **Development Advantages:**
- **Fast iteration** with local Streamlit hot reload
- **Direct debugging** access to Python code
- **Immediate feedback** on UI changes
- **Local development tools** integration

#### ✅ **Production Infrastructure:**
- **Managed database** with automatic backups
- **VPC security** for data protection
- **Scalable storage** with RDS PostgreSQL
- **Enterprise compliance** ready

#### ✅ **Cost Optimization:**
- **No container orchestration** costs (ECS/EKS)
- **No load balancer** charges
- **Pay only for database and Bedrock usage**
- **Scale infrastructure independently**

### Hybrid Configuration Options

#### Development Mode (Default)
```env
DEBUG_MODE=true
USE_LOCAL_STORAGE=false
DATABASE_POOL_SIZE=2
CACHE_TTL=60
```

#### Production-like Testing
```env
DEBUG_MODE=false
USE_LOCAL_STORAGE=false
DATABASE_POOL_SIZE=10
CACHE_TTL=300
ENABLE_METRICS=true
```

### Monitoring Hybrid Deployment

```powershell
# Monitor local application performance
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Select-Object ProcessName, CPU, WorkingSet

# Monitor AWS RDS performance
aws rds describe-db-instances `
  --db-instance-identifier $(aws cloudformation describe-stacks --stack-name financial-forecast-infrastructure --query "Stacks[0].Outputs[?OutputKey=='DatabaseInstanceId'].OutputValue" --output text) `
  --query "DBInstances[0].DBInstanceStatus"

# Check Bedrock usage
aws bedrock list-foundation-models --region us-east-1
```

### Troubleshooting Hybrid Setup

#### ❌ "Database connection timeout"
```powershell
# Solution: Check VPC security groups allow your IP
# Get your public IP
$ip = (Invoke-WebRequest -Uri "https://api.ipify.org").Content
Write-Host "Your IP: $ip"

# Update security group to allow your IP (replace sg-xxxxx with actual ID)
aws ec2 authorize-security-group-ingress `
  --group-id sg-xxxxx `
  --protocol tcp `
  --port 5432 `
  --cidr "$ip/32"
```

#### ❌ "SSL connection required"
```powershell
# Solution: Update connection string with SSL
# Add to .env file:
POSTGRES_CONNECTION=postgresql://username:password@endpoint:5432/dbname?sslmode=require
```

#### ❌ "Local app can't reach AWS"
```powershell
# Solution: Verify AWS credentials and region
aws sts get-caller-identity
aws configure get region
```

---

## 🏗️ Optional: AWS Infrastructure Deployment

If you want to deploy the full AWS infrastructure (VPC, Database, IAM) for production use without the hybrid approach, you can use the included CloudFormation templates:

### Deploy Complete Infrastructure Stack
```powershell
# Navigate to project directory
cd c:\Users\anton\OneDrive\Desktop\AI\finalcial_forecast_ia_app

# Deploy unified CloudFormation stack
aws cloudformation create-stack `
  --stack-name financial-forecast-complete `
  --template-body file://infra/cloudformation.yaml `
  --capabilities CAPABILITY_IAM `
  --parameters ParameterKey=Environment,ParameterValue=dev `
               ParameterKey=UserName,ParameterValue=Antonio `
  --region us-east-1

# Monitor deployment status
aws cloudformation describe-stacks `
  --stack-name financial-forecast-complete `
  --region us-east-1 `
  --query "Stacks[0].StackStatus"
```

### Wait for Infrastructure Completion
```powershell
# Wait for stack creation (takes 10-15 minutes)
aws cloudformation wait stack-create-complete `
  --stack-name financial-forecast-complete `
  --region us-east-1

Write-Host "Infrastructure deployment completed!" -ForegroundColor Green
```

### Get Infrastructure Outputs
```powershell
# Get database connection and other outputs
aws cloudformation describe-stacks `
  --stack-name financial-forecast-complete `
  --region us-east-1 `
  --query "Stacks[0].Outputs" `
  --output table
```

### Update Environment for AWS Database
If you deployed the infrastructure, update your `.env` file:
```env
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Database Configuration (from CloudFormation outputs)
USE_LOCAL_STORAGE=false
POSTGRES_CONNECTION=postgresql://username:password@endpoint:5432/financial_forecast_db

# Application Settings
DEBUG_MODE=false
STREAMLIT_SERVER_PORT=8520
```

---

## 🔧 Advanced Configuration

### Custom Port Configuration
```powershell
# Use custom port if 8520 is busy
streamlit run src\ui\app.py --server.port 8521

# Check what's using a port
netstat -ano | findstr :8520
```

### Background Service Setup
```powershell
# Run as background service (keeps running when terminal closes)
Start-Process powershell -ArgumentList "-Command", "cd 'c:\path\to\project'; .\.venv\Scripts\Activate.ps1; streamlit run src\ui\app.py --server.port 8520" -WindowStyle Hidden
```

### Firewall Configuration (for network access)
```powershell
# Allow inbound connections on port 8520
New-NetFirewallRule -DisplayName "Financial Forecast AI" -Direction Inbound -Port 8520 -Protocol TCP -Action Allow
```

---

## 🔍 Troubleshooting Guide

### Common Issues and Solutions

#### ❌ "Python not found"
```powershell
# Solution: Add Python to PATH or reinstall
# Download from: https://www.python.org/downloads/
# Ensure "Add Python to PATH" is checked during installation
```

#### ❌ "Virtual environment activation failed"
```powershell
# Solution: Change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
.\.venv\Scripts\Activate.ps1
```

#### ❌ "AWS credentials not configured"
```powershell
# Solution: Reconfigure AWS CLI
aws configure

# Or set environment variables directly
$env:AWS_ACCESS_KEY_ID="your_key"
$env:AWS_SECRET_ACCESS_KEY="your_secret"
$env:AWS_DEFAULT_REGION="us-east-1"
```

#### ❌ "Bedrock access denied"
```powershell
# Solution: Check model access in AWS Console
# Go to Bedrock → Model access → Request access for Titan models
aws bedrock list-foundation-models --region us-east-1
```

#### ❌ "Port 8520 already in use"
```powershell
# Solution: Find and kill process using the port
$process = Get-NetTCPConnection -LocalPort 8520 -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $process.OwningProcess -Force
}

# Or use different port
streamlit run src\ui\app.py --server.port 8521
```

#### ❌ "Module not found" errors
```powershell
# Solution: Reinstall dependencies
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### ❌ "CloudFormation deployment failed"
```powershell
# Solution: Check stack events for details
aws cloudformation describe-stack-events `
  --stack-name financial-forecast-complete `
  --region us-east-1 `
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED']"

# Delete failed stack and retry
aws cloudformation delete-stack `
  --stack-name financial-forecast-complete `
  --region us-east-1
```

---

## 📊 Monitoring and Maintenance

### Application Health Monitoring
```powershell
# Check application status
Invoke-WebRequest -Uri "http://localhost:8520/_stcore/health" -Method GET

# Monitor system resources
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Select-Object ProcessName, CPU, WorkingSet
```

### Log Management
```powershell
# View real-time logs
Get-Content -Path "streamlit.log" -Wait -Tail 10

# Create log rotation script
$logPath = "C:\path\to\logs\streamlit.log"
if ((Get-Item $logPath).Length -gt 10MB) {
    Move-Item $logPath ($logPath + ".old")
}
```

### Backup Procedures
```powershell
# Backup local storage (if using local files)
$backupPath = "C:\Backups\FinancialForecast\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $backupPath -Force
Copy-Item -Path "data\*" -Destination $backupPath -Recurse
```

---

## 🧹 Cleanup and Uninstallation

### Remove Local Installation
```powershell
# Deactivate virtual environment
deactivate

# Remove virtual environment
Remove-Item -Path ".venv" -Recurse -Force

# Remove project directory (optional)
cd ..
Remove-Item -Path "financial-forecast-ai" -Recurse -Force
```

### Remove AWS Infrastructure (if deployed)
```powershell
# Delete CloudFormation stack (works for both hybrid and full deployments)
aws cloudformation delete-stack `
  --stack-name financial-forecast-infrastructure `
  --region us-east-1

# Or delete the complete stack if using the full deployment option
aws cloudformation delete-stack `
  --stack-name financial-forecast-complete `
  --region us-east-1

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete `
  --stack-name financial-forecast-infrastructure `
  --region us-east-1

Write-Host "AWS infrastructure removed!" -ForegroundColor Green
```

---

## ✅ Deployment Completion Checklist

### Local Development Deployment
- [ ] Python 3.11+ installed and verified
- [ ] Virtual environment created and activated
- [ ] Dependencies installed successfully
- [ ] AWS CLI configured with valid credentials
- [ ] Bedrock model access approved
- [ ] Environment variables configured
- [ ] Application starts without errors
- [ ] Can access UI at http://localhost:8520
- [ ] Can upload documents and get AI responses
- [ ] Console shows no critical errors

---

## 🎯 What's Next?

### After Successful Deployment

1. **📚 Learn the Interface**
   - Upload sample financial documents
   - Try different types of analysis queries
   - Explore the chat interface features

2. **🔧 Customize for Your Needs**
   - Add your organization's document templates
   - Configure custom analysis prompts
   - Set up user-specific workflows

3. **📈 Scale Your Usage**
   - Process larger document sets
   - Integrate with existing systems
   - Train team members on the platform

4. **🛡️ Enhance Security**
   - Implement additional access controls
   - Set up audit logging
   - Configure backup and disaster recovery

---

## 📞 Support and Resources

### Getting Help
- **📧 Issues**: Create GitHub issues for bugs or feature requests
- **📖 Documentation**: Check README.md for usage instructions
- **🔍 AWS Support**: Use AWS support for Bedrock-related issues
- **💬 Community**: Join financial AI communities for best practices

### Useful Links
- **AWS Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **Streamlit Documentation**: https://docs.streamlit.io/
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **AWS CLI Configuration**: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure.html

---

**🎉 Congratulations! Your Financial Forecast AI application is now deployed and ready to use!**

Access your application at: **http://localhost:8520**
