# Financial Forecast AI Application

A production-ready AI application for analyzing prospectus reports and relay files to forecast prepayment speeds and rates.

## Features

- RAG-based document analysis
- Agentic workflows for intelligent processing
- AWS Bedrock Claude Sonnet model integration
- Vector search with PostgreSQL and pgvector
- Modern chat interface with Streamlit
- CloudFormation deployment to AWS

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- PostgreSQL database with pgvector extension
- AWS credentials configured

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
POSTGRES_CONNECTION=postgresql://user:password@localhost:5432/financial_forecast
```

## Usage

1. Start the application:
```bash
# From project root directory
streamlit run src/ui/app.py
```

2. Open your browser and go to http://localhost:8501
3. Upload prospectus reports and relay files through the web interface
4. Ask questions about prepayment speeds and rates
5. View detailed analysis and forecasts

**Note**: The application currently runs in development mode with local storage. For production use with AWS Bedrock and PostgreSQL, ensure your `.env` file contains valid AWS credentials.

## AWS Bedrock Setup

### Step 1: Configure IAM Permissions

AWS Bedrock requires specific IAM permissions. You need to set up proper access policies:

#### Option A: Using IAM User (Recommended for Development)
1. **Go to AWS IAM Console** → Users → Select your user
2. **Attach Policy** → Create or attach these policies:

**Policy Name**: `BedrockFullAccess`
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Option B: Using AWS Managed Policy (Easier)
1. **Attach the managed policy**: `AmazonBedrockFullAccess`
2. This gives full access to Bedrock services

### Step 2: Request Model Access
1. **Go to AWS Console** → Bedrock → Model access
2. **Select region**: us-east-1
3. **Request access** to "Anthropic Claude 3.5 Sonnet"
4. **Fill out use case form**:
   ```
   Use Case: Financial analysis application for mortgage prepayment forecasting.
   Industry: Financial Services
   Application: Commercial analytical platform for investment decision support.
   ```
5. **Wait for approval** (usually 15 minutes to 2 hours)

### Step 3: Verify Setup
- Check that Model access shows "Available" for Claude 3.5 Sonnet
- Ensure your IAM user/role has Bedrock permissions
- Verify AWS credentials in `.env` file

### Requirements:
1. **IAM permissions** for Bedrock access
2. **Model access approval** for Claude 3.5 Sonnet
3. **Valid AWS credentials** in your `.env` file
4. **Correct AWS region** (us-east-1 recommended)

### Troubleshooting:
- **ResourceNotFoundException**: Request model access in Bedrock console
- **AccessDenied**: Check IAM permissions for your user/role
- **Invalid credentials**: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

## AWS Deployment

### Option 1: Complete Deployment (Recommended)

1. **Deploy IAM permissions first**:
```bash
aws cloudformation create-stack \
    --stack-name financial-forecast-iam \
    --template-body file://infra/iam-permissions.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters ParameterKey=Environment,ParameterValue=dev \
                 ParameterKey=CreateDeveloperUser,ParameterValue=true
```

2. **Deploy VPC and Database**:
```bash
aws cloudformation create-stack \
    --stack-name financial-forecast-vpc \
    --template-body file://infra/vpc-db.yaml \
    --parameters ParameterKey=Environment,ParameterValue=dev
```

3. **Deploy Application**:
```bash
aws cloudformation create-stack \
    --stack-name financial-forecast-app \
    --template-body file://infra/app.yaml \
    --capabilities CAPABILITY_IAM \
    --parameters ParameterKey=Environment,ParameterValue=dev \
                 ParameterKey=VPCStackName,ParameterValue=financial-forecast-vpc
```

4. **Get developer credentials** (if created):
```bash
aws secretsmanager get-secret-value \
    --secret-id dev/financial-forecast/developer/credentials \
    --query SecretString --output text
```

### Option 2: Local Development Only

If you just want to set up permissions for local development:

```bash
aws cloudformation create-stack \
    --stack-name financial-forecast-iam-dev \
    --template-body file://infra/iam-permissions.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters ParameterKey=Environment,ParameterValue=dev
```

Then add your existing user to the created IAM group:
```bash
aws iam add-user-to-group \
    --group-name dev-FinancialForecastDevelopers \
    --user-name YOUR_USERNAME
```

## Project Structure

```
.
├── src/
│   ├── agents/          # Agent implementations
│   ├── core/            # Core business logic
│   └── ui/             # Streamlit interface
├── infra/              # CloudFormation templates
├── .env               # Environment configuration
└── README.md         # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT