#!/usr/bin/env python3
"""
Test actual SPARQL capabilities of JOLUX endpoint
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import time

sparql = SPARQLWrapper("https://data.legilux.public.lu/sparqlendpoint")
sparql.setReturnFormat(JSON)

def test_query(name, query, expected_results=1):
    """Test a SPARQL query and return results"""
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")
    print(f"Query:\n{query}")
    
    try:
        start_time = time.time()
        sparql.setQuery(query)
        results = sparql.query().convert()
        duration = time.time() - start_time
        
        bindings = results.get('results', {}).get('bindings', [])
        count = len(bindings)
        
        print(f"\n✅ SUCCESS: {count} results in {duration:.2f}s")
        
        # Show first few results
        for i, binding in enumerate(bindings[:3]):
            print(f"  Result {i+1}:")
            for key, value in binding.items():
                val = value.get('value', '')[:80]
                print(f"    {key}: {val}{'...' if len(value.get('value', '')) > 80 else ''}")
        
        return True, count, duration
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, 0, 0

# Test 1: Basic document search
test_query("Basic document search", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?entity ?title WHERE {
    ?entity jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
    FILTER(regex(str(?title), "SARL", "i"))
}
LIMIT 10
""")

# Test 2: Document with JOLUX properties
test_query("Documents with JOLUX properties", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?entity ?title ?typeDoc ?subject WHERE {
    ?entity jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
    OPTIONAL { ?entity jolux:typeDocument ?typeDoc }
    OPTIONAL { ?entity jolux:subjectLevel1 ?subject }
    FILTER(regex(str(?title), "SARL", "i"))
}
LIMIT 5
""")

# Test 3: Citation relationships (jolux:cites)
test_query("Citation relationships", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?doc1 ?title1 ?doc2 ?title2 WHERE {
    ?doc1 jolux:cites ?doc2 .
    ?doc1 jolux:isRealizedBy/jolux:title ?title1 .
    ?doc2 jolux:isRealizedBy/jolux:title ?title2 .
}
LIMIT 10
""")

# Test 4: Amendment relationships (jolux:modifies)
test_query("Amendment relationships", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?modifier ?title1 ?modified ?title2 WHERE {
    ?modifier jolux:modifies ?modified .
    ?modifier jolux:isRealizedBy/jolux:title ?title1 .
    ?modified jolux:isRealizedBy/jolux:title ?title2 .
}
LIMIT 10
""")

# Test 5: Repeal relationships (jolux:repeals)
test_query("Repeal relationships", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?repealer ?title1 ?repealed ?title2 WHERE {
    ?repealer jolux:repeals ?repealed .
    ?repealer jolux:isRealizedBy/jolux:title ?title1 .
    ?repealed jolux:isRealizedBy/jolux:title ?title2 .
}
LIMIT 10
""")

# Test 6: Consolidation relationships (jolux:consolidates)
test_query("Consolidation relationships", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?consolidation ?title1 ?original ?title2 WHERE {
    ?consolidation jolux:consolidates ?original .
    ?consolidation jolux:isRealizedBy/jolux:title ?title1 .
    ?original jolux:isRealizedBy/jolux:title ?title2 .
}
LIMIT 10
""")

# Test 7: Large result set (context concern)
test_query("Large result set test", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?entity ?title ?date WHERE {
    ?entity jolux:dateDocument ?date ;
            jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
}
ORDER BY DESC(?date)
LIMIT 500
""")

# Test 8: Complex multi-property query
test_query("Complex multi-property query", """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?entity ?title ?type ?subject ?date ?authority WHERE {
    ?entity jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
    ?entity jolux:dateDocument ?date .
    OPTIONAL { ?entity jolux:typeDocument ?type }
    OPTIONAL { ?entity jolux:subjectLevel1 ?subject }
    OPTIONAL { ?entity jolux:responsibilityOf ?authority }
    FILTER(regex(str(?title), "loi", "i"))
}
LIMIT 20
""")

print(f"\n{'='*60}")
print("SPARQL CAPABILITY TESTING COMPLETE")
print(f"{'='*60}")