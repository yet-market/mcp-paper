#!/bin/bash

# 2-Function Serverless Deployment Script for Luxembourg Legal Assistant
# Creates separate API handler and Job processor Lambda functions
# Proper serverless architecture with async job processing

set -e  # Exit on any error

# Configuration
PROJECT_NAME="luxembourg-legal-assistant"
AWS_REGION="eu-west-2"
AWS_PROFILE="yet"
ENVIRONMENT="prod"
# Default MCP server URL (can be overridden by .env file)
DEFAULT_MCP_SERVER_URL="https://yet-mcp-legilux.site/mcp/"

# Function names
API_FUNCTION_NAME="$PROJECT_NAME-api"
PROCESSOR_FUNCTION_NAME="$PROJECT_NAME-processor"

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

# Get AWS account ID
get_account_id() {
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
    log_info "AWS Account ID: $ACCOUNT_ID"
}

# Load API keys from .env file
load_api_keys() {
    log_info "Loading API keys from .env file..."
    
    if [ -f "../.env" ]; then
        log_info "Reading API keys from ../.env file..."
        source ../.env
    elif [ -f ".env" ]; then
        log_info "Reading API keys from .env file..."
        source .env
    else
        log_error "No .env file found. Please create one with GROQ_API_KEY and ANTHROPIC_API_KEY"
        exit 1
    fi
    
    # Check for required API keys
    if [ -z "$GROQ_API_KEY" ]; then
        log_error "GROQ_API_KEY not found in .env file"
        exit 1
    else
        log_success "✅ GROQ_API_KEY found"
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log_error "ANTHROPIC_API_KEY not found in .env file"
        exit 1
    else
        log_success "✅ ANTHROPIC_API_KEY found"
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY not found in .env - GPT-4.1-nano provider will not work"
    else
        log_success "✅ OPENAI_API_KEY found"
    fi
    
    # Set MCP server URL with fallback to default
    if [ -z "$MCP_SERVER_URL" ]; then
        MCP_SERVER_URL="$DEFAULT_MCP_SERVER_URL"
        log_info "Using default MCP server URL: $MCP_SERVER_URL"
    else
        log_info "Using MCP server URL from .env: $MCP_SERVER_URL"
    fi
}

# Create ECR repositories for both functions
create_ecr_repositories() {
    log_info "Creating ECR repositories..."
    
    # API function repository
    API_ECR_REPO_NAME="$PROJECT_NAME-api-lambda"
    API_ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$API_ECR_REPO_NAME"
    
    if aws ecr describe-repositories --repository-names "$API_ECR_REPO_NAME" --region "$AWS_REGION" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_success "API ECR repository already exists: $API_ECR_URI"
    else
        aws ecr create-repository \
            --repository-name "$API_ECR_REPO_NAME" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" \
            --image-scanning-configuration scanOnPush=true >/dev/null
        log_success "API ECR repository created: $API_ECR_URI"
    fi
    
    # Processor function repository
    PROCESSOR_ECR_REPO_NAME="$PROJECT_NAME-processor-lambda"
    PROCESSOR_ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROCESSOR_ECR_REPO_NAME"
    
    if aws ecr describe-repositories --repository-names "$PROCESSOR_ECR_REPO_NAME" --region "$AWS_REGION" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_success "Processor ECR repository already exists: $PROCESSOR_ECR_URI"
    else
        aws ecr create-repository \
            --repository-name "$PROCESSOR_ECR_REPO_NAME" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" \
            --image-scanning-configuration scanOnPush=true >/dev/null
        log_success "Processor ECR repository created: $PROCESSOR_ECR_URI"
    fi
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" | \
        docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build and push API function
    log_info "Building API function image..."
    cd api_function
    # Copy shared modules for Docker build
    cp -r ../shared ./
    docker build --platform linux/amd64 -t "$API_FUNCTION_NAME:latest" .
    docker tag "$API_FUNCTION_NAME:latest" "$API_ECR_URI:latest"
    docker push "$API_ECR_URI:latest"
    # Clean up
    rm -rf ./shared
    cd ..
    log_success "API function image pushed: $API_ECR_URI:latest"
    
    # Build and push Processor function
    log_info "Building Processor function image..."
    cd processor_function
    # Copy shared modules for Docker build
    cp -r ../shared ./
    docker build --platform linux/amd64 -t "$PROCESSOR_FUNCTION_NAME:latest" .
    docker tag "$PROCESSOR_FUNCTION_NAME:latest" "$PROCESSOR_ECR_URI:latest"
    docker push "$PROCESSOR_ECR_URI:latest"
    # Clean up
    rm -rf ./shared
    cd ..
    log_success "Processor function image pushed: $PROCESSOR_ECR_URI:latest"
}

