# 2-Function Serverless Architecture

## Overview

The Luxembourg Legal Assistant now uses a proper 2-function serverless architecture that follows AWS best practices for long-running asynchronous processing.

## Architecture Components

### 1. API Handler Function (`luxembourg-legal-assistant-api`)
- **Purpose**: Fast API responses and job creation
- **Timeout**: 30 seconds  
- **Memory**: 512 MB
- **Responsibilities**:
  - Handle HTTP requests via API Gateway
  - Create jobs in DynamoDB
  - Trigger async processing
  - Provide job status and results
  - Return immediate responses (202 Accepted)

### 2. Job Processor Function (`luxembourg-legal-assistant-processor`) 
- **Purpose**: Heavy legal research processing
- **Timeout**: 15 minutes (900 seconds)
- **Memory**: 3008 MB
- **Responsibilities**:
  - Process legal research jobs
  - Use MCP tools for document analysis
  - Integrate with Claude, Groq, and OpenAI
  - Update job progress in real-time
  - Store final results in DynamoDB

## Default Configuration

- **Default AI Provider**: Claude Sonnet (anthropic)
- **Default Model**: `claude-3-5-sonnet-20241022`
- **MCP Server**: `https://yet-mcp-legilux.site/mcp/`
- **Storage**: DynamoDB (2 tables)
- **Job Tracking**: Comprehensive real-time progress

## API Endpoints

### Current Deployment
- **Base URL**: `https://rw9x4ki667.execute-api.eu-west-2.amazonaws.com/prod`
- **API Key**: `58KyD7YQAW4ZXzunWs9U56zN4cP5esQn58ijc0js`

### Available Endpoints

#### 1. Create Async Job
```bash
POST /chat
Headers: X-API-Key: {api_key}
Body: {
  "message": "Comment créer une SARL au Luxembourg?",
  "provider": "anthropic",  # optional: anthropic, groq, openai
  "company_id": "my-company",  # optional
  "user_id": "user123"  # optional
}

Response: {
  "job_id": "uuid",
  "status": "created",
  "endpoints": {
    "status": "/job/{job_id}",
    "result": "/job/{job_id}/result"
  }
}
```

#### 2. Check Job Status  
```bash
GET /job/{job_id}

Response: {
  "job_id": "uuid",
  "status": "processing|completed|failed",
  "processing_details": {
    "current_stage": "ai_processing",
    "percentage": 75,
    "estimated_remaining_seconds": 30
  }
}
```

#### 3. Get Job Result
```bash  
GET /job/{job_id}/result

Response: {
  "response": {
    "content": "Detailed legal analysis...",
    "language": "french"
  },
  "tools_execution": {
    "available_tools": 6,
    "tools_used": ["search_documents", "extract_content"]
  },
  "cost_analysis": {
    "total_tokens": 1250,
    "total_cost_usd": 0.018750
  }
}
```

#### 4. Health Check
```bash
GET /health

Response: {
  "status": "healthy",
  "providers": {
    "available": ["anthropic", "groq", "openai"],
    "default": "anthropic"
  },
  "pattern": "2-Function Serverless"
}
```

#### 5. Tools Information
```bash
GET /tools

Response (dynamic list of all tools with schemas):
```
{
  "total_tools": 6,
  "available_tools": [
    {
      "name": "search_documents",
      "description": "Find documents by keyword",
      "inputSchema": { /* JSON Schema for search_documents */ }
    },
    /* … other tools … */
  ],
  "providers": {
    "default": "anthropic",
    "models": {
      "anthropic": "claude-3-5-sonnet-20241022",
      "groq": "llama-3.3-70b-versatile",
      "openai": "gpt-4.1-mini"
    }
  },
  "mcp_server": "https://yet-mcp-legilux.site/mcp/",
  "pattern": "2-Function Serverless"
}
```

#### 6. Invoke Single MCP Tool
```bash
POST /tool/{tool_name}
Headers: X-API-Key: {api_key}, Content-Type: application/json
Body: { /* parameters matching the tool's inputSchema */ }

