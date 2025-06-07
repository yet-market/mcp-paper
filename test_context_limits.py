#!/usr/bin/env python3
"""
Test context limits for MCP responses
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import json

sparql = SPARQLWrapper("https://data.legilux.public.lu/sparqlendpoint")
sparql.setReturnFormat(JSON)

def test_result_sizes():
    """Test different result set sizes and their JSON output sizes"""
    
    for limit in [10, 50, 100, 200, 500]:
        query = f"""
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        SELECT ?entity ?title ?date ?type ?subject WHERE {{
            ?entity jolux:dateDocument ?date ;
                    jolux:isRealizedBy ?expression .
            ?expression jolux:title ?title .
            OPTIONAL {{ ?entity jolux:typeDocument ?type }}
            OPTIONAL {{ ?entity jolux:subjectLevel1 ?subject }}
        }}
        ORDER BY DESC(?date)
        LIMIT {limit}
        """
        
        try:
            sparql.setQuery(query)
            results = sparql.query().convert()
            
            # Convert to JSON and measure size
            json_str = json.dumps(results, ensure_ascii=False)
            size_bytes = len(json_str.encode('utf-8'))
            size_kb = size_bytes / 1024
            
            bindings = results.get('results', {}).get('bindings', [])
            
            print(f"LIMIT {limit:3d}: {len(bindings):3d} results, {size_kb:6.1f} KB")
            
            # Estimate typical MCP response size
            if bindings:
                avg_title_length = sum(len(b.get('title', {}).get('value', '')) for b in bindings) / len(bindings)
                print(f"           Average title length: {avg_title_length:.0f} chars")
            
        except Exception as e:
            print(f"LIMIT {limit:3d}: ERROR - {str(e)}")

def test_citation_response_size():
    """Test citation response size"""
    
    # Get a document with citations
    query_doc = """
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?doc WHERE {
        ?doc jolux:cites ?other .
    }
    LIMIT 1
    """
    
    sparql.setQuery(query_doc)
    doc_result = sparql.query().convert()
    
    if doc_result.get('results', {}).get('bindings'):
        doc_uri = doc_result['results']['bindings'][0]['doc']['value']
        
        # Test citation query size
        citation_query = f"""
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        SELECT ?cited ?title ?date WHERE {{
            <{doc_uri}> jolux:cites ?cited .
            ?cited jolux:isRealizedBy/jolux:title ?title .
            ?cited jolux:dateDocument ?date .
        }}
        """
        
        sparql.setQuery(citation_query)
        citation_results = sparql.query().convert()
        
        json_str = json.dumps(citation_results, ensure_ascii=False)
        size_kb = len(json_str.encode('utf-8')) / 1024
        count = len(citation_results.get('results', {}).get('bindings', []))
        
        print(f"\nCitation query: {count} citations, {size_kb:.1f} KB")

print("TESTING MCP RESPONSE SIZES")
print("=" * 50)
test_result_sizes()
test_citation_response_size()

print(f"\n{'='*50}")
print("CONTEXT ANALYSIS:")
print("- Claude context limit: ~200K tokens")
print("- 1 token ≈ 4 chars, so ~800KB text limit")
print("- MCP responses should stay under 100KB for safety")
print("- Limit queries to 50-100 results max")
print("="*50)