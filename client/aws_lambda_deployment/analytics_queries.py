#!/usr/bin/env python3
"""
Sample analytics queries for Luxembourg Legal Intelligence request tracking
Demonstrates how to query the comprehensive request data for insights
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Dict, List, Any

class LegalAnalytics:
    """Analytics queries for Luxembourg Legal Intelligence request tracking."""
    
    def __init__(self, region_name='eu-west-2'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.requests_table = self.dynamodb.Table('luxembourg-legal-requests')
    
    def get_company_usage_stats(self, company_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a company."""
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.requests_table.query(
                IndexName='company-date-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('company_id').eq(company_id) & 
                                     boto3.dynamodb.conditions.Key('created_at').between(
                                         start_date.isoformat(), end_date.isoformat()
                                     )
            )
            
            requests = response['Items']
            
            stats = {
                'company_id': company_id,
                'period_days': days,
                'total_requests': len(requests),
                'total_cost_usd': 0.0,
                'total_tokens': 0,
                'average_processing_time': 0.0,
                'tool_usage': {},
                'user_breakdown': {},
                'status_breakdown': {
                    'completed': 0,
                    'failed': 0,
                    'processing': 0
                },
                'response_quality': {
                    'with_citations': 0,
                    'with_legal_sources': 0,
                    'average_response_length': 0
                }
            }
            
            if not requests:
                return stats
            
            total_processing_time = 0
            total_response_length = 0
            
            for request in requests:
                # Cost analysis
                if 'costs' in request and 'total_cost_usd' in request['costs']:
                    stats['total_cost_usd'] += float(request['costs']['total_cost_usd'])
                
                # Token analysis
                if 'tokens' in request and 'total_tokens' in request['tokens']:
                    stats['total_tokens'] += int(request['tokens']['total_tokens'])
                
                # Processing time
                if 'performance_metrics' in request and 'processing_time_seconds' in request['performance_metrics']:
                    total_processing_time += float(request['performance_metrics']['processing_time_seconds'])
                
                # Tool usage
                if 'tools_execution' in request and 'tools_used' in request['tools_execution']:
                    for tool in request['tools_execution']['tools_used']:
                        if tool in stats['tool_usage']:
                            stats['tool_usage'][tool] += 1
                        else:
                            stats['tool_usage'][tool] = 1
                
                # User breakdown
                user_id = request.get('user_id', 'unknown')
                if user_id in stats['user_breakdown']:
                    stats['user_breakdown'][user_id]['requests'] += 1
                    stats['user_breakdown'][user_id]['cost_usd'] += float(request.get('costs', {}).get('total_cost_usd', 0))
                else:
                    stats['user_breakdown'][user_id] = {
                        'requests': 1,
                        'cost_usd': float(request.get('costs', {}).get('total_cost_usd', 0))
                    }
                
                # Status breakdown
                status = request.get('status', 'unknown')
                if status in stats['status_breakdown']:
                    stats['status_breakdown'][status] += 1
                
                # Response quality
                if 'response_metrics' in request:
                    metrics = request['response_metrics']
                    if metrics.get('has_citations', False):
                        stats['response_quality']['with_citations'] += 1
                    if metrics.get('has_legal_sources', False):
                        stats['response_quality']['with_legal_sources'] += 1
                    
                    response_length = int(metrics.get('response_length', 0))
                    total_response_length += response_length
            
            # Calculate averages
            if len(requests) > 0:
                stats['average_processing_time'] = total_processing_time / len(requests)
                stats['response_quality']['average_response_length'] = total_response_length // len(requests)
            
            return stats
            
        except Exception as e:
            print(f"Error getting company stats: {e}")
            return {}
    
    def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive cost analysis across all companies."""
        
        # For a full scan, we'll scan the table (in production, consider using date-based partitioning)
        try:
            response = self.requests_table.scan()
            requests = response['Items']
            
            # Filter by date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            filtered_requests = [
                r for r in requests 
                if start_date.isoformat() <= r.get('created_at', '') <= end_date.isoformat()
            ]
            
            cost_analysis = {
                'period_days': days,
                'total_requests': len(filtered_requests),
                'total_cost_usd': 0.0,
                'total_tokens': 0,
                'cost_by_company': {},
                'cost_by_model': {},
                'average_cost_per_request': 0.0,
                'cost_efficiency': {
                    'cost_per_token': 0.0,
                    'tokens_per_dollar': 0.0
                }
            }
            
            for request in filtered_requests:
                company_id = request.get('company_id', 'unknown')
                model = request.get('model', 'unknown')
                cost = float(request.get('costs', {}).get('total_cost_usd', 0))
                tokens = int(request.get('tokens', {}).get('total_tokens', 0))
                
                cost_analysis['total_cost_usd'] += cost
                cost_analysis['total_tokens'] += tokens
                
                # By company
                if company_id in cost_analysis['cost_by_company']:
                    cost_analysis['cost_by_company'][company_id]['cost_usd'] += cost
                    cost_analysis['cost_by_company'][company_id]['requests'] += 1
                else:
                    cost_analysis['cost_by_company'][company_id] = {
                        'cost_usd': cost,
                        'requests': 1
                    }
                
                # By model
                if model in cost_analysis['cost_by_model']:
                    cost_analysis['cost_by_model'][model]['cost_usd'] += cost
                    cost_analysis['cost_by_model'][model]['requests'] += 1
                else:
                    cost_analysis['cost_by_model'][model] = {
                        'cost_usd': cost,
                        'requests': 1
                    }
            
            # Calculate efficiency metrics
            if len(filtered_requests) > 0:
                cost_analysis['average_cost_per_request'] = cost_analysis['total_cost_usd'] / len(filtered_requests)
            
            if cost_analysis['total_tokens'] > 0:
                cost_analysis['cost_efficiency']['cost_per_token'] = cost_analysis['total_cost_usd'] / cost_analysis['total_tokens']
                cost_analysis['cost_efficiency']['tokens_per_dollar'] = cost_analysis['total_tokens'] / max(cost_analysis['total_cost_usd'], 0.000001)
            
            return cost_analysis
            
        except Exception as e:
            print(f"Error getting cost analysis: {e}")
            return {}
    
    def get_tool_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics on tool usage patterns."""
        
        try:
            # Scan for recent requests
            response = self.requests_table.scan()
            requests = response['Items']
            
            # Filter by date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            filtered_requests = [
                r for r in requests 
                if start_date.isoformat() <= r.get('created_at', '') <= end_date.isoformat()
            ]
            
            tool_analytics = {
                'period_days': days,
                'total_requests': len(filtered_requests),
                'tool_usage_frequency': {},
                'tool_success_rates': {},
                'average_tools_per_request': 0.0,
                'tool_combinations': {},
                'performance_by_tool_count': {}
            }
            
            total_tools_used = 0
            
            for request in filtered_requests:
                tools_used = request.get('tools_execution', {}).get('tools_used', [])
                tool_count = len(tools_used)
                total_tools_used += tool_count
                
                # Tool frequency
                for tool in tools_used:
                    if tool in tool_analytics['tool_usage_frequency']:
                        tool_analytics['tool_usage_frequency'][tool] += 1
                    else:
                        tool_analytics['tool_usage_frequency'][tool] = 1
                
                # Tool combinations
                if tool_count > 1:
                    combination = ', '.join(sorted(tools_used))
                    if combination in tool_analytics['tool_combinations']:
                        tool_analytics['tool_combinations'][combination] += 1
                    else:
                        tool_analytics['tool_combinations'][combination] = 1
                
                # Performance by tool count
                processing_time = float(request.get('performance_metrics', {}).get('processing_time_seconds', 0))
                cost = float(request.get('costs', {}).get('total_cost_usd', 0))
                
                if tool_count not in tool_analytics['performance_by_tool_count']:
                    tool_analytics['performance_by_tool_count'][tool_count] = {
                        'requests': 0,
                        'total_time': 0.0,
                        'total_cost': 0.0
                    }
                
                tool_analytics['performance_by_tool_count'][tool_count]['requests'] += 1
                tool_analytics['performance_by_tool_count'][tool_count]['total_time'] += processing_time
                tool_analytics['performance_by_tool_count'][tool_count]['total_cost'] += cost
            
            # Calculate averages
            if len(filtered_requests) > 0:
                tool_analytics['average_tools_per_request'] = total_tools_used / len(filtered_requests)
            
            # Calculate average time and cost by tool count
            for tool_count, data in tool_analytics['performance_by_tool_count'].items():
                if data['requests'] > 0:
                    data['average_time'] = data['total_time'] / data['requests']
                    data['average_cost'] = data['total_cost'] / data['requests']
            
            return tool_analytics
            
        except Exception as e:
            print(f"Error getting tool analytics: {e}")
            return {}