# Response: raw JSON result from the specified MCP tool
{
  /* tool-specific JSON output */
}
```

## Workflow

1. **Job Creation**: POST /chat → API function creates job → returns job_id immediately
2. **Async Processing**: API function triggers Processor function asynchronously  
3. **Progress Tracking**: Processor function updates DynamoDB with real-time progress
4. **Status Monitoring**: GET /job/{id} → API function reads status from DynamoDB
5. **Result Retrieval**: GET /job/{id}/result → API function returns final result

## Benefits vs Monolithic

### ✅ Advantages
- **No timeouts**: Processor can run up to 15 minutes
- **Better resource allocation**: API function is lightweight, Processor is powerful
- **Scalability**: Functions scale independently
- **Cost efficiency**: Pay only for what you use
- **Proper async pattern**: Immediate responses, background processing
- **Real-time progress**: Live status updates during processing

### 🏗️ Architecture Comparison

| Component | Monolithic | 2-Function Serverless |
|-----------|------------|----------------------|
| API Response | Synchronous (45s timeout) | Async (immediate) |
| Processing Time | Limited to Lambda timeout | Up to 15 minutes |
| Memory Usage | Fixed for all operations | Optimized per function |
| Scalability | Single function scaling | Independent scaling |
| Error Handling | All-or-nothing | Isolated failure domains |

## Deployment

Use the `deploy_2_functions.sh` script:

```bash
./deploy_2_functions.sh
```

### Deployment Commands
- `./deploy_2_functions.sh` - Deploy both functions
- `./deploy_2_functions.sh clean` - Clean up artifacts  
- `./deploy_2_functions.sh test` - Test endpoints

## DynamoDB Tables

### 1. luxembourg-legal-jobs
- **Purpose**: Job tracking and progress
- **Primary Key**: job_id (String)
- **TTL**: 7 days after completion
- **Indexes**: company-date-index, user-date-index

### 2. luxembourg-legal-requests  
- **Purpose**: Request analytics and cost tracking
- **Primary Key**: request_id (String)
- **GSI**: company-date-index, user-date-index
- **Metrics**: tokens, costs, tools usage, performance

## AI Providers

### Default: Claude Sonnet
- **Model**: claude-3-5-sonnet-20241022
- **Strengths**: Best legal reasoning, structured output
- **Cost**: $3.00 input + $15.00 output per 1M tokens

### Alternative: Groq (Llama)
- **Model**: llama-3.3-70b-versatile  
- **Strengths**: Very fast, low cost
- **Cost**: $0.59 input + $0.79 output per 1M tokens

### Alternative: OpenAI
- **Model**: gpt-4.1-nano
- **Strengths**: Very fast, extremely low cost
- **Cost**: $0.20 input + $0.80 output per 1M tokens

## MCP Legal Tools

6 professional legal research tools available:

1. **search_documents**: Find legal documents by keyword
2. **get_citations**: Discover legal citation networks  
3. **get_amendments**: Track legislative changes
4. **check_legal_status**: Verify current validity
5. **get_relationships**: Understand legal hierarchies
6. **extract_content**: Get full legal text content

## Example Usage

### Test with SARL Question
```bash
# 1. Create job
JOB_ID=$(curl -s -X POST 'https://rw9x4ki667.execute-api.eu-west-2.amazonaws.com/prod/chat' \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: 58KyD7YQAW4ZXzunWs9U56zN4cP5esQn58ijc0js' \
  -d '{"message": "Quels sont les documents requis pour créer une SARL?"}' | jq -r .job_id)

# 2. Monitor progress  
curl "https://rw9x4ki667.execute-api.eu-west-2.amazonaws.com/prod/job/$JOB_ID" | jq .processing_details

# 3. Get result when completed
curl "https://rw9x4ki667.execute-api.eu-west-2.amazonaws.com/prod/job/$JOB_ID/result" | jq .
```

## Monitoring & Logs

### CloudWatch Logs
- `/aws/lambda/luxembourg-legal-assistant-api`
- `/aws/lambda/luxembourg-legal-assistant-processor`

### Key Metrics
- Job creation rate
- Processing success rate  
- Average processing time
- Cost per request
- Tool usage patterns

## Next Development

For future development, always use this 2-function architecture:

1. **API changes**: Modify `api_function/lambda_function.py`
2. **Processing changes**: Modify `processor_function/lambda_function.py`  
3. **Shared logic**: Modify `shared/dynamodb_manager.py`
4. **Deploy**: Run `./deploy_2_functions.sh`

This architecture is production-ready and follows AWS serverless best practices.