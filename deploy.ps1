param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1",
    [string]$UserName = "Antonio"
)

# Get account ID
$AccountId = (aws sts get-caller-identity --query Account --output text)

Write-Host "🚀 Deploying Financial Forecast AI Infrastructure..."
Write-Host "   Environment: $Environment"
Write-Host "   Region: $Region"
Write-Host "   User: $UserName"
Write-Host "   Account: $AccountId"
Write-Host ""

# Create ECR repository if it doesn't exist
Write-Host "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names financial-forecast-ai 2>&1 > $null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name financial-forecast-ai
    Write-Host "✅ ECR repository created"
} else {
    Write-Host "✅ ECR repository already exists"
}

# Build and push Docker image
Write-Host "🐳 Building and pushing Docker image..."
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
docker build -t financial-forecast-ai .
docker tag financial-forecast-ai "$AccountId.dkr.ecr.$Region.amazonaws.com/financial-forecast-ai:latest"
docker push "$AccountId.dkr.ecr.$Region.amazonaws.com/financial-forecast-ai:latest"
Write-Host "✅ Docker image pushed successfully"

# Deploy complete infrastructure stack
Write-Host "🏗️ Deploying complete infrastructure stack..."
$StackName = "financial-forecast-complete"
aws cloudformation create-stack `
    --stack-name $StackName `
    --template-body file://infra/cloudformation.yaml `
    --parameters ParameterKey=Environment,ParameterValue=$Environment `
                ParameterKey=UserName,ParameterValue=$UserName `
    --capabilities CAPABILITY_IAM

Write-Host "⏳ Waiting for infrastructure stack to complete..."
aws cloudformation wait stack-create-complete --stack-name $StackName

Write-Host "🎉 Deployment complete!"
Write-Host ""

# Get outputs
Write-Host "📊 Infrastructure Outputs:"
Write-Host "=========================="
Write-Host "Database Endpoint:"
aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' --output text

Write-Host "`nVPC ID:"
aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' --output text

Write-Host "`nBedrock Policy:"
aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs[?OutputKey==`BedrockPolicyName`].OutputValue' --output text

Write-Host "`n🚀 Next Steps:"
Write-Host "1. Configure your .env file with the database endpoint"
Write-Host "2. Run: streamlit run src/ui/app.py --server.port 8516"
Write-Host "3. Open: http://localhost:8516"