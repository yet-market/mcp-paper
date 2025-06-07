# 🚀 Multi-Model Luxembourg Legal Assistant - AWS Lambda Deployment

Complete serverless deployment of the Luxembourg Legal Assistant with **configurable AWS Bedrock model support**. Choose from Claude, Mistral, Llama, Cohere, or Amazon Titan models.

## 🏗️ Architecture

```
Client Application → API Gateway → Lambda (ECR Container) → AWS Bedrock (Any Model) + MCP Server
```

## 🤖 Supported Models

### 🧠 Anthropic Claude
- **`anthropic.claude-3-5-sonnet-20241022-v2:0`** (Recommended)
- **`anthropic.claude-3-haiku-20240307-v1:0`** (Fast & Cost-effective)

### 🔥 Mistral
- **`mistral.mistral-7b-instruct-v0:2`** (Budget-friendly)
- **`mistral.mixtral-8x7b-instruct-v0:1`** (Powerful)

### 🦙 Meta Llama
- **`meta.llama3-70b-instruct-v1:0`** (High performance)
- **`meta.llama3-8b-instruct-v1:0`** (Fast inference)

### 🌊 Cohere
- **`cohere.command-r-plus-v1:0`** (Advanced reasoning)
- **`cohere.command-r-v1:0`** (Standard performance)

### 🏔️ Amazon Titan
- **`amazon.titan-text-premier-v1:0`** (Enterprise-grade)
- **`amazon.titan-text-express-v1`** (Fast responses)

## 📁 Deployment Files

- `lambda_function.py` - Multi-model Lambda handler with configurable AWS Bedrock support
- `Dockerfile` - Container definition for Lambda
- `requirements.txt` - Python dependencies
- `deploy.sh` - Interactive deployment script with model selection
- `README.md` - This comprehensive documentation

## 🚀 Quick Deployment

### Prerequisites

1. **AWS CLI** configured with appropriate profile
2. **Docker** installed and running
3. **Terraform** installed (v1.0+)
4. **AWS IAM permissions** for Bedrock, Lambda, ECR, API Gateway

### One-Command Deployment

```bash
cd client/aws_lambda_deployment
./deploy.sh
```

The interactive script will:
1. ✅ Check dependencies and AWS credentials
2. 🤖 Let you choose your preferred Bedrock model
3. 🔧 Configure MCP server connection
4. 🏗️ Build Docker container for Lambda
5. 📦 Push to ECR repository
6. 🚀 Deploy infrastructure with Terraform
7. 🔑 Generate API key and endpoints

### Model Selection Menu

```
Select AWS Bedrock model:
1) Claude 3.5 Sonnet (Recommended)
2) Claude 3 Haiku (Fast & Cheap)
3) Mistral 7B (Budget)
4) Llama 3 70B (Powerful)
5) Cohere Command R+
6) Custom model ID
```

## 🌐 API Endpoints

After deployment, you'll get:

### `/chat` - Legal Assistant (POST)
Main conversational interface with automatic legal document search.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY`

**Body:**
```json
{
  "message": "Comment créer une SARL au Luxembourg?"
}
```

**Response:**
```json
{
  "response": "Pour créer une SARL au Luxembourg...",
  "tools_used": ["search_luxembourg_documents"],
  "model": {
    "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "provider": "anthropic"
  },
  "cost_info": {
    "estimated_cost_usd": 0.0001,
    "processing_time_ms": 1250
  }
}
```

### `/search` - Document Search (POST)
Direct access to Luxembourg legal documents.

**Body:**
```json
{
  "keywords": "SARL|société",
  "limit": 5,
  "include_content": true
}
```

### `/tools` - Available Tools (GET)
List MCP tools and current model configuration.

**Response:**
```json
{
  "total_tools": 12,
  "available_tools": ["search_documents_with_full_metadata", ...],
  "model": {
    "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "provider": "anthropic"
  }
}
```

### `/health` - Health Check (GET)
System status with model information (no API key required).

## 💰 Cost Comparison by Model

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Use Case |
|-------|----------------------|------------------------|----------|
| Claude 3.5 Sonnet | $3.00 | $15.00 | Best quality, complex reasoning |
| Claude 3 Haiku | $0.25 | $1.25 | Fast responses, simple queries |
| Mistral 7B | $0.15 | $0.60 | Budget-friendly, good performance |
| Llama 3 70B | $0.65 | $0.80 | Balanced cost/performance |
| Cohere Command R+ | $1.00 | $2.00 | Advanced reasoning tasks |
| Titan Express | $0.50 | $1.50 | Enterprise, reliable |

## 🔧 Management Commands

### List Supported Models
```bash
./deploy.sh models
```

### Update Deployment (Change Model)
```bash
# Edit terraform.tfvars to change model_id
vim terraform.tfvars

