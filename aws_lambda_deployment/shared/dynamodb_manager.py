#!/usr/bin/env python3
"""
Shared DynamoDB Job Manager for Luxembourg Legal Assistant
Used by both API handler and Job processor functions
"""

import os
import json
import boto3
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from decimal import Decimal

def convert_to_decimals(obj):
    """Convert Python numeric types to DynamoDB Decimal types for storage."""
    if isinstance(obj, list):
        return [convert_to_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, (int, float)):
        try:
            # Handle special float values and long precision
            if obj != obj:  # NaN check
                return str(obj)
            elif obj == float('inf') or obj == float('-inf'):
                return str(obj)
            else:
                # Round floats to reasonable precision to avoid Decimal conversion issues
                if isinstance(obj, float):
                    obj = round(obj, 6)  # Limit to 6 decimal places
                return Decimal(str(obj))
        except Exception as e:
            logger.warning(f"Could not convert {obj} to Decimal: {e}, using string instead")
            return str(obj)
    else:
        return obj

# Configure logging
logger = logging.getLogger(__name__)

# Global DynamoDB resource
dynamodb = None

def get_dynamodb():
    global dynamodb
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'eu-west-2'))
    return dynamodb

def get_jobs_table():
    return get_dynamodb().Table('luxembourg-legal-jobs')

def convert_decimals(obj):
    """Convert DynamoDB Decimal types to native Python types for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert Decimal to int if it's a whole number, else float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

class JobStatus:
    """Job status constants."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DynamoDBJobManager:
    """DynamoDB-based job management with real-time progress tracking."""
    
    @staticmethod
    def create_job(message: str, provider: Optional[str] = None, company_id: str = "default", user_id: str = "default") -> str:
        """Create a new job in DynamoDB."""
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        job_item = {
            'job_id': job_id,
            'company_id': company_id,
            'user_id': user_id,
            'status': JobStatus.CREATED,
            'message': message,
            'provider': provider or 'anthropic',
            'created_at': now,
            'updated_at': now,
            'processing_details': {
                'current_stage': 'initialization',
                'current_action': 'Job created, waiting to start processing',
                'percentage': 0,
                'estimated_remaining_seconds': 300,
                'stages_completed': [],
                'current_tools_execution': {},
                'ai_interaction': {
                    'model_calls': 0,
                    'tokens_used': 0,
                    'current_ai_task': 'Preparing for legal research'
                }
            },
            'result': None,
            'error': None
        }
        
        try:
            table = get_jobs_table()
            table.put_item(Item=job_item)
            logger.info(f"Created job {job_id} for company {company_id}, user {user_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to create job in DynamoDB: {e}")
            raise
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """Get job from DynamoDB."""
        try:
            table = get_jobs_table()
            response = table.get_item(Key={'job_id': job_id})
            item = response.get('Item')
            if item:
                # Convert DynamoDB Decimals to native Python types
                return convert_decimals(item)
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    @staticmethod
    def update_job_progress(job_id: str, stage: str, percentage: int, action: str, details: Dict[str, Any] = None):
        """Update job progress in DynamoDB."""
        try:
            table = get_jobs_table()
            now = datetime.now(timezone.utc).isoformat()
            
            update_expression = "SET updated_at = :updated_at, processing_details.current_stage = :stage, processing_details.current_action = :action, processing_details.percentage = :percentage"
            expression_values = {
                ':updated_at': now,
                ':stage': stage,
                ':action': action,
                ':percentage': percentage
            }
            
            if details:
                for key, value in details.items():
                    update_expression += f", processing_details.{key} = :{key}"
                    expression_values[f":{key}"] = value
            
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Job {job_id}: {stage} ({percentage}%) - {action}")
        except Exception as e:
            logger.error(f"Failed to update job progress {job_id}: {e}")
    
    @staticmethod
    def add_completed_stage(job_id: str, stage: str, duration_ms: int, details: str):
        """Add a completed stage to the job progress."""
        try:
            table = get_jobs_table()
            now = datetime.now(timezone.utc).isoformat()
            
            stage_info = {
                'stage': stage,
                'completed_at': now,
                'duration_ms': duration_ms,
                'details': details
            }
            
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression="SET processing_details.stages_completed = list_append(if_not_exists(processing_details.stages_completed, :empty_list), :stage_info)",
                ExpressionAttributeValues={
                    ':empty_list': [],
                    ':stage_info': [stage_info]
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to add completed stage for job {job_id}: {e}")
    
    @staticmethod
    def set_job_processing(job_id: str):
        """Mark job as processing."""
        try:
            table = get_jobs_table()
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': JobStatus.PROCESSING,
                    ':updated_at': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to set job processing {job_id}: {e}")
    
    @staticmethod
    def complete_job(job_id: str, result: Dict[str, Any]):
        """Mark job as completed with result."""
        try:
            table = get_jobs_table()
            now = datetime.now(timezone.utc).isoformat()
            
            # DEBUG: Log the result structure before DynamoDB
            logger.info(f"DEBUG: Result structure before DynamoDB save: {json.dumps(result, indent=2, default=str)}")
            logger.info(f"DEBUG: Result type analysis:")
            def analyze_types(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        analyze_types(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        analyze_types(item, f"{path}[{i}]")
                else:
                    logger.info(f"DEBUG:   {path}: {type(obj).__name__} = {obj}")
            
            analyze_types(result)
            
            # Convert all numeric values to Decimal for DynamoDB
            result_for_dynamodb = convert_to_decimals(result)
            logger.info(f"DEBUG: Converted result for DynamoDB storage")
            
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at, #result = :result, processing_details.current_stage = :stage, processing_details.percentage = :percentage",
                ExpressionAttributeNames={
                    '#status': 'status',
                    '#result': 'result'
                },
                ExpressionAttributeValues={
                    ':status': JobStatus.COMPLETED,
                    ':updated_at': now,
                    ':result': result_for_dynamodb,
                    ':stage': 'completed',
                    ':percentage': 100
                }
            )
            
            logger.info(f"Job {job_id} completed")
        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")
    
    @staticmethod
    def fail_job(job_id: str, error: str):
        """Mark job as failed with error."""
        try:
            table = get_jobs_table()
            table.update_item(
                Key={'job_id': job_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at, #error = :error",
                ExpressionAttributeNames={
                    '#status': 'status',
                    '#error': 'error'
                },
                ExpressionAttributeValues={
                    ':status': JobStatus.FAILED,
                    ':updated_at': datetime.now(timezone.utc).isoformat(),
                    ':error': error
                }
            )
            logger.error(f"Job {job_id} failed: {error}")
        except Exception as e:
            logger.error(f"Failed to fail job {job_id}: {e}")