#!/usr/bin/env python3
"""
API Handler Lambda Function for Luxembourg Legal Assistant
Fast response - creates jobs and returns immediately
"""

import os
import json
import boto3
import logging
import time
from typing import Dict, Any

# Import shared DynamoDB manager
import sys
sys.path.append('/opt/python')
from shared.dynamodb_manager import DynamoDBJobManager, JobStatus

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main Lambda handler for API Gateway integration."""
    try:
        # Parse the request
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        body = event.get("body", "")
        
        # Parse body if present
        request_data = {}
        if body:
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Invalid JSON in request body"})
                }
        
        # Route the request
        if path == "/chat" and http_method == "POST":
            return handle_chat(request_data)
        elif path == "/health" and http_method == "GET":
            return handle_health()
        elif path == "/tools" and http_method == "GET":
            return handle_tools()
        elif path.startswith("/job/") and http_method == "GET":
            # Handle job status and result endpoints
            parts = path.split("/")
            if len(parts) >= 3:
                job_id = parts[2]
                if len(parts) == 3:
                    return handle_job_status(job_id)
                elif len(parts) == 4 and parts[3] == "result":
                    return handle_job_result(job_id)
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Endpoint not found"})
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }


def handle_chat(request_data: Dict[str, Any]):
    """Handle /chat endpoint - create job and trigger async processing."""
    try:
        message = request_data.get("message", "").strip()
        if not message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Message is required"})
            }
        
        # Get optional parameters
        provider = request_data.get("provider", "").strip() or None
        company_id = request_data.get("company_id", "default")
        user_id = request_data.get("user_id", "default")
        
        # Validate provider if specified
        supported_providers = ["anthropic", "groq", "openai"]
        if provider and provider not in supported_providers:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": f"Invalid provider '{provider}'. Supported providers: {supported_providers}",
                    "supported_providers": {
                        "anthropic": "claude-3-5-sonnet-20241022",
                        "groq": "llama-3.3-70b-versatile", 
                        "openai": "gpt-4.1-mini"
                    }
                })
            }
        
        # Create job in DynamoDB
        job_id = DynamoDBJobManager.create_job(message, provider, company_id, user_id)
        
        # Trigger async job processing
        try:
            lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'eu-west-2'))
            
            # Invoke job processor function asynchronously
            lambda_client.invoke(
                FunctionName=os.environ.get('JOB_PROCESSOR_FUNCTION', 'luxembourg-legal-job-processor'),
                InvocationType='Event',  # Async invocation
                Payload=json.dumps({
                    'job_id': job_id,
                    'message': message,
                    'provider': provider,
                    'company_id': company_id,
                    'user_id': user_id
                })
            )
            
            logger.info(f"Triggered async processing for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger async processing: {e}")
            # Mark job as failed if we can't start processing
            DynamoDBJobManager.fail_job(job_id, f"Failed to start processing: {str(e)}")
            
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Failed to start job processing"})
            }
        
        # Return job_id immediately (202 Accepted)
        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-API-Key"
            },
            "body": json.dumps({
                "job_id": job_id,
                "status": "created",
                "message": "Job created and processing started. Use GET /job/{job_id} to check progress.",
                "endpoints": {
                    "status": f"/job/{job_id}",
                    "result": f"/job/{job_id}/result"
                },
                "processing_info": {
                    "estimated_time": "2-5 minutes",
                    "provider": provider or "anthropic",
                    "model": {
                        "anthropic": "claude-3-5-sonnet-20241022",
                        "groq": "llama-3.3-70b-versatile",
                        "openai": "gpt-4.1-mini"
                    }.get(provider or "anthropic"),
                    "workflow": "enhanced_6_tool_mcp_workflow",
                    "structured_output": True,
                    "request_tracking": True
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Chat handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_job_status(job_id: str):
    """Handle GET /job/{job_id} - return job status from DynamoDB."""
    try:
        job = DynamoDBJobManager.get_job(job_id)
        if not job:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Job not found"})
            }
        
        # Return current status with real-time progress
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "job_id": job["job_id"],
                "status": job["status"],
                "company_id": job.get("company_id"),
                "user_id": job.get("user_id"),
                "provider": job["provider"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "processing_details": job.get("processing_details", {}),
                "has_result": job.get("result") is not None,
                "has_error": job.get("error") is not None
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Job status handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_job_result(job_id: str):
    """Handle GET /job/{job_id}/result - return job result from DynamoDB."""
    try:
        job = DynamoDBJobManager.get_job(job_id)
        if not job:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Job not found"})
            }
        
        if job["status"] == JobStatus.COMPLETED and job.get("result"):
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(job["result"], ensure_ascii=False, default=str)
            }
        elif job["status"] == JobStatus.FAILED:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Job failed",
                    "details": job.get("error"),
                    "job_id": job_id
                })
            }
        elif job["status"] in [JobStatus.CREATED, JobStatus.PROCESSING]:
            return {
                "statusCode": 202,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "message": "Job still processing",
                    "status": job["status"],
                    "progress": job.get("processing_details", {}),
                    "job_id": job_id
                })
            }
        else:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unknown job status"})
            }
        
    except Exception as e:
        logger.error(f"Job result handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_tools():
    """Handle /tools endpoint."""
    try:
        tools_info = {
            "total_tools": 6,  # Known MCP tools
            "available_tools": [
                "search_documents", "get_citations", "get_amendments", 
                "check_legal_status", "get_relationships", "extract_content"
            ],
            "providers": {
                "available": ["anthropic", "groq", "openai"],
                "default": "anthropic",
                "models": {
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "groq": "llama-3.3-70b-versatile",
                    "openai": "gpt-4.1-mini"
                }
            },
            "mcp_server": os.environ.get("MCP_SERVER_URL", "https://yet-mcp-legilux.site/mcp/"),
            "storage": "DynamoDB",
            "pattern": "2-Function Serverless",
            "timestamp": int(time.time())
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(tools_info, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Tools handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_health():
    """Handle /health endpoint."""
    try:
        health_data = {
            "status": "healthy",
            "providers": {
                "available": ["anthropic", "groq", "openai"],
                "default": os.environ.get("MODEL_PROVIDER", "anthropic"),
                "models": {
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "groq": "llama-3.3-70b-versatile",
                    "openai": "gpt-4.1-mini"
                }
            },
            "mcp_server": os.environ.get("MCP_SERVER_URL", "https://yet-mcp-legilux.site/mcp/"),
            "storage": "DynamoDB",
            "pattern": "2-Function Serverless",
            "supported_providers": {
                "groq": ["llama-3.3-70b-versatile"],
                "anthropic": ["claude-3-5-sonnet-20241022"],
                "openai": ["gpt-4.1-mini"]
            },
            "timestamp": int(time.time())
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(health_data)
        }
        
    except Exception as e:
        logger.error(f"Health handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }