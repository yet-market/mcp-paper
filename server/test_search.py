#!/usr/bin/env python3
"""
Test the simple JOLUX search functionality directly.
"""

from SPARQLWrapper import SPARQLWrapper, JSON

def test_simple_jolux_search():
    """Test the simple working JOLUX search."""
    print("🔍 Testing Simple JOLUX Search")
    print("=" * 50)
    
    sparql = SPARQLWrapper("https://data.legilux.public.lu/sparqlendpoint")
    sparql.setReturnFormat(JSON)
    
    # Test search for SARL using proven query pattern
    keywords = "société"  # Let AI choose appropriate legal terms
    query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?entity ?date ?title ?type WHERE {{
        ?entity jolux:dateDocument ?date ;
                a ?type ;
                jolux:isRealizedBy ?expression .
        ?expression jolux:title ?title .
        FILTER(regex(str(?title), "{keywords}", "i"))
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """
    
    try:
        print(f"🔍 Searching for: '{keywords}'")
        sparql.setQuery(query)
        results = sparql.query().convert()
        
        documents = []
        if 'results' in results and 'bindings' in results['results']:
            for binding in results['results']['bindings']:
                doc = {
                    'uri': binding.get('entity', {}).get('value', ''),
                    'title': binding.get('title', {}).get('value', ''),
                    'date': binding.get('date', {}).get('value', ''),
                    'type': binding.get('type', {}).get('value', ''),
                }
                documents.append(doc)
        
        print(f"✅ Found {len(documents)} documents")
        print("\n📄 Sample Results:")
        for i, doc in enumerate(documents[:3], 1):
            print(f"  {i}. {doc['title'][:80]}...")
            print(f"     Date: {doc['date']}")
            print(f"     Type: {doc['type'].split('#')[-1] if '#' in doc['type'] else doc['type']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_simple_jolux_search()