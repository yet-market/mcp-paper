#!/usr/bin/env python3
"""
AWS Lambda Function for Luxembourg Legal Intelligence MCP Server
Configurable multi-model support with AWS Bedrock
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError
import time
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global variables for Lambda reuse
bedrock_client = None
legal_client = None


class MultiModelLegalClient:
    """Luxembourg Legal client for AWS Lambda with configurable model support."""
    
    def __init__(self):
        self.region = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "eu-west-2"))
        self.mcp_server_url = os.environ.get("MCP_SERVER_URL", "https://yet-mcp-legilux.site")
        
        # Configurable model - default to Claude 3.5 Sonnet
        self.model_id = os.environ.get("MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.model_provider = self._get_model_provider(self.model_id)
        
        # Initialize Bedrock client using IAM role (no credentials needed)
        global bedrock_client
        if not bedrock_client:
            bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region
            )
        self.bedrock = bedrock_client
        
        # Tool discovery cache
        self.available_tools = []
        self._tools_discovered = False
        
        # Cost tracking
        self.query_count = 0
        
        logger.info(f"🤖 Initialized with model: {self.model_id} ({self.model_provider})")
    
    def _get_model_provider(self, model_id: str) -> str:
        """Determine the model provider from model ID."""
        if "anthropic" in model_id:
            return "anthropic"
        elif "mistral" in model_id:
            return "mistral"
        elif "meta" in model_id or "llama" in model_id:
            return "meta"
        elif "cohere" in model_id:
            return "cohere"
        elif "amazon" in model_id:
            return "amazon"
        else:
            return "unknown"
    
    async def discover_tools(self) -> List[str]:
        """Discover available MCP tools."""
        if self._tools_discovered:
            return self.available_tools
        
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            async with Client(transport) as client:
                tools = await client.list_tools()
                self.available_tools = [tool.name for tool in tools]
                self._tools_discovered = True
                
                logger.info(f"🔧 Discovered {len(self.available_tools)} MCP tools")
                return self.available_tools
                
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            return []
    
    def _should_use_legal_search(self, message: str) -> bool:
        """Determine if a message should trigger legal document search."""
        legal_indicators = [
            "sarl", "société", "entreprise", "capital", "taxe", "impôt", "tva",
            "travailleur", "employé", "droit", "loi", "règlement", "luxembourg",
            "juridique", "légal", "créer", "création", "obligation", "fiscal",
            "environnement", "écologie", "commercial", "contrat", "juridique"
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in legal_indicators)
    
    def _extract_legal_keywords(self, message: str) -> str:
        """Extract relevant legal keywords using enhanced domain detection."""
        message_lower = message.lower()
        
        # Company formation domain
        if any(word in message_lower for word in ["sarl", "société", "entreprise", "création", "constituer"]):
            return "SARL|société|création"
        
        # Tax compliance domain
        elif any(word in message_lower for word in ["taxe", "impôt", "fiscal", "tva", "contribution"]):
            return "taxe|impôt|fiscal"
        
        # Employment law domain
        elif any(word in message_lower for word in ["travail", "employé", "salarié", "contrat"]):
            return "travail|employé|salarié"
        
        # Environmental law domain
        elif any(word in message_lower for word in ["environnement", "écologie", "pollution"]):
            return "environnement|écologie"
        
        # Administrative law domain
        elif any(word in message_lower for word in ["administration", "procédure", "formalité"]):
            return "administration|procédure"
        
        # Default general legal
        else:
            return "droit|luxembourg"
    
    async def _call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool using proper FastMCP client."""
        try:
            transport = StreamableHttpTransport(url=self.mcp_server_url)
            
            async with Client(transport) as client:
                result = await client.call_tool(tool_name, parameters)
                
                return {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name,
                    "parameters": parameters
                }
                    
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "parameters": parameters
            }
    
    def _format_tool_result(self, tool_result: Dict[str, Any]) -> str:
        """Format tool execution result."""
        if not tool_result["success"]:
            return f"Erreur lors de la recherche: {tool_result['error']}"
        
        result = tool_result["result"]
        
        # Handle MCP TextContent objects and other complex types
        if hasattr(result, 'text'):
            return result.text
        elif hasattr(result, 'content'):
            # Handle list of content objects
            if isinstance(result.content, list):
                return "\n".join([
                    content.text if hasattr(content, 'text') 
                    else str(content) for content in result.content
                ])
            else:
                return str(result.content)
        elif isinstance(result, dict) and "content" in result:
            return result["content"]
        elif isinstance(result, str):
            return result
        else:
            # Safely convert to string for JSON serialization
            try:
                return json.dumps(result, ensure_ascii=False, default=str)
            except (TypeError, AttributeError):
                return str(result)
    
    def _format_request_for_model(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Format request based on model provider."""
        
        if self.model_provider == "anthropic":
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1200,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.6,
                "top_p": 0.9
            }
        
        elif self.model_provider == "mistral":
            prompt = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"
            return {
                "prompt": prompt,
                "max_tokens": 1200,
                "temperature": 0.6,
                "top_p": 0.9,
                "stop": ["</s>"]
            }
        
        elif self.model_provider == "meta":  # Llama
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
            return {
                "prompt": prompt,
                "max_gen_len": 1200,
                "temperature": 0.6,
                "top_p": 0.9
            }
        
        elif self.model_provider == "cohere":
            return {
                "message": user_prompt,
                "chat_history": [
                    {
                        "role": "SYSTEM",
                        "message": system_prompt
                    }
                ],
                "max_tokens": 1200,
                "temperature": 0.6,
                "p": 0.9
            }
        
        elif self.model_provider == "amazon":  # Titan
            prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1200,
                    "temperature": 0.6,
                    "topP": 0.9,
                    "stopSequences": []
                }
            }
        
        else:
            # Default to Anthropic format for unknown providers
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1200,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.6,
                "top_p": 0.9
            }
    
    def _extract_response_from_model(self, response_body: Dict[str, Any]) -> str:
        """Extract response text based on model provider."""
        
        if self.model_provider == "anthropic":
            if "content" in response_body and response_body["content"]:
                return response_body["content"][0].get("text", "")
        
        elif self.model_provider == "mistral":
            if "outputs" in response_body and response_body["outputs"]:
                return response_body["outputs"][0].get("text", "")
        
        elif self.model_provider == "meta":  # Llama
            return response_body.get("generation", "")
        
        elif self.model_provider == "cohere":
            return response_body.get("text", "")
        
        elif self.model_provider == "amazon":  # Titan
            if "results" in response_body and response_body["results"]:
                return response_body["results"][0].get("outputText", "")
        
        # Fallback: try common fields
        for field in ["text", "response", "content", "output", "message"]:
            if field in response_body:
                value = response_body[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, list) and value:
                    return str(value[0])
        
        return "Désolé, je n'ai pas pu générer une réponse."
    
    async def search_legal_documents(self, message: str) -> Dict[str, Any]:
        """Search legal documents using available MCP tools."""
        tools_used = []
        tool_results = []
        keywords = self._extract_legal_keywords(message)
        
        logger.info(f"🔍 Searching legal documents with keywords: '{keywords}'")
        
        try:
            # Try enhanced search first, fallback to basic search
            if "search_documents_with_full_metadata" in self.available_tools:
                search_result = await self._call_mcp_tool(
                    "search_documents_with_full_metadata",
                    {
                        "keywords": keywords,
                        "search_fields": ["title", "subject1", "subject2"],
                        "limit": 10
                    }
                )
                tools_used.append("search_documents_with_full_metadata")
            elif "search_luxembourg_documents" in self.available_tools:
                search_result = await self._call_mcp_tool(
                    "search_luxembourg_documents",
                    {
                        "keywords": keywords,
                        "limit": 5,
                        "include_content": True,
                        "comprehensive_search": True
                    }
                )
                tools_used.append("search_luxembourg_documents")
            else:
                # Basic query fallback
                search_result = await self._call_mcp_tool(
                    "query",
                    {"sparql_query": f"SELECT * WHERE {{ ?s ?p ?o . FILTER(CONTAINS(LCASE(?o), '{keywords.lower()}')) }} LIMIT 5"}
                )
                tools_used.append("query")
            
            tool_results.append(search_result)
            
            formatted_result = self._format_tool_result(search_result)
            
            return {
                "search_context": formatted_result,
                "tools_used": tools_used,
                "tool_results": tool_results,
                "workflow": "legal_search_complete"
            }
            
        except Exception as e:
            logger.error(f"Legal search failed: {e}")
            return {
                "search_context": f"Erreur lors de la recherche: {str(e)}",
                "tools_used": tools_used,
                "tool_results": tool_results,
                "workflow": "search_error"
            }
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Main chat interface with configurable model support."""
        self.query_count += 1
        start_time = time.time()
        
        try:
            # Discover available tools
            await self.discover_tools()
            
            # Check if we should search legal documents
            should_search = self._should_use_legal_search(message)
            
            if should_search:
                search_data = await self.search_legal_documents(message)
                search_context = search_data["search_context"]
                tools_used = search_data["tools_used"]
                tool_results = search_data["tool_results"]
                workflow = search_data["workflow"]
            else:
                search_context = ""
                tools_used = []
                tool_results = []
                workflow = "no_search_needed"
            
            # Generate AI response with the configured model
            system_prompt = """Vous êtes un assistant juridique spécialisé dans le droit luxembourgeois. 
Répondez toujours en français avec une analyse précise et structurée."""
            
            if search_context:
                user_prompt = f"""Question: {message}

Documents légaux luxembourgeois analysés:
{search_context}

Répondez à la question en vous basant sur ces documents légaux officiels luxembourgeois. 
Structurez votre réponse de manière claire et mentionnez les sources pertinentes."""
            else:
                user_prompt = message
            
            # Format request for the specific model
            request_body = self._format_request_for_model(system_prompt, user_prompt)
            
            # Call Bedrock with the configured model
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract response based on model provider
            ai_response = self._extract_response_from_model(response_body)
            
            # Calculate cost and timing
            processing_time = time.time() - start_time
            estimated_tokens = len(json.dumps(request_body)) // 4 + len(ai_response) // 4
            estimated_cost = self._estimate_cost(estimated_tokens)
            
            return {
                "response": ai_response,
                "tools_used": tools_used,
                "tool_results": tool_results,
                "workflow": workflow,
                "cost_info": {
                    "estimated_cost_usd": round(estimated_cost, 6),
                    "estimated_tokens": estimated_tokens,
                    "processing_time_ms": round(processing_time * 1000, 2)
                },
                "model": {
                    "id": self.model_id,
                    "provider": self.model_provider
                },
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "response": f"Erreur: {str(e)}",
                "tools_used": [],
                "tool_results": [],
                "workflow": "error",
                "error": str(e),
                "model": {
                    "id": self.model_id,
                    "provider": self.model_provider
                }
            }
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on model provider and tokens."""
        # Rough estimates for different model providers (per 1M tokens)
        pricing = {
            "anthropic": {"input": 3.0, "output": 15.0},
            "mistral": {"input": 0.15, "output": 0.6},
            "meta": {"input": 0.65, "output": 0.8},
            "cohere": {"input": 1.0, "output": 2.0},
            "amazon": {"input": 0.5, "output": 1.5}
        }
        
        provider_pricing = pricing.get(self.model_provider, {"input": 1.0, "output": 3.0})
        input_cost = (tokens * 0.7 / 1_000_000) * provider_pricing["input"]
        output_cost = (tokens * 0.3 / 1_000_000) * provider_pricing["output"]
        
        return input_cost + output_cost


# Lambda handler functions
def lambda_handler(event, context):
    """Main Lambda handler for API Gateway integration."""
    global legal_client
    
    try:
        # Initialize client on first run
        if not legal_client:
            legal_client = MultiModelLegalClient()
        
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
        elif path == "/search" and http_method == "POST":
            return handle_search(request_data)
        elif path == "/tools" and http_method == "GET":
            return handle_tools()
        elif path == "/health" and http_method == "GET":
            return handle_health()
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
    """Handle /chat endpoint."""
    try:
        message = request_data.get("message", "").strip()
        if not message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Message is required"})
            }
        
        # Run async chat
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(legal_client.chat(message))
        loop.close()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-API-Key"
            },
            "body": json.dumps(result, ensure_ascii=False, default=str)
        }
        
    except Exception as e:
        logger.error(f"Chat handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_search(request_data: Dict[str, Any]):
    """Handle /search endpoint."""
    try:
        keywords = request_data.get("keywords", "").strip()
        if not keywords:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Keywords are required"})
            }
        
        # Direct search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Discover tools first
        loop.run_until_complete(legal_client.discover_tools())
        
        # Use best available tool
        if "search_documents_with_full_metadata" in legal_client.available_tools:
            tool_name = "search_documents_with_full_metadata"
            tool_params = {
                "keywords": keywords,
                "search_fields": ["title", "subject1"],
                "limit": request_data.get("limit", 10)
            }
        elif "search_luxembourg_documents" in legal_client.available_tools:
            tool_name = "search_luxembourg_documents"
            tool_params = {
                "keywords": keywords,
                "limit": request_data.get("limit", 5),
                "include_content": request_data.get("include_content", True),
                "comprehensive_search": request_data.get("comprehensive_search", False)
            }
        else:
            tool_name = "query"
            tool_params = {"sparql_query": f"SELECT * WHERE {{ ?s ?p ?o . FILTER(CONTAINS(LCASE(?o), '{keywords.lower()}')) }} LIMIT 5"}
        
        tool_result = loop.run_until_complete(
            legal_client._call_mcp_tool(tool_name, tool_params)
        )
        loop.close()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-API-Key"
            },
            "body": json.dumps(tool_result, ensure_ascii=False, default=str)
        }
        
    except Exception as e:
        logger.error(f"Search handler error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


def handle_tools():
    """Handle /tools endpoint."""
    try:
        # Run async tool discovery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tools = loop.run_until_complete(legal_client.discover_tools())
        loop.close()
        
        tools_info = {
            "total_tools": len(tools),
            "available_tools": tools,
            "model": {
                "id": legal_client.model_id,
                "provider": legal_client.model_provider
            },
            "mcp_server": legal_client.mcp_server_url,
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
            "model": {
                "id": legal_client.model_id if legal_client else os.environ.get("MODEL_ID", "not-configured"),
                "provider": legal_client.model_provider if legal_client else "unknown"
            },
            "region": os.environ.get("BEDROCK_REGION", "eu-west-2"),
            "mcp_server": os.environ.get("MCP_SERVER_URL", "not-configured"),
            "supported_models": {
                "anthropic": ["anthropic.claude-3-5-sonnet-20241022-v2:0", "anthropic.claude-3-haiku-20240307-v1:0"],
                "mistral": ["mistral.mistral-7b-instruct-v0:2", "mistral.mixtral-8x7b-instruct-v0:1"],
                "meta": ["meta.llama3-70b-instruct-v1:0", "meta.llama3-8b-instruct-v1:0"],
                "cohere": ["cohere.command-r-plus-v1:0", "cohere.command-r-v1:0"],
                "amazon": ["amazon.titan-text-premier-v1:0", "amazon.titan-text-express-v1"]
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