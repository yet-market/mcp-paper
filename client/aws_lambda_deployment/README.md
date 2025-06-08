# Luxembourg Legal Assistant - Enhanced 2-Function Serverless Architecture

## 🏗️ Architecture Overview

This deployment implements a **professional 2-function serverless architecture** for the Luxembourg Legal Intelligence MCP Server with enhanced multi-provider AI support and structured output capabilities.

### 🎯 Key Features

- **🚀 Multi-Provider AI Support**: OpenAI GPT-4.1-mini, Claude Sonnet, Groq Llama
- **🔧 6-Tool MCP Workflow**: Comprehensive legal research with all MCP tools
- **📊 Structured JSON Output**: Provider-specific structured output generation
- **📈 Enhanced Request Tracking**: Complete analytics and performance monitoring
- **⚡ Serverless Architecture**: Fast API responses with async background processing
- **🔐 Secure**: AWS IAM, API Gateway with API keys, DynamoDB encryption

## 📁 Project Structure

```
aws_lambda_deployment/
├── api_function/                    # Fast API handler (30s timeout)
│   ├── Dockerfile
│   ├── lambda_function.py          # Job creation and status endpoints
│   └── requirements.txt
├── processor_function/              # Long-running processor (15min timeout)
│   ├── Dockerfile
│   ├── lambda_function.py          # Enhanced legal research with MCP tools
│   └── requirements.txt
├── shared/                          # Shared utilities
│   └── dynamodb_manager.py         # DynamoDB job and request tracking
├── deploy_2_functions.sh           # Main deployment script
├── create_request_tracking_table.py # DynamoDB table setup
├── analytics_queries.py            # Request analytics queries
├── deployment_info.json            # Last deployment details
└── api_key.txt                     # Generated API key
```

## 🚀 Quick Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Docker** installed and running
3. **API Keys** in `.env` file:
   ```bash
   ANTHROPIC_API_KEY=your_claude_key
   GROQ_API_KEY=your_groq_key
   OPENAI_API_KEY=your_openai_key
   ```

### Deploy

```bash
# Make deployment script executable and run
chmod +x deploy_2_functions.sh
./deploy_2_functions.sh
```

### Test Deployment

```bash
# Test health endpoint
./deploy_2_functions.sh test
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health and provider info |
| `/tools` | GET | Available MCP tools and capabilities |
| `/chat` | POST | Create async legal research job |
| `/job/{id}` | GET | Job status and progress |
| `/job/{id}/result` | GET | Complete structured legal analysis |

## 🔧 Usage Examples

### 1. Create Legal Research Job

```bash
curl -X POST 'https://your-api-gateway-url/prod/chat' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "message": "What are the requirements for creating a SARL in Luxembourg?",
    "provider": "openai",
    "company_id": "your_company",
    "user_id": "your_user"
  }'

# Response:
{
  "job_id": "uuid-job-id",
  "status": "created",
  "endpoints": {
    "status": "/job/uuid-job-id",
    "result": "/job/uuid-job-id/result"
  },
  "processing_info": {
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "workflow": "enhanced_6_tool_mcp_workflow",
    "structured_output": true
  }
}
```

### 2. Check Job Progress

```bash
curl 'https://your-api-gateway-url/prod/job/uuid-job-id'

# Response:
{
  "job_id": "uuid-job-id",
  "status": "processing",
  "processing_details": {
    "current_stage": "mcp_tools_execution",
    "percentage": 45,
    "current_action": "Executing MCP tools - iteration 3/15"
  }
}
```

### 3. Get Structured Legal Analysis

```bash
curl 'https://your-api-gateway-url/prod/job/uuid-job-id/result'