# Redeploy
./deploy.sh
```

### Clean Artifacts
```bash
./deploy.sh clean
```

### Destroy Infrastructure
```bash
./deploy.sh destroy
```

## 🔑 Model Configuration

### Environment Variables (Lambda)
- `MODEL_ID` - AWS Bedrock model identifier (configurable)
- `MCP_SERVER_URL` - Luxembourg legal MCP server endpoint
- `BEDROCK_REGION` - AWS region (default: eu-west-2)

### Change Model After Deployment
1. Edit `terraform.tfvars`:
   ```hcl
   model_id = "anthropic.claude-3-haiku-20240307-v1:0"
   ```
2. Redeploy: `./deploy.sh`

### Custom Model Configuration
```bash
# For custom model
echo 'model_id = "your-custom-model-id"' >> terraform.tfvars
./deploy.sh
```

## 🛡️ Security Features

- **API Key Authentication** required for all endpoints (except health)
- **Rate Limiting**: 10 req/sec, 20 burst, 1000/day quota
- **CORS Support** for web applications
- **IAM Policies** with least privilege access
- **Environment Variables** for sensitive configuration
- **Multi-region support** for compliance

## 📊 Monitoring & Debugging

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/luxembourg-legal-assistant-function --follow --profile yet
```

### Test Function
```bash
aws lambda invoke --profile yet \
  --function-name luxembourg-legal-assistant-function \
  --payload '{"httpMethod":"GET","path":"/health"}' \
  response.json
```

### Monitor Costs
```bash
# View Bedrock usage
aws bedrock get-model-invocation-logs --profile yet

# API Gateway metrics
aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway \
  --metric-name Count --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z --period 3600 \
  --statistics Sum --profile yet
```

## 🚨 Troubleshooting

### Common Issues

1. **Model Not Available in Region**
   ```bash
   aws bedrock list-foundation-models --region eu-west-2 --profile yet
   ```

2. **Lambda Timeout**
   - Increase timeout in Terraform configuration
   - Check MCP server connectivity

3. **High Costs**
   - Switch to cheaper model (Haiku, Mistral 7B)
   - Implement request caching
   - Add usage limits

### Model-Specific Issues

#### Claude Models
- Ensure you have Anthropic model access in AWS Bedrock
- Check message format compliance

#### Mistral Models
- Verify prompt format with `<s>[INST]` tags
- Check stop sequences configuration

#### Llama Models
- Confirm Meta model access approval
- Validate chat template format

## 🎯 Integration Examples

### Next.js API Route
```javascript
// pages/api/legal/chat.js
export default async function handler(req, res) {
  const response = await fetch(process.env.LAMBDA_CHAT_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.LEGAL_API_KEY
    },
    body: JSON.stringify({
      message: req.body.message
    })
  });
  
  const data = await response.json();
  res.json(data);
}
```

### Python Client
```python
import requests

def ask_legal_question(question, model="claude"):
    response = requests.post(
        "YOUR_LAMBDA_ENDPOINT/chat",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "YOUR_API_KEY"
        },
        json={"message": question}
    )
    return response.json()

# Usage
result = ask_legal_question("Comment créer une SARL?")
print(f"Model used: {result['model']['id']}")
print(f"Response: {result['response']}")
```

### React Hook
```javascript
import { useState } from 'react';

export function useLegalAssistant() {
  const [loading, setLoading] = useState(false);
  
  const ask = async (question) => {
    setLoading(true);
    try {
      const response = await fetch('/api/legal/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question })
      });
      return await response.json();
    } finally {
      setLoading(false);
    }
  };
  
  return { ask, loading };
}
```

## 📈 Production Optimization

### Performance Tips
1. **Model Selection**: Use Haiku for simple queries, Sonnet for complex analysis
2. **Caching**: Implement response caching for common questions
3. **Batch Processing**: Group similar requests when possible
4. **Regional Deployment**: Deploy closer to users

### Cost Optimization
1. **Smart Model Routing**: Route simple queries to cheaper models
2. **Request Filtering**: Pre-filter non-legal questions
3. **Usage Monitoring**: Set up billing alerts
4. **Cache Responses**: Cache common legal document searches

### Scaling Considerations
1. **Concurrent Execution**: Configure Lambda concurrency limits
2. **API Rate Limits**: Adjust based on expected traffic
3. **Multi-Region**: Deploy in multiple regions for global access
4. **CDN Integration**: Cache static responses via CloudFront

## 🌟 Advanced Features

### Multi-Model Routing
```python
# Route based on query complexity
def select_model(question):
    if len(question.split()) < 5:
        return "anthropic.claude-3-haiku-20240307-v1:0"  # Fast & cheap
    elif "complex" in question.lower():
        return "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Powerful
    else:
        return "mistral.mistral-7b-instruct-v0:2"  # Balanced
```

### Custom Prompt Templates
```python
# Model-specific optimizations
PROMPT_TEMPLATES = {
    "anthropic": "Human: {system}\n\n{question}\n\nAssistant:",
    "mistral": "<s>[INST] {system}\n\n{question} [/INST]",
    "meta": "<|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|>..."
}
```

## 📋 Checklist for Production

- [ ] Model selection based on use case and budget
- [ ] API key security and rotation
- [ ] Rate limiting configuration
- [ ] Cost monitoring and alerts
- [ ] Error handling and fallbacks
- [ ] Performance monitoring
- [ ] Backup model configuration
- [ ] Documentation for team
- [ ] Integration testing
- [ ] Load testing with expected traffic

Your Luxembourg Legal AI is now production-ready with configurable model support! 🎉

Choose your model, deploy, and start serving intelligent legal assistance! 🚀