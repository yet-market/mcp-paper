#!/bin/bash

# Deployment script for Multi-Model Luxembourg Legal Assistant
# Builds Docker container, pushes to ECR, and deploys with Terraform
# Supports configurable AWS Bedrock models

set -e  # Exit on any error

# Configuration
PROJECT_NAME="luxembourg-legal-assistant"
AWS_REGION="eu-west-2"
AWS_PROFILE="yet"
ENVIRONMENT="prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

# Check AWS credentials
check_aws_credentials() {
    log_info "Checking AWS credentials for profile: $AWS_PROFILE"
    
    if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
        log_error "AWS credentials for profile '$AWS_PROFILE' are not configured"
        log_info "Please run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    log_success "AWS credentials verified (Account: $account_id)"
}

# Get or create ECR repository URL
get_ecr_repository() {
    log_info "Getting ECR repository URL..."
    
    # Check if we have terraform state
    if [ -f "terraform.tfstate" ]; then
        ECR_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
        if [ -n "$ECR_URL" ]; then
            log_success "ECR repository URL from Terraform: $ECR_URL"
            return
        fi
    fi
    
    # Get account ID for ECR URL construction
    local account_id=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    ECR_URL="$account_id.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-lambda"
    log_info "Constructed ECR URL: $ECR_URL"
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building Docker image..."
    
    # Build the image
    docker build -t "$PROJECT_NAME:latest" .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
    
    log_info "Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" | \
        docker login --username AWS --password-stdin "$ECR_URL"
    
    if [ $? -eq 0 ]; then
        log_success "ECR login successful"
    else
        log_error "ECR login failed"
        exit 1
    fi
    
    # Tag and push the image
    log_info "Tagging and pushing image to ECR..."
    docker tag "$PROJECT_NAME:latest" "$ECR_URL:latest"
    docker push "$ECR_URL:latest"
    
    if [ $? -eq 0 ]; then
        log_success "Image pushed to ECR successfully"
    else
        log_error "Image push failed"
        exit 1
    fi
}

# Collect deployment variables with model selection
collect_variables() {
    log_info "Collecting deployment variables..."
    
    # Check if variables file exists
    if [ -f "terraform.tfvars" ]; then
        log_warning "terraform.tfvars already exists. Overwrite? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Using existing terraform.tfvars"
            return
        fi
    fi
    
    echo "# Terraform variables for $PROJECT_NAME deployment" > terraform.tfvars
    echo "# Generated on $(date)" >> terraform.tfvars
    echo "# Multi-model support - configure MODEL_ID as needed" >> terraform.tfvars
    echo "" >> terraform.tfvars
    
    # Prompt for model selection
    log_info "Select AWS Bedrock model:"
    echo "1) Claude 3.5 Sonnet (Recommended)"
    echo "2) Claude 3 Haiku (Fast & Cheap)"
    echo "3) Mistral 7B (Budget)"
    echo "4) Llama 3 70B (Powerful)"
    echo "5) Cohere Command R+"
    echo "6) Custom model ID"
    echo -n "Choice (1-6): "
    read -r model_choice
    
    case $model_choice in
        1) MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0" ;;
        2) MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0" ;;
        3) MODEL_ID="mistral.mistral-7b-instruct-v0:2" ;;
        4) MODEL_ID="meta.llama3-70b-instruct-v1:0" ;;
        5) MODEL_ID="cohere.command-r-plus-v1:0" ;;
        6) 
            echo -n "Enter custom model ID: "
            read -r MODEL_ID
            ;;
        *) 
            log_warning "Invalid choice, using Claude 3.5 Sonnet (default)"
            MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
            ;;
    esac
    
    log_success "Selected model: $MODEL_ID"
    
    # Fixed MCP server URL - always use production server
    mcp_url="https://yet-mcp-legilux.site"
    
    # Write secure configuration to terraform.tfvars
    cat >> terraform.tfvars << EOF
project_name = "$PROJECT_NAME"
environment = "$ENVIRONMENT"
model_id = "$MODEL_ID"
mcp_server_url = "$mcp_url"
EOF

    log_success "Variables collected and saved to terraform.tfvars"
    log_info "Model: $MODEL_ID"
    log_info "MCP Server: $mcp_url"
}

# Deploy with Terraform
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    if [ $? -ne 0 ]; then
        log_error "Terraform init failed"
        exit 1
    fi
    
    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -var-file="terraform.tfvars"
    
    if [ $? -ne 0 ]; then
        log_error "Terraform plan failed"
        exit 1
    fi
    
    # Ask for confirmation
    log_warning "Proceed with deployment? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    # Apply deployment
    log_info "Applying Terraform deployment..."
    terraform apply -var-file="terraform.tfvars" -auto-approve
    
    if [ $? -eq 0 ]; then
        log_success "Infrastructure deployed successfully"
    else
        log_error "Terraform apply failed"
        exit 1
    fi
}

