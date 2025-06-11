#!/usr/bin/env python3
"""
Test the fixed SPARQL queries from tools.py against Luxembourg SPARQL endpoint
"""

import json
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SPARQL endpoint
SPARQL_ENDPOINT = "https://data.legilux.public.lu/sparqlendpoint"

def test_sparql_query(name: str, query: str, timeout: int = 30):
    """Test a SPARQL query and return results."""
    logger.info(f"\n🔍 Testing {name}...")
    try:
        sparql = SPARQLWrapper(SPARQL_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        start_time = time.time()
        results = sparql.query().convert()
        end_time = time.time()

        if 'results' in results and 'bindings' in results['results']:
            bindings = results['results']['bindings']
            logger.info(f"✅ {name}: Found {len(bindings)} results in {end_time - start_time:.2f}s")
            
            # Show first few results
            for i, binding in enumerate(bindings[:3]):
                logger.info(f"   Result {i+1}:")
                for key, value in binding.items():
                    if 'value' in value:
                        display_value = value['value']
                        if len(display_value) > 80:
                            display_value = display_value[:80] + "..."
                        logger.info(f"     {key}: {display_value}")
            
            return {
                "success": True,
                "results": bindings,
                "count": len(bindings),
                "execution_time": end_time - start_time
            }
        else:
            logger.warning(f"❌ {name}: No results returned")
            return {
                "success": False,
                "error": "No results in response",
                "response": results
            }
    except Exception as e:
        logger.error(f"❌ {name}: Query failed - {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Test all fixed SPARQL queries from tools.py."""
    
    # Test document URI for relationship queries
    test_doc_uri = "http://data.legilux.public.lu/eli/etat/leg/loi/1915/08/10/n1/jo"
    
    # 1. Test citations query (fixed BIND syntax)
    citations_query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?neighbor ?title ?date ?type ?direction WHERE {{
      {{
        <{test_doc_uri}> jolux:cites ?neighbor .
        BIND("outbound" AS ?direction)
      }}
      UNION
      {{
        ?neighbor jolux:cites <{test_doc_uri}> .
        BIND("inbound" AS ?direction)
      }}
      ?neighbor jolux:isRealizedBy/jolux:title ?title .
      ?neighbor jolux:dateDocument ?date .
      OPTIONAL {{ ?neighbor jolux:typeDocument ?type }}
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """
    
    # 2. Test amendments query (fixed BIND syntax)
    amendments_query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?neighbor ?title ?date ?type ?direction WHERE {{
      {{ 
        <{test_doc_uri}> jolux:modifies ?neighbor .
        BIND("outgoing" AS ?direction)
      }}
      UNION
      {{ 
        ?neighbor jolux:modifies <{test_doc_uri}> .
        BIND("incoming" AS ?direction)
      }}
      ?neighbor jolux:isRealizedBy/jolux:title ?title .
      ?neighbor jolux:dateDocument ?date .
      OPTIONAL {{ ?neighbor jolux:typeDocument ?type }}
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """
    
    # 3. Test legal status query (fixed BIND syntax)
    legal_status_query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?related ?title ?date ?relType ?entryDate ?expiryDate WHERE {{
      OPTIONAL {{ <{test_doc_uri}> jolux:entryIntoForceDate ?entryDate }}
      OPTIONAL {{ <{test_doc_uri}> jolux:eventEndDate ?expiryDate }}
      {{ 
        <{test_doc_uri}> jolux:repeals ?related .
        BIND("repeals" AS ?relType)
      }}
      UNION
      {{ 
        ?related jolux:repeals <{test_doc_uri}> .
        BIND("repealedBy" AS ?relType)
      }}
      UNION
      {{ 
        <{test_doc_uri}> jolux:consolidates ?related .
        BIND("consolidates" AS ?relType)
      }}
      ?related jolux:isRealizedBy/jolux:title ?title .
      ?related jolux:dateDocument ?date .
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """
    
    # 4. Test relationships query (fixed BIND syntax)
    relationships_query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?neighbor ?title ?date ?type ?relType WHERE {{
      {{ 
        <{test_doc_uri}> jolux:cites ?neighbor .
        BIND("cites" AS ?relType)
      }}
      UNION
      {{ 
        <{test_doc_uri}> jolux:modifies ?neighbor .
        BIND("modifies" AS ?relType)
      }}
      UNION
      {{ 
        <{test_doc_uri}> jolux:repeals ?neighbor .
        BIND("repeals" AS ?relType)
      }}
      UNION
      {{ 
        <{test_doc_uri}> jolux:basedOn ?neighbor .
        BIND("basedOn" AS ?relType)
      }}
      UNION
      {{ 
        ?neighbor jolux:basedOn <{test_doc_uri}> .
        BIND("implements" AS ?relType)
      }}
      ?neighbor jolux:isRealizedBy/jolux:title ?title .
      ?neighbor jolux:dateDocument ?date .
      OPTIONAL {{ ?neighbor jolux:typeDocument ?type }}
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """
    
    # 5. Test foundation discovery citation analysis (already working)
    foundation_citation_query = """
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
        ?citing_doc jolux:cites ?cited_doc .
        ?cited_doc jolux:isRealizedBy ?expr .
        ?expr jolux:title ?title .
        ?cited_doc jolux:dateDocument ?date .
        FILTER(CONTAINS(LCASE(?title), "société"))
    }
    GROUP BY ?cited_doc ?title ?date
    ORDER BY DESC(?citation_count)
    LIMIT 5
    """
    
    # 6. Test basic document search (content extraction fallback)
    basic_search_query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?title ?date ?type WHERE {{
        <{test_doc_uri}> jolux:isRealizedBy/jolux:title ?title .
        <{test_doc_uri}> jolux:dateDocument ?date .
        OPTIONAL {{ <{test_doc_uri}> jolux:typeDocument ?type }}
    }}
    """
    
    # 7. Test simple document search (without full-text for now)
    simple_search_query = """
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    SELECT ?entity ?title ?date ?type ?subject ?authority WHERE {
        ?entity jolux:isRealizedBy ?expression .
        ?expression jolux:title ?title .
        ?entity jolux:dateDocument ?date .
        OPTIONAL { ?entity jolux:typeDocument ?type }
        OPTIONAL { ?entity jolux:subjectLevel1 ?subject }
        OPTIONAL { ?entity jolux:responsibilityOf ?authority }
        FILTER(regex(str(?title), "société", "i"))
    }
    ORDER BY DESC(?date)
    LIMIT 5
    """
    
    queries_to_test = [
        ("Citations Query (Fixed BIND)", citations_query),
        ("Amendments Query (Fixed BIND)", amendments_query), 
        ("Legal Status Query (Fixed BIND)", legal_status_query),
        ("Relationships Query (Fixed BIND)", relationships_query),
        ("Foundation Citation Analysis", foundation_citation_query),
        ("Basic Document Search", basic_search_query),
        ("Simple Document Search", simple_search_query),
    ]
    
    results = {}
    
    logger.info("🚀 TESTING FIXED SPARQL QUERIES FROM TOOLS.PY")
    logger.info("=" * 80)
    logger.info(f"📍 Test document URI: {test_doc_uri}")
    logger.info(f"🎯 Testing {len(queries_to_test)} queries...")
    
    for name, query in queries_to_test:
        results[name] = test_sparql_query(name, query)
        time.sleep(1)  # Rate limiting
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 SPARQL QUERY TEST RESULTS SUMMARY:")
    logger.info("=" * 80)
    
    success_count = 0
    for name, result in results.items():
        if result["success"]:
            success_count += 1
            logger.info(f"✅ {name}: {result['count']} results ({result['execution_time']:.2f}s)")
        else:
            logger.info(f"❌ {name}: Failed - {result['error']}")
    
    logger.info(f"\n🎯 OVERALL RESULTS: {success_count}/{len(queries_to_test)} queries working")
    
    if success_count == len(queries_to_test):
        logger.info("🎉 ALL SPARQL QUERIES ARE WORKING CORRECTLY!")
    else:
        logger.info("⚠️  Some queries need further debugging")
    
    # Save detailed results
    with open('sparql_query_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("\n💾 Detailed results saved to sparql_query_test_results.json")

if __name__ == "__main__":
    main()