# Response: Complete structured JSON with 5 sections:
{
  "legal_analysis": {
    "answer": {
      "summary": "Executive summary...",
      "key_points": ["Point 1", "Point 2"],
      "exhaustive_content": "# Complete legal analysis...",
      "practical_guidance": "Step-by-step guide..."
    },
    "reference_sources": {
      "total_sources": 5,
      "primary_laws": [...],
      "supporting_regulations": [...]
    },
    "citations_network": {
      "total_citations": 23,
      "key_relationships": [...]
    },
    "historique_amendements": {
      "total_amendments": 8,
      "major_changes": [...]
    },
    "validite_legale": {
      "overall_status": "current",
      "validity_details": [...]
    }
  }
}
```

## 🤖 Multi-Provider Support

### Available Providers

| Provider | Model | Structured Output | Speed | Cost |
|----------|--------|------------------|-------|------|
| **OpenAI** | gpt-4.1-mini | Native JSON | Very Fast | $0.00015/1M tokens |
| **Claude** | claude-3-5-sonnet | Prompt-based | Moderate | $0.003/1M tokens |
| **Groq** | llama-3.3-70b | Prompt-based | Very Fast | $0.0005/1M tokens |

### Provider Selection

```bash
# Use OpenAI (fastest, cheapest)
"provider": "openai"

# Use Claude (highest quality)
"provider": "anthropic"

# Use Groq (fastest inference)
"provider": "groq"

# Auto-select (defaults to Claude)
# No provider specified
```

## 📊 Enhanced Request Tracking

The system tracks comprehensive analytics in DynamoDB:

- **Performance Metrics**: Processing time, iterations, tool usage
- **Cost Analysis**: Token usage, estimated costs per provider
- **Quality Metrics**: Analysis depth, citation count, source quality
- **Legal Intelligence**: MCP tool execution, structured output generation

### View Analytics

```python
# Run analytics queries
python analytics_queries.py
```

## 🔧 MCP Tools Integration

The system uses all 6 professional MCP tools systematically:

1. **search_documents**: Find legal documents by keyword
2. **get_citations**: Analyze citation networks (75K+ relationships)
3. **get_amendments**: Track legal evolution (26K+ modifications)
4. **check_legal_status**: Verify current validity
5. **get_relationships**: Map legal hierarchy
6. **extract_content**: Get full legal text with structure

## 🏗️ Technical Architecture

### API Function (Fast Response)
- **Purpose**: Handle requests, create jobs, return status
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Triggers**: Job processor function asynchronously

### Processor Function (Long Running)
- **Purpose**: Execute MCP workflow, generate structured output
- **Timeout**: 15 minutes
- **Memory**: 3008 MB
- **Features**: Multi-provider AI, comprehensive tool usage

### DynamoDB Tables
- **luxembourg-legal-jobs**: Job tracking and progress
- **luxembourg-legal-requests**: Enhanced analytics and metrics

## 🔐 Security & Permissions

- **API Gateway**: API key authentication
- **Lambda**: IAM roles with minimal permissions
- **DynamoDB**: Encryption at rest and in transit
- **Environment Variables**: Secure API key storage

## 📈 Monitoring & Logs

```bash
# View API function logs
aws logs tail /aws/lambda/luxembourg-legal-assistant-api --follow

# View processor function logs
aws logs tail /aws/lambda/luxembourg-legal-assistant-processor --follow
```

## 🛠️ Maintenance

### Update Functions
```bash
# Redeploy with updates
./deploy_2_functions.sh
```

### Clean Up
```bash
# Remove deployment artifacts
./deploy_2_functions.sh clean
```

## 📋 Environment Variables

| Variable | Function | Description |
|----------|----------|-------------|
| `MCP_SERVER_URL` | Both | MCP server endpoint |
| `JOB_PROCESSOR_FUNCTION` | API | Processor function name |
| `ANTHROPIC_API_KEY` | Processor | Claude API key |
| `GROQ_API_KEY` | Processor | Groq API key |
| `OPENAI_API_KEY` | Processor | OpenAI API key |
| `MODEL_PROVIDER` | Processor | Default provider |

## 🎯 Performance Benchmarks

- **API Response**: < 2 seconds (job creation)
- **Legal Research**: 2-5 minutes (complete analysis)
- **MCP Tools**: 6 tools executed systematically
- **Structured Output**: 5 comprehensive sections
- **Cost Efficiency**: $0.001-0.005 per analysis

## 🚨 Troubleshooting

### Common Issues

1. **Job Failed**: Check processor function logs
2. **MCP Connection**: Verify MCP_SERVER_URL
3. **Provider Error**: Check API keys in environment
4. **DynamoDB Error**: Verify table permissions

### Support

- Check CloudWatch logs for detailed error information
- Verify API keys are valid and have sufficient credits
- Ensure MCP server is accessible from Lambda