# Update Lambda function with new image
update_lambda() {
    log_info "Updating Lambda function with new image..."
    
    local function_name=$(terraform output -raw lambda_function_name)
    
    aws lambda update-function-code \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --function-name "$function_name" \
        --image-uri "$ECR_URL:latest" \
        > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Lambda function updated successfully"
    else
        log_error "Lambda function update failed"
        exit 1
    fi
}

# Display deployment information
show_deployment_info() {
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Deployment Information:"
    echo "========================"
    
    local api_url=$(terraform output -raw api_gateway_url)
    local api_key=$(terraform output -raw api_key_value)
    local chat_endpoint=$(terraform output -raw chat_endpoint)
    local search_endpoint=$(terraform output -raw search_endpoint)
    local health_endpoint=$(terraform output -raw health_endpoint)
    local model_id=$(grep "model_id" terraform.tfvars | cut -d'"' -f2)
    
    echo "🤖 Model: $model_id"
    echo "🌐 API Gateway URL: $api_url"
    echo "🔑 API Key: $api_key"
    echo ""
    echo "📡 Endpoints:"
    echo "  💬 Chat:   $chat_endpoint"
    echo "  🔍 Search: $search_endpoint"
    echo "  ❤️  Health: $health_endpoint"
    echo ""
    echo "📋 Usage Example:"
    echo "curl -X POST '$chat_endpoint' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -H 'X-API-Key: $api_key' \\"
    echo "  -d '{\"message\": \"Comment créer une SARL au Luxembourg?\"}'"
    echo ""
    echo "🔧 Model Configuration:"
    echo "  To change model: Edit terraform.tfvars and redeploy"
    echo "  Supported: Claude, Mistral, Llama, Cohere, Titan"
    echo ""
    
    # Save API key to file for easy access
    echo "$api_key" > api_key.txt
    log_info "API key saved to api_key.txt"
}

# Main deployment function
main() {
    log_info "🚀 Starting deployment of $PROJECT_NAME (Multi-Model)"
    log_info "Region: $AWS_REGION | Profile: $AWS_PROFILE | Environment: $ENVIRONMENT"
    echo ""
    
    check_dependencies
    check_aws_credentials
    collect_variables
    get_ecr_repository
    
    # First deployment creates ECR, subsequent ones can skip
    if [ ! -f "terraform.tfstate" ]; then
        log_info "First deployment - creating infrastructure..."
        deploy_infrastructure
        get_ecr_repository  # Get the actual ECR URL after creation
    fi
    
    build_and_push_image
    
    # Update Lambda if infrastructure already exists
    if [ -f "terraform.tfstate" ]; then
        update_lambda
    fi
    
    show_deployment_info
}

# Script execution
case "${1:-}" in
    "clean")
        log_info "Cleaning up deployment artifacts..."
        rm -f terraform.tfstate* terraform.tfplan *.zip api_key.txt
        log_success "Cleanup completed"
        ;;
    "destroy")
        log_warning "This will DESTROY all infrastructure. Are you sure? (type 'yes' to confirm)"
        read -r response
        if [ "$response" = "yes" ]; then
            terraform destroy -var-file="terraform.tfvars" -auto-approve
            log_success "Infrastructure destroyed"
        else
            log_info "Destruction cancelled"
        fi
        ;;
    "models")
        log_info "Supported AWS Bedrock Models:"
        echo ""
        echo "🧠 Anthropic Claude:"
        echo "  - anthropic.claude-3-5-sonnet-20241022-v2:0 (Recommended)"
        echo "  - anthropic.claude-3-haiku-20240307-v1:0 (Fast & Cheap)"
        echo ""
        echo "🔥 Mistral:"
        echo "  - mistral.mistral-7b-instruct-v0:2 (Budget)"
        echo "  - mistral.mixtral-8x7b-instruct-v0:1 (Powerful)"
        echo ""
        echo "🦙 Meta Llama:"
        echo "  - meta.llama3-70b-instruct-v1:0 (Powerful)"
        echo "  - meta.llama3-8b-instruct-v1:0 (Fast)"
        echo ""
        echo "🌊 Cohere:"
        echo "  - cohere.command-r-plus-v1:0 (Advanced)"
        echo "  - cohere.command-r-v1:0 (Standard)"
        echo ""
        echo "🏔️ Amazon Titan:"
        echo "  - amazon.titan-text-premier-v1:0 (Enterprise)"
        echo "  - amazon.titan-text-express-v1 (Fast)"
        echo ""
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|destroy|models]"
        echo ""
        echo "Commands:"
        echo "  (no args) - Deploy or update the application"
        echo "  clean     - Clean up deployment artifacts"
        echo "  destroy   - Destroy all infrastructure"
        echo "  models    - List supported Bedrock models"
        exit 1
        ;;
esac