# Create IAM role for Lambda functions
create_lambda_role() {
    log_info "Creating Lambda IAM role..."
    
    ROLE_NAME="$PROJECT_NAME-lambda-role"
    
    # Trust policy for Lambda
    cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # Create role if it doesn't exist
    if aws iam get-role --role-name "$ROLE_NAME" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_success "IAM role already exists: $ROLE_NAME"
    else
        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file://trust-policy.json \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "IAM role created: $ROLE_NAME"
    fi
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
        --profile "$AWS_PROFILE" >/dev/null 2>&1 || true
    
    # Create and attach comprehensive policy for both functions
    cat > function-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/luxembourg-legal-jobs",
                "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/luxembourg-legal-jobs/index/*",
                "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/luxembourg-legal-requests",
                "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/luxembourg-legal-requests/index/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:$AWS_REGION:$ACCOUNT_ID:function:$PROCESSOR_FUNCTION_NAME"
            ]
        }
    ]
}
EOF

    FUNCTION_POLICY_NAME="$PROJECT_NAME-function-policy"
    
    # Create policy if it doesn't exist
    if aws iam get-policy --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$FUNCTION_POLICY_NAME" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_success "Function policy already exists"
    else
        aws iam create-policy \
            --policy-name "$FUNCTION_POLICY_NAME" \
            --policy-document file://function-policy.json \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "Function policy created"
    fi
    
    # Attach policy to role
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$FUNCTION_POLICY_NAME" \
        --profile "$AWS_PROFILE" >/dev/null 2>&1 || true
    
    LAMBDA_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    log_success "Lambda role configured: $LAMBDA_ROLE_ARN"
    
    # Wait for role to be ready
    log_info "Waiting for IAM role to be ready..."
    sleep 10
}

# Create both Lambda functions
create_lambda_functions() {
    log_info "Creating Lambda functions..."
    
    # Create API function
    create_api_function
    
    # Create Processor function
    create_processor_function
}

