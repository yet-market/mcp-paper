#!/usr/bin/env python3
"""
Interactive Luxembourg Legal Assistant Client
Real-time question processing with live progress monitoring
"""

import requests
import json
import time
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

class LegalAssistantClient:
    def __init__(self, api_url: str, api_key: str):
        """Initialize the client with API credentials."""
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def ask_question(self, question: str, provider: str = "anthropic", company_id: str = "default", user_id: str = "default") -> Dict[str, Any]:
        """Submit a question and get job ID."""
        print(f"🚀 Submitting question to {provider.upper()} provider...")
        print(f"📝 Question: {question}")
        print("-" * 80)
        
        payload = {
            "message": question,
            "provider": provider,
            "company_id": company_id,
            "user_id": user_id
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 202:
                result = response.json()
                print(f"✅ Job created successfully!")
                print(f"🆔 Job ID: {result['job_id']}")
                print(f"🤖 Provider: {result['processing_info']['provider']}")
                print(f"🧠 Model: {result['processing_info']['model']}")
                print(f"⏱️  Estimated time: {result['processing_info']['estimated_time']}")
                print(f"📊 Structured output: {result['processing_info']['structured_output']}")
                print("-" * 80)
                return result
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {}
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current job status."""
        try:
            response = requests.get(
                f"{self.api_url}/job/{job_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {}
    
    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get final job result."""
        try:
            response = requests.get(
                f"{self.api_url}/job/{job_id}/result",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Result fetch failed: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Result fetch error: {e}")
            return {}
    
    def monitor_progress(self, job_id: str, max_wait_minutes: int = 10) -> Optional[Dict[str, Any]]:
        """Monitor job progress with real-time updates."""
        print("📡 Monitoring job progress...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        last_percentage = -1
        last_stage = ""
        
        while time.time() - start_time < max_wait_seconds:
            status = self.get_job_status(job_id)
            
            if not status:
                time.sleep(2)
                continue
            
            current_status = status.get('status', 'unknown')
            processing_details = status.get('processing_details', {})
            percentage = processing_details.get('percentage', 0)
            current_stage = processing_details.get('current_stage', 'unknown')
            current_action = processing_details.get('current_action', 'Processing...')
            
            # Show progress updates
            if percentage != last_percentage or current_stage != last_stage:
                timestamp = datetime.now().strftime("%H:%M:%S")
                progress_bar = self._create_progress_bar(percentage)
                
                print(f"[{timestamp}] {progress_bar} {percentage}% - {current_stage}")
                print(f"           📋 {current_action}")
                
                # Show detailed progress info
                if 'tools_progress' in processing_details:
                    tools_info = processing_details['tools_progress']
                    if 'current_iteration' in tools_info:
                        iteration = tools_info['current_iteration']
                        tools_completed = tools_info.get('tools_executed', 0)
                        print(f"           🔧 Iteration {iteration}, Tools: {tools_completed}")
                
                if 'ai_interaction' in processing_details:
                    ai_info = processing_details['ai_interaction']
                    model_calls = ai_info.get('model_calls', 0)
                    tokens_used = ai_info.get('tokens_used', 0)
                    if model_calls > 0:
                        print(f"           🤖 AI calls: {model_calls}, Tokens: {tokens_used}")
                
                last_percentage = percentage
                last_stage = current_stage
                print()
            
            # Check if completed
            if current_status == 'completed':
                print("🎉 Job completed successfully!")
                return self.get_job_result(job_id)
            elif current_status == 'failed':
                print("❌ Job failed!")
                return status
            
            time.sleep(3)  # Check every 3 seconds
        
        print(f"⏰ Timeout after {max_wait_minutes} minutes")
        return None
    
    def _create_progress_bar(self, percentage: int, width: int = 20) -> str:
        """Create a visual progress bar."""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def display_result(self, result: Dict[str, Any]):
        """Display the final result in a formatted way."""
        if not result:
            print("❌ No result to display")
            return
        
        print("=" * 80)
        print("📋 LUXEMBOURG LEGAL ANALYSIS RESULT")
        print("=" * 80)
        
        # Performance metrics
        if 'performance' in result:
            perf = result['performance']
            processing_time = perf.get('processing_time_seconds', 0)
            tools_executed = perf.get('mcp_tools_executed', 0)
            iterations = perf.get('iterations', 0)
            
            print(f"⚡ Performance:")
            print(f"   Processing time: {processing_time:.2f} seconds")
            print(f"   MCP tools executed: {tools_executed}")
            print(f"   AI iterations: {iterations}")
            print()
        
        # Model information
        if 'model_info' in result:
            model = result['model_info']
            print(f"🤖 Model Information:")
            print(f"   Provider: {model.get('provider', 'unknown')}")
            print(f"   Model: {model.get('model_name', 'unknown')}")
            print(f"   Temperature: {model.get('temperature', 'unknown')}")
            print(f"   Structured output: {model.get('structured_output', 'unknown')}")
            print()
        
        # Legal analysis
        if 'legal_analysis' in result:
            analysis = result['legal_analysis']
            
            # Answer section
            if 'answer' in analysis:
                answer = analysis['answer']
                print("📖 LEGAL ANALYSIS:")
                print("-" * 40)
                
                if 'summary' in answer:
                    print(f"📝 Summary: {answer['summary']}")
                    print()
                
                if 'key_points' in answer and answer['key_points']:
                    print("🔑 Key Points:")
                    for i, point in enumerate(answer['key_points'], 1):
                        print(f"   {i}. {point}")
                    print()
                
                if 'practical_guidance' in answer:
                    print(f"💡 Practical Guidance: {answer['practical_guidance']}")
                    print()
                
                if 'exhaustive_content' in answer:
                    content = answer['exhaustive_content']
                    if len(content) > 500:
                        print("📄 Detailed Analysis (first 500 chars):")
                        print(content[:500] + "...")
                    else:
                        print("📄 Detailed Analysis:")
                        print(content)
                    print()
            
            # Sources section
            if 'reference_sources' in analysis:
                sources = analysis['reference_sources']
                total_sources = sources.get('total_sources', 0)
                print(f"📚 LEGAL SOURCES ({total_sources} total):")
                print("-" * 40)
                
                if 'primary_laws' in sources and sources['primary_laws']:
                    print("📜 Primary Laws:")
                    for law in sources['primary_laws'][:3]:  # Show first 3
                        print(f"   • {law}")
                    print()
                
                if 'supporting_regulations' in sources and sources['supporting_regulations']:
                    print("📋 Supporting Regulations:")
                    for reg in sources['supporting_regulations'][:3]:  # Show first 3
                        print(f"   • {reg}")
                    print()
            
            # Citations network
            if 'citations_network' in analysis:
                citations = analysis['citations_network']
                total_citations = citations.get('total_citations', 0)
                network_strength = citations.get('network_strength', 'unknown')
                
                print(f"🔗 CITATIONS NETWORK:")
                print(f"   Total citations: {total_citations}")
                print(f"   Network strength: {network_strength}")
                print()
            
            # Legal validity
            if 'validite_legale' in analysis:
                validity = analysis['validite_legale']
                overall_status = validity.get('overall_status', 'unknown')
                confidence = validity.get('confidence_level', 'unknown')
                
                print(f"⚖️  LEGAL VALIDITY:")
                print(f"   Overall status: {overall_status}")
                print(f"   Confidence level: {confidence}")
                print()
        
        print("=" * 80)

def main():
    """Main interactive function."""
    parser = argparse.ArgumentParser(description='Luxembourg Legal Assistant Interactive Client')
    parser.add_argument('--api-url', default='https://ymtocda5s2.execute-api.eu-west-2.amazonaws.com/prod',
                       help='API Gateway URL')
    parser.add_argument('--api-key', default='o7tKNwreM48ojccC4ck6j5ZtIhWiNVFj7ffrGuMw',
                       help='API Key')
    parser.add_argument('--provider', choices=['anthropic', 'openai', 'groq'], default='anthropic',
                       help='AI provider to use')
    parser.add_argument('--question', help='Question to ask (if not provided, will prompt)')
    parser.add_argument('--company-id', default='default', help='Company ID')
    parser.add_argument('--user-id', default='default', help='User ID')
    parser.add_argument('--max-wait', type=int, default=10, help='Maximum wait time in minutes')
    
    args = parser.parse_args()
    
    # Initialize client
    client = LegalAssistantClient(args.api_url, args.api_key)
    
    print("🏛️  LUXEMBOURG LEGAL ASSISTANT - INTERACTIVE CLIENT")
    print("=" * 80)
    
    # Get question
    if args.question:
        question = args.question
    else:
        print("Please enter your legal question:")
        question = input("❓ Question: ").strip()
        
        if not question:
            print("❌ No question provided. Exiting.")
            sys.exit(1)
    
    print()
    
    # Submit question
    job_info = client.ask_question(question, args.provider, args.company_id, args.user_id)
    
    if not job_info:
        print("❌ Failed to submit question. Exiting.")
        sys.exit(1)
    
    job_id = job_info.get('job_id')
    if not job_id:
        print("❌ No job ID received. Exiting.")
        sys.exit(1)
    
    # Monitor progress and get result
    result = client.monitor_progress(job_id, args.max_wait)
    
    if result:
        print()
        client.display_result(result)
    else:
        print("❌ Failed to get result within timeout period.")
        print(f"🔗 You can check manually at: {args.api_url}/job/{job_id}/result")

if __name__ == "__main__":
    main()