def main():
    """Example usage of the analytics queries."""
    
    print("📊 Luxembourg Legal Intelligence - Analytics Dashboard")
    print("=" * 60)
    
    analytics = LegalAnalytics()
    
    # Example 1: Company usage stats
    print("\n1. 📈 Company Usage Stats (last 30 days)")
    print("-" * 40)
    company_stats = analytics.get_company_usage_stats("default", 30)
    if company_stats:
        print(f"Company: {company_stats['company_id']}")
        print(f"Total Requests: {company_stats['total_requests']}")
        print(f"Total Cost: ${company_stats['total_cost_usd']:.4f}")
        print(f"Total Tokens: {company_stats['total_tokens']:,}")
        print(f"Avg Processing Time: {company_stats['average_processing_time']:.2f}s")
        print(f"Tool Usage: {company_stats['tool_usage']}")
    
    # Example 2: Cost analysis
    print("\n2. 💰 Cost Analysis (last 30 days)")
    print("-" * 40)
    cost_analysis = analytics.get_cost_analysis(30)
    if cost_analysis:
        print(f"Total Requests: {cost_analysis['total_requests']}")
        print(f"Total Cost: ${cost_analysis['total_cost_usd']:.4f}")
        print(f"Avg Cost/Request: ${cost_analysis['average_cost_per_request']:.4f}")
        print(f"Cost per Token: ${cost_analysis['cost_efficiency']['cost_per_token']:.6f}")
        print(f"Companies: {list(cost_analysis['cost_by_company'].keys())}")
    
    # Example 3: Tool usage analytics
    print("\n3. 🛠️  Tool Usage Analytics (last 30 days)")
    print("-" * 40)
    tool_analytics = analytics.get_tool_usage_analytics(30)
    if tool_analytics:
        print(f"Total Requests: {tool_analytics['total_requests']}")
        print(f"Avg Tools/Request: {tool_analytics['average_tools_per_request']:.2f}")
        print(f"Most Used Tools: {dict(list(sorted(tool_analytics['tool_usage_frequency'].items(), key=lambda x: x[1], reverse=True))[:3])}")
        print(f"Performance by Tool Count: {tool_analytics['performance_by_tool_count']}")

if __name__ == "__main__":
    main()