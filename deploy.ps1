param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1"
)

# Get account ID
$AccountId = (aws sts get-caller-identity --query Account --output text)

# Create ECR repository if it doesn't exist
Write-Host "Creating ECR repository..."
aws ecr describe-repositories --repository-names financial-forecast-ai 2>&1 > $null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name financial-forecast-ai
}

# Build and push Docker image
Write-Host "Building and pushing Docker image..."
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
docker build -t financial-forecast-ai .
docker tag financial-forecast-ai "$AccountId.dkr.ecr.$Region.amazonaws.com/financial-forecast-ai:latest"
docker push "$AccountId.dkr.ecr.$Region.amazonaws.com/financial-forecast-ai:latest"

# Deploy VPC and Database stack
Write-Host "Deploying VPC and Database stack..."
$VpcStackName = "financial-forecast-vpc-$Environment"
aws cloudformation create-stack `
    --stack-name $VpcStackName `
    --template-body file://infra/vpc-db.yaml `
    --parameters ParameterKey=Environment,ParameterValue=$Environment `
    --capabilities CAPABILITY_IAM

Write-Host "Waiting for VPC and Database stack to complete..."
aws cloudformation wait stack-create-complete --stack-name $VpcStackName

# Deploy Application stack
Write-Host "Deploying Application stack..."
$AppStackName = "financial-forecast-app-$Environment"
aws cloudformation create-stack `
    --stack-name $AppStackName `
    --template-body file://infra/app.yaml `
    --parameters ParameterKey=Environment,ParameterValue=$Environment `
                ParameterKey=VPCStackName,ParameterValue=$VpcStackName `
    --capabilities CAPABILITY_IAM

Write-Host "Waiting for Application stack to complete..."
aws cloudformation wait stack-create-complete --stack-name $AppStackName

Write-Host "Deployment complete!"

# Get outputs
Write-Host "`nDatabase Endpoint:"
aws cloudformation describe-stacks --stack-name $VpcStackName --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' --output text

Write-Host "`nECS Cluster Name:"
aws cloudformation describe-stacks --stack-name $AppStackName --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' --output text