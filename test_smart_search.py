#!/usr/bin/env python3
"""
Test the new smart keyword search functionality
"""

import sys
sys.path.append('server')

from luxembourg_legal_server.search import LuxembourgSearch

def test_smart_search():
    """Test the new smart keyword search vs old search"""
    
    endpoint = "https://data.legilux.public.lu/sparqlendpoint"
    search_engine = LuxembourgSearch(endpoint)
    
    print("🧪 TESTING SMART SEARCH vs OLD SEARCH")
    print("="*60)
    
    # Test cases - AI should choose appropriate keywords for each scenario
    test_cases = [
        "société responsabilité",  # Test multi-word legal terms
        "créer entreprise Luxembourg",  # Test business context
        "obligations fiscales Luxembourg",  # Test tax context  
        "travail",  # Test single precise keyword
    ]
    
    for keywords in test_cases:
        print(f"\n📝 Testing: '{keywords}'")
        print("-" * 40)
        
        # Test old simple search
        try:
            old_result = search_engine.simple_title_search(keywords, limit=5)
            old_count = old_result["total_found"]
            print(f"   🔍 Old simple search: {old_count} documents")
        except Exception as e:
            print(f"   🔍 Old simple search: ERROR - {e}")
            old_count = 0
        
        # Test new smart search
        try:
            smart_result = search_engine.smart_keyword_search(keywords, limit=5)
            if smart_result["query_successful"]:
                smart_count = smart_result["total_found"]
                keywords_used = smart_result.get("keywords_used", [])
                print(f"   🧠 Smart search: {smart_count} documents")
                print(f"      Keywords extracted: {keywords_used}")
                if smart_count > 0:
                    # Show top result with relevance
                    top_doc = smart_result["documents"][0]
                    relevance = top_doc.get("relevance_score", 0)
                    title_preview = top_doc["title"][:60]
                    print(f"      Top result ({relevance:.2f}): {title_preview}...")
            else:
                print(f"   🧠 Smart search: ERROR - {smart_result.get('error', 'Unknown')}")
                smart_count = 0
        except Exception as e:
            print(f"   🧠 Smart search: ERROR - {e}")
            smart_count = 0
        
        # Compare
        if smart_count > old_count:
            print(f"   ✅ IMPROVEMENT: +{smart_count - old_count} more documents")
        elif smart_count == old_count and old_count > 0:
            print(f"   ≈ SAME: Both found {smart_count} documents")
        elif old_count == 0 and smart_count == 0:
            print(f"   ❌ BOTH FAILED: No documents found")
        else:
            print(f"   ⚠️ REGRESSION: {old_count} → {smart_count}")

if __name__ == "__main__":
    test_smart_search()