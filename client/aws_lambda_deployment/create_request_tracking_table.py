#!/usr/bin/env python3
"""
Create DynamoDB table for comprehensive request tracking
Tracks: tokens, costs, processing time, user, company, and all request details
"""

import boto3
import json
from datetime import datetime

def create_request_tracking_table():
    """Create the luxembourg-legal-requests table for comprehensive tracking."""
    
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    
    table_name = 'luxembourg-legal-requests'
    
    # Check if table already exists
    try:
        table = dynamodb.Table(table_name)
        table.load()
        print(f"✅ Table {table_name} already exists")
        return table
    except:
        print(f"🔧 Creating table {table_name}...")
    
    # Create table with comprehensive schema
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'request_id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'request_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'company_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'created_at',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'company-date-index',
                'KeySchema': [
                    {
                        'AttributeName': 'company_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_at',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'BillingMode': 'PAY_PER_REQUEST'
            },
            {
                'IndexName': 'user-date-index',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_at',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'  # Pay per request, no capacity planning needed
    )
    
    # Wait for the table to be created
    print("⏳ Waiting for table to be created...")
    table.wait_until_exists()
    
    print(f"✅ Table {table_name} created successfully!")
    print(f"📊 Table ARN: {table.table_arn}")
    
    return table

def print_table_schema():
    """Print the complete table schema for reference."""
    
    schema = {
        "table_name": "luxembourg-legal-requests",
        "description": "Comprehensive request tracking for Luxembourg Legal Intelligence",
        "primary_key": "request_id (String)",
        "global_secondary_indexes": [
            {
                "name": "company-date-index",
                "partition_key": "company_id",
                "sort_key": "created_at",
                "description": "Query requests by company and date range"
            },
            {
                "name": "user-date-index", 
                "partition_key": "user_id",
                "sort_key": "created_at",
                "description": "Query requests by user and date range"
            }
        ],
        "attributes": {
            "request_id": "Unique identifier for each request (UUID)",
            "job_id": "Associated job ID for tracking",
            "company_id": "Company identifier",
            "user_id": "User identifier",
            "created_at": "ISO timestamp when request was created",
            "completed_at": "ISO timestamp when request was completed",
            "message": "Original user message/question",
            "message_length": "Length of user message in characters",
            "provider": "AI provider used (anthropic, groq, openai)",
            "model": "Specific model used (claude-3-5-sonnet-20241022, etc.)",
            "status": "Request status (created, processing, completed, failed)",
            "processing_time_seconds": "Total processing time in seconds",
            "tokens": {
                "input_tokens": "Total input tokens used",
                "output_tokens": "Total output tokens used", 
                "total_tokens": "Sum of input + output tokens"
            },
            "costs": {
                "input_cost_usd": "Cost for input tokens in USD",
                "output_cost_usd": "Cost for output tokens in USD",
                "total_cost_usd": "Total cost in USD"
            },
            "tools_execution": {
                "tools_used": "List of MCP tools used",
                "total_tools_called": "Number of tool calls made",
                "iterations": "Number of AI iterations"
            },
            "response_metrics": {
                "response_length": "Length of final response in characters",
                "response_truncated": "Boolean if response was truncated",
                "has_citations": "Boolean if response contains legal citations",
                "has_legal_sources": "Boolean if legal sources were found"
            },
            "performance_metrics": {
                "mcp_server_response_time": "MCP server response time",
                "ai_model_response_time": "AI model response time",
                "average_iteration_time": "Average time per AI iteration"
            },
            "error_info": {
                "error_message": "Error message if request failed",
                "error_type": "Type of error (timeout, api_error, etc.)",
                "failed_at_iteration": "Iteration number where failure occurred"
            }
        }
    }
    
    print("\n" + "="*80)
    print("📋 LUXEMBOURG LEGAL REQUESTS TABLE SCHEMA")
    print("="*80)
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    print("="*80)

if __name__ == "__main__":
    print("🏗️  Luxembourg Legal Intelligence - Request Tracking Setup")
    print("="*60)
    
    # Create the table
    table = create_request_tracking_table()
    
    # Print schema for reference
    print_table_schema()
    
    print("\n✅ Setup complete! The Lambda function can now track all requests.")
    print("🔧 Next: Update the Lambda function to use this table for request tracking.")