create_api_function() {
    log_info "Creating API handler function..."
    
    # Check if function exists
    if aws lambda get-function --function-name "$API_FUNCTION_NAME" --region "$AWS_REGION" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_info "Updating existing API function..."
        
        # Update function code
        aws lambda update-function-code \
            --function-name "$API_FUNCTION_NAME" \
            --image-uri "$API_ECR_URI:latest" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        # Wait for code update to complete
        aws lambda wait function-updated \
            --function-name "$API_FUNCTION_NAME" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE"
        
        # Update function configuration
        aws lambda update-function-configuration \
            --function-name "$API_FUNCTION_NAME" \
            --timeout 30 \
            --memory-size 512 \
            --environment "Variables={MCP_SERVER_URL=$MCP_SERVER_URL,ENVIRONMENT=$ENVIRONMENT,JOB_PROCESSOR_FUNCTION=$PROCESSOR_FUNCTION_NAME}" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "API function updated: $API_FUNCTION_NAME"
    else
        log_info "Creating new API function..."
        
        aws lambda create-function \
            --function-name "$API_FUNCTION_NAME" \
            --package-type Image \
            --code ImageUri="$API_ECR_URI:latest" \
            --role "$LAMBDA_ROLE_ARN" \
            --timeout 30 \
            --memory-size 512 \
            --environment "Variables={MCP_SERVER_URL=$MCP_SERVER_URL,ENVIRONMENT=$ENVIRONMENT,JOB_PROCESSOR_FUNCTION=$PROCESSOR_FUNCTION_NAME}" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "API function created: $API_FUNCTION_NAME"
    fi
    
    # Wait for function to be ready
    aws lambda wait function-active \
        --function-name "$API_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE"
    
    # Get Lambda function ARN
    API_LAMBDA_ARN=$(aws lambda get-function \
        --function-name "$API_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query Configuration.FunctionArn \
        --output text)
    
    log_success "API function ready: $API_LAMBDA_ARN"
}

create_processor_function() {
    log_info "Creating Job processor function..."
    
    # Check if function exists
    if aws lambda get-function --function-name "$PROCESSOR_FUNCTION_NAME" --region "$AWS_REGION" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
        log_info "Updating existing Processor function..."
        
        # Update function code
        aws lambda update-function-code \
            --function-name "$PROCESSOR_FUNCTION_NAME" \
            --image-uri "$PROCESSOR_ECR_URI:latest" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        # Wait for code update to complete
        aws lambda wait function-updated \
            --function-name "$PROCESSOR_FUNCTION_NAME" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE"
        
        # Update function configuration with 15-minute timeout
        aws lambda update-function-configuration \
            --function-name "$PROCESSOR_FUNCTION_NAME" \
            --timeout 900 \
            --memory-size 3008 \
            --environment "Variables={MCP_SERVER_URL=$MCP_SERVER_URL,ENVIRONMENT=$ENVIRONMENT,MODEL_PROVIDER=anthropic,GROQ_API_KEY=$GROQ_API_KEY,ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY}" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "Processor function updated: $PROCESSOR_FUNCTION_NAME"
    else
        log_info "Creating new Processor function..."
        
        aws lambda create-function \
            --function-name "$PROCESSOR_FUNCTION_NAME" \
            --package-type Image \
            --code ImageUri="$PROCESSOR_ECR_URI:latest" \
            --role "$LAMBDA_ROLE_ARN" \
            --timeout 900 \
            --memory-size 3008 \
            --environment "Variables={MCP_SERVER_URL=$MCP_SERVER_URL,ENVIRONMENT=$ENVIRONMENT,MODEL_PROVIDER=anthropic,GROQ_API_KEY=$GROQ_API_KEY,ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY}" \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
        
        log_success "Processor function created: $PROCESSOR_FUNCTION_NAME"
    fi
    
    # Wait for function to be ready
    aws lambda wait function-active \
        --function-name "$PROCESSOR_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE"
    
    # Get Lambda function ARN
    PROCESSOR_LAMBDA_ARN=$(aws lambda get-function \
        --function-name "$PROCESSOR_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query Configuration.FunctionArn \
        --output text)
    
    log_success "Processor function ready: $PROCESSOR_LAMBDA_ARN"
}

# Create API Gateway (same as before, but points to API function only)
create_api_gateway() {
    log_info "Creating API Gateway..."
    
    API_NAME="$PROJECT_NAME-api"
    
    # Create REST API
    API_ID=$(aws apigateway create-rest-api \
        --name "$API_NAME" \
        --description "Luxembourg Legal Assistant API - 2-Function Architecture" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query id \
        --output text)
    
    log_success "API Gateway created: $API_ID"
    
    # Get root resource ID
    ROOT_RESOURCE_ID=$(aws apigateway get-resources \
        --rest-api-id "$API_ID" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query 'items[0].id' \
        --output text)
    
    # Create resources and methods (same structure as before)
    create_api_resources_and_methods "$API_ID" "$ROOT_RESOURCE_ID"
    
    # Deploy API
    deploy_api "$API_ID"
}

create_api_resources_and_methods() {
    local api_id="$1"
    local root_id="$2"
    
    # Create resources
    create_api_resource "chat" "$api_id" "$root_id"
    CHAT_RESOURCE_ID="$RESOURCE_ID"
    
    create_api_resource "tools" "$api_id" "$root_id"
    TOOLS_RESOURCE_ID="$RESOURCE_ID"
    
    create_api_resource "health" "$api_id" "$root_id"
    HEALTH_RESOURCE_ID="$RESOURCE_ID"
    
    # Create job resources
    create_api_resource "job" "$api_id" "$root_id"
    JOB_RESOURCE_ID="$RESOURCE_ID"
    
    create_api_resource "{job_id}" "$api_id" "$JOB_RESOURCE_ID"
    JOB_ID_RESOURCE_ID="$RESOURCE_ID"
    
    create_api_resource "result" "$api_id" "$JOB_ID_RESOURCE_ID"
    JOB_RESULT_RESOURCE_ID="$RESOURCE_ID"
    
    # Create methods (all point to API function only)
    create_api_method_with_integration "$api_id" "$CHAT_RESOURCE_ID" "POST" "$API_LAMBDA_ARN" true
    create_api_method_with_integration "$api_id" "$TOOLS_RESOURCE_ID" "GET" "$API_LAMBDA_ARN" false
    create_api_method_with_integration "$api_id" "$HEALTH_RESOURCE_ID" "GET" "$API_LAMBDA_ARN" false
    create_api_method_with_integration "$api_id" "$JOB_ID_RESOURCE_ID" "GET" "$API_LAMBDA_ARN" false
    create_api_method_with_integration "$api_id" "$JOB_RESULT_RESOURCE_ID" "GET" "$API_LAMBDA_ARN" false
    
    # Create CORS
    create_cors_options "$api_id" "$CHAT_RESOURCE_ID"
}

# Helper functions (same as original script)
create_api_resource() {
    local path_part="$1"
    local api_id="$2"
    local parent_id="$3"
    
    RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id "$api_id" \
        --parent-id "$parent_id" \
        --path-part "$path_part" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query id \
        --output text)
    
    log_success "Created /$path_part resource: $RESOURCE_ID"
}

create_api_method_with_integration() {
    local api_id="$1"
    local resource_id="$2" 
    local http_method="$3"
    local lambda_arn="$4"
    local api_key_required="$5"
    
    # Create method
    if [ "$api_key_required" = "true" ]; then
        aws apigateway put-method \
            --rest-api-id "$api_id" \
            --resource-id "$resource_id" \
            --http-method "$http_method" \
            --authorization-type NONE \
            --api-key-required \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
    else
        aws apigateway put-method \
            --rest-api-id "$api_id" \
            --resource-id "$resource_id" \
            --http-method "$http_method" \
            --authorization-type NONE \
            --no-api-key-required \
            --region "$AWS_REGION" \
            --profile "$AWS_PROFILE" >/dev/null
    fi
    
    # Create integration
    aws apigateway put-integration \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method "$http_method" \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$lambda_arn/invocations" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    # Give API Gateway permission to invoke Lambda
    aws lambda add-permission \
        --function-name "$API_FUNCTION_NAME" \
        --statement-id "apigateway-invoke-$resource_id-$http_method" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$AWS_REGION:$ACCOUNT_ID:$api_id/*/*" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null 2>&1 || true
    
    log_success "Created $http_method method and Lambda integration"
}

create_cors_options() {
    local api_id="$1"
    local resource_id="$2"
    
    # Create OPTIONS method
    aws apigateway put-method \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    # Create MOCK integration
    aws apigateway put-integration \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    # Create method response
    aws apigateway put-method-response \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true, "method.response.header.Access-Control-Allow-Methods": true, "method.response.header.Access-Control-Allow-Origin": true}' \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    # Create integration response
    aws apigateway put-integration-response \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Api-Key'"'"'", "method.response.header.Access-Control-Allow-Methods": "'"'"'POST,OPTIONS'"'"'", "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}' \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    log_success "Created CORS OPTIONS method"
}

deploy_api() {
    local api_id="$1"
    
    log_info "Deploying API Gateway..."
    
    aws apigateway create-deployment \
        --rest-api-id "$api_id" \
        --stage-name "$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    API_URL="https://$api_id.execute-api.$AWS_REGION.amazonaws.com/$ENVIRONMENT"
    log_success "API deployed: $API_URL"
}

# Create API Key and Usage Plan (same as before)
create_api_key_and_usage_plan() {
    log_info "Creating API Key and Usage Plan..."
    
    # Create API Key
    API_KEY_ID=$(aws apigateway create-api-key \
        --name "$PROJECT_NAME-api-key" \
        --enabled \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query id \
        --output text)
    
    API_KEY_VALUE=$(aws apigateway get-api-key \
        --api-key "$API_KEY_ID" \
        --include-value \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query value \
        --output text)
    
    log_success "API Key created: $API_KEY_ID"
    
    # Create Usage Plan
    USAGE_PLAN_ID=$(aws apigateway create-usage-plan \
        --name "$PROJECT_NAME-usage-plan" \
        --quota limit=1000,period=DAY \
        --throttle rateLimit=10,burstLimit=20 \
        --api-stages apiId="$API_ID",stage="$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query id \
        --output text)
    
    # Link API Key to Usage Plan
    aws apigateway create-usage-plan-key \
        --usage-plan-id "$USAGE_PLAN_ID" \
        --key-type API_KEY \
        --key-id "$API_KEY_ID" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" >/dev/null
    
    log_success "Usage plan created and linked: $USAGE_PLAN_ID"
}

# Display deployment information
show_deployment_info() {
    log_success "🎉 2-Function Serverless Deployment completed successfully!"
    echo ""
    log_info "Deployment Information:"
    echo "========================"
    
    echo "🏗️  Architecture: 2-Function Serverless (Proper AWS Pattern)"
    echo "🚀 API Handler: $API_FUNCTION_NAME (fast response)"
    echo "⚙️  Job Processor: $PROCESSOR_FUNCTION_NAME (long running)"
    echo "🤖 Triple Provider Support: Groq + Claude + GPT-4.1-mini"
    echo "🌐 API Gateway URL: $API_URL"
    echo "🔑 API Key: $API_KEY_VALUE"
    echo ""
    echo "📡 Endpoints:"
    echo "  💬 Chat:   $API_URL/chat (creates async job)"
    echo "  🔧 Tools:  $API_URL/tools"
    echo "  ❤️  Health: $API_URL/health"
    echo "  📋 Job Status: $API_URL/job/{job_id}"
    echo "  📄 Job Result: $API_URL/job/{job_id}/result"
    echo ""
    echo "🔄 How it works:"
    echo "  1. POST /chat → API function creates job → triggers Processor function → returns job_id"
    echo "  2. GET /job/{id} → API function reads job status from DynamoDB"
    echo "  3. Processor function runs in background (up to 15 minutes)"
    echo ""
    echo "📋 Usage Examples:"
    echo "# 1. Create async job:"
    echo "curl -X POST '$API_URL/chat' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -H 'X-API-Key: $API_KEY_VALUE' \\"
    echo "  -d '{\"message\": \"Comment créer une SARL au Luxembourg?\", \"provider\": \"groq\"}'"
    echo ""
    echo "# 2. Check job progress:"
    echo "curl '$API_URL/job/{job_id}'"
    echo ""
    echo "# 3. Get job result:"
    echo "curl '$API_URL/job/{job_id}/result'"
    echo ""
    
    # Save API key to file for easy access
    echo "$API_KEY_VALUE" > api_key.txt
    log_info "API key saved to api_key.txt"
    
    # Save deployment info
    cat > deployment_info.json << EOF
{
    "architecture": "2-function-serverless",
    "api_url": "$API_URL",
    "api_key": "$API_KEY_VALUE",
    "functions": {
        "api_handler": "$API_FUNCTION_NAME",
        "job_processor": "$PROCESSOR_FUNCTION_NAME"
    },
    "ecr_repositories": {
        "api": "$API_ECR_URI",
        "processor": "$PROCESSOR_ECR_URI"
    },
    "endpoints": {
        "chat": "$API_URL/chat",
        "tools": "$API_URL/tools",
        "health": "$API_URL/health",
        "job_status": "$API_URL/job/{job_id}",
        "job_result": "$API_URL/job/{job_id}/result"
    },
    "providers": {
        "groq": {
            "model": "llama-3.3-70b-versatile",
            "cost_per_million_tokens": 0.0005,
            "speed": "very_fast"
        },
        "anthropic": {
            "model": "claude-3-5-sonnet-20241022",
            "cost_per_million_tokens": 0.015,
            "speed": "moderate"
        },
        "openai": {
            "model": "gpt-4.1-mini",
            "cost_per_million_tokens": 0.00015,
            "speed": "very_fast"
        }
    },
    "default_provider": "anthropic",
    "async_processing": {
        "enabled": true,
        "job_tracking": true,
        "progress_updates": true,
        "max_processing_time": "15 minutes"
    }
}
EOF
    log_info "Deployment info saved to deployment_info.json"
}

# Clean up temporary files
cleanup() {
    rm -f trust-policy.json function-policy.json
    log_info "Cleaned up temporary files"
}

# Main deployment function
main() {
    log_info "🚀 Starting 2-Function Serverless deployment of $PROJECT_NAME"
    log_info "Region: $AWS_REGION | Profile: $AWS_PROFILE | Environment: $ENVIRONMENT"
    log_info "Architecture: API Handler + Job Processor (Proper Serverless Pattern)"
    echo ""
    
    load_api_keys
    get_account_id
    create_ecr_repositories
    build_and_push_images
    create_lambda_role
    create_lambda_functions
    create_api_gateway
    create_api_key_and_usage_plan
    cleanup
    show_deployment_info
}

# Script execution
case "${1:-}" in
    "clean")
        log_info "Cleaning up deployment artifacts..."
        rm -f api_key.txt deployment_info.json trust-policy.json function-policy.json
        log_success "Cleanup completed"
        ;;
    "test")
        log_info "Testing API endpoints..."
        if [ -f "deployment_info.json" ]; then
            API_URL=$(grep -o '"api_url": "[^"]*' deployment_info.json | cut -d'"' -f4)
            API_KEY=$(grep -o '"api_key": "[^"]*' deployment_info.json | cut -d'"' -f4)
            
            echo "Testing health endpoint..."
            curl -s "$API_URL/health" | jq .
            echo ""
            echo "Testing chat endpoint..."
            curl -s -X POST "$API_URL/chat" \
                -H "Content-Type: application/json" \
                -H "X-API-Key: $API_KEY" \
                -d '{"message": "Test question", "provider": "groq"}' | jq .
        else
            log_error "No deployment info found. Run deployment first."
        fi
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|test]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Deploy the 2-function serverless application"
        echo "  clean      - Clean up deployment artifacts"
        echo "  test       - Test API endpoints"
        exit 1
        ;;
esac