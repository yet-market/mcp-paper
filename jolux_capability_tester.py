#!/usr/bin/env python3
"""
JOLUX SPARQL Endpoint Capability Tester
Tests real capabilities vs assumptions for treaty, EU directive, and legislative features.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import quote


class JOLUXTester:
    def __init__(self):
        self.endpoint = "https://data.legilux.public.lu/sparqlendpoint"
        self.headers = {
            'Accept': 'application/sparql-results+json',
            'User-Agent': 'JOLUX-Capability-Tester/1.0'
        }
        self.results = {}
        
    def execute_query(self, query: str, description: str = "") -> Optional[Dict]:
        """Execute SPARQL query and return results"""
        try:
            print(f"\n🔍 Testing: {description}")
            print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
            
            params = {'query': query}
            response = requests.get(self.endpoint, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('results', {}).get('bindings', []))
                print(f"✅ Success: {count} results")
                return data
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_treaty_capabilities(self):
        """Test treaty-related queries"""
        print("\n" + "="*60)
        print("TESTING TREATY CAPABILITIES")
        print("="*60)
        
        tests = [
            # Test for treaty classes
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  ?instance rdf:type ?class .
                  FILTER(CONTAINS(LCASE(STR(?class)), "treaty"))
                }
                GROUP BY ?class
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for treaty-related classes'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  VALUES ?class { jolux:TreatyProcess jolux:TreatyDocument jolux:TreatyRatification }
                  ?instance rdf:type ?class .
                }
                GROUP BY ?class
                ''',
                'description': 'Test specific treaty classes (TreatyProcess, TreatyDocument, TreatyRatification)'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?usage_count)
                WHERE {
                  ?s jolux:transposes ?o .
                }
                GROUP BY ?property
                ''',
                'description': 'Test jolux:transposes property usage'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT ?doc ?title ?type
                WHERE {
                  ?doc rdf:type ?type .
                  ?doc eli:title ?title .
                  FILTER(CONTAINS(LCASE(?title), "treaty") || CONTAINS(LCASE(?title), "traité"))
                }
                LIMIT 10
                ''',
                'description': 'Search for documents with "treaty" in title'
            }
        ]
        
        self.results['treaty'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['treaty'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)  # Be nice to the endpoint
    
    def test_eu_directive_capabilities(self):
        """Test EU directive transposition capabilities"""
        print("\n" + "="*60)
        print("TESTING EU DIRECTIVE CAPABILITIES")
        print("="*60)
        
        tests = [
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  VALUES ?class { jolux:TranspositionAction jolux:InfringementProcedure }
                  ?instance rdf:type ?class .
                }
                GROUP BY ?class
                ''',
                'description': 'Test TranspositionAction and InfringementProcedure classes'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  ?instance rdf:type ?class .
                  FILTER(CONTAINS(LCASE(STR(?class)), "directive") || CONTAINS(LCASE(STR(?class)), "transpos"))
                }
                GROUP BY ?class
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for directive/transposition-related classes'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT ?doc ?title ?type
                WHERE {
                  ?doc rdf:type ?type .
                  ?doc eli:title ?title .
                  FILTER(CONTAINS(LCASE(?title), "directive") || CONTAINS(LCASE(?title), "transpos"))
                }
                LIMIT 10
                ''',
                'description': 'Search for documents with "directive" or "transposition" in title'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?count)
                WHERE {
                  ?s ?property ?o .
                  FILTER(CONTAINS(LCASE(STR(?property)), "transpos") || CONTAINS(LCASE(STR(?property)), "directive"))
                }
                GROUP BY ?property
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for transposition/directive-related properties'
            }
        ]
        
        self.results['eu_directive'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['eu_directive'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)
    
    def test_legislative_process_capabilities(self):
        """Test legislative process tracking"""
        print("\n" + "="*60)
        print("TESTING LEGISLATIVE PROCESS CAPABILITIES")
        print("="*60)
        
        tests = [
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  VALUES ?class { jolux:Draft jolux:Opinion jolux:Vote }
                  ?instance rdf:type ?class .
                }
                GROUP BY ?class
                ''',
                'description': 'Test Draft, Opinion, Vote classes'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  ?instance rdf:type ?class .
                  FILTER(CONTAINS(LCASE(STR(?class)), "draft") || 
                         CONTAINS(LCASE(STR(?class)), "opinion") || 
                         CONTAINS(LCASE(STR(?class)), "vote") ||
                         CONTAINS(LCASE(STR(?class)), "parliamentar"))
                }
                GROUP BY ?class
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for legislative process-related classes'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?count)
                WHERE {
                  ?s ?property ?o .
                  FILTER(CONTAINS(LCASE(STR(?property)), "workflow") || 
                         CONTAINS(LCASE(STR(?property)), "process") ||
                         CONTAINS(LCASE(STR(?property)), "stage") ||
                         CONTAINS(LCASE(STR(?property)), "phase"))
                }
                GROUP BY ?property
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for legislative workflow properties'
            }
        ]
        
        self.results['legislative'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['legislative'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)
    
    def test_predictive_capabilities(self):
        """Test predictive properties"""
        print("\n" + "="*60)
        print("TESTING PREDICTIVE CAPABILITIES")
        print("="*60)
        
        tests = [
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?count)
                WHERE {
                  VALUES ?property { jolux:foreseeableModificationBy jolux:foreseeableRepealBy }
                  ?s ?property ?o .
                }
                GROUP BY ?property
                ''',
                'description': 'Test specific predictive properties'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?count)
                WHERE {
                  ?s ?property ?o .
                  FILTER(CONTAINS(LCASE(STR(?property)), "foresee") || 
                         CONTAINS(LCASE(STR(?property)), "predict") ||
                         CONTAINS(LCASE(STR(?property)), "anticipat"))
                }
                GROUP BY ?property
                ORDER BY DESC(?count)
                ''',
                'description': 'Search for all predictive/foreseen properties'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT ?subject ?property ?object
                WHERE {
                  ?subject ?property ?object .
                  FILTER(CONTAINS(LCASE(STR(?property)), "foresee"))
                }
                LIMIT 5
                ''',
                'description': 'Sample predictive property usage'
            }
        ]
        
        self.results['predictive'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['predictive'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)
    
    def test_document_types(self):
        """Test document type filtering capabilities"""
        print("\n" + "="*60)
        print("TESTING DOCUMENT TYPE CAPABILITIES")
        print("="*60)
        
        tests = [
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT DISTINCT ?type (COUNT(?doc) as ?count)
                WHERE {
                  ?doc rdf:type ?type .
                  ?doc eli:type_document ?docType .
                }
                GROUP BY ?type
                ORDER BY DESC(?count)
                LIMIT 20
                ''',
                'description': 'Get all document types with counts'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT DISTINCT ?docType (COUNT(?doc) as ?count)
                WHERE {
                  ?doc eli:type_document ?docType .
                }
                GROUP BY ?docType
                ORDER BY DESC(?count)
                ''',
                'description': 'Get eli:type_document distribution'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT ?doc ?type ?title
                WHERE {
                  ?doc eli:type_document ?type .
                  ?doc eli:title ?title .
                  FILTER(?type IN ("TRAIT", "DIRECTIVE", "LOI", "RGD", "AMIN"))
                }
                LIMIT 10
                ''',
                'description': 'Test for TRAIT and DIRECTIVE document types'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX eli: <http://data.europa.eu/eli/ontology#>
                SELECT DISTINCT ?docType
                WHERE {
                  ?doc eli:type_document ?docType .
                  FILTER(CONTAINS(LCASE(?docType), "treat") || 
                         CONTAINS(LCASE(?docType), "trait") ||
                         CONTAINS(LCASE(?docType), "directive"))
                }
                ''',
                'description': 'Search for treaty/directive document type codes'
            }
        ]
        
        self.results['document_types'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['document_types'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)
    
    def test_basic_ontology_structure(self):
        """Test basic ontology structure"""
        print("\n" + "="*60)
        print("TESTING BASIC ONTOLOGY STRUCTURE")
        print("="*60)
        
        tests = [
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT DISTINCT ?class (COUNT(?instance) as ?count)
                WHERE {
                  ?instance rdf:type ?class .
                  FILTER(STRSTARTS(STR(?class), "http://data.legilux.public.lu/resource/ontology/jolux#"))
                }
                GROUP BY ?class
                ORDER BY DESC(?count)
                LIMIT 20
                ''',
                'description': 'Get top 20 JOLUX classes by instance count'
            },
            {
                'query': '''
                PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
                SELECT DISTINCT ?property (COUNT(?s) as ?count)
                WHERE {
                  ?s ?property ?o .
                  FILTER(STRSTARTS(STR(?property), "http://data.legilux.public.lu/resource/ontology/jolux#"))
                }
                GROUP BY ?property
                ORDER BY DESC(?count)
                LIMIT 20
                ''',
                'description': 'Get top 20 JOLUX properties by usage count'
            }
        ]
        
        self.results['ontology'] = []
        for test in tests:
            result = self.execute_query(test['query'], test['description'])
            self.results['ontology'].append({
                'description': test['description'],
                'query': test['query'],
                'result': result
            })
            time.sleep(1)
    
    def run_all_tests(self):
        """Run all capability tests"""
        print("🚀 Starting JOLUX SPARQL Endpoint Capability Tests")
        print(f"Endpoint: {self.endpoint}")
        
        self.test_basic_ontology_structure()
        self.test_treaty_capabilities()
        self.test_eu_directive_capabilities()
        self.test_legislative_process_capabilities()
        self.test_predictive_capabilities()
        self.test_document_types()
        
        self.generate_summary()
    
    def generate_summary(self):
        """Generate summary of findings"""
        print("\n" + "="*80)
        print("SUMMARY OF FINDINGS")
        print("="*80)
        
        for category, tests in self.results.items():
            print(f"\n📊 {category.upper()} CAPABILITIES:")
            print("-" * 50)
            
            for test in tests:
                desc = test['description']
                result = test['result']
                
                if result and 'results' in result:
                    bindings = result['results']['bindings']
                    count = len(bindings)
                    
                    if count > 0:
                        print(f"✅ {desc}: {count} results")
                        # Show sample data for interesting results
                        if count <= 5:
                            for binding in bindings:
                                values = [f"{k}={v.get('value', 'N/A')}" for k, v in binding.items()]
                                print(f"   {', '.join(values)}")
                        elif 'count' in bindings[0]:
                            # Show aggregated counts
                            for binding in bindings[:5]:
                                name = binding.get('class', binding.get('property', binding.get('type', {}))).get('value', 'Unknown')
                                count_val = binding.get('count', {}).get('value', '0')
                                print(f"   {name}: {count_val}")
                    else:
                        print(f"❌ {desc}: No results found")
                else:
                    print(f"❌ {desc}: Query failed")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 50)
        
        # Check what actually exists
        existing_capabilities = []
        missing_capabilities = []
        
        # Analyze results to determine what exists vs what doesn't
        for category, tests in self.results.items():
            for test in tests:
                if test['result'] and len(test['result'].get('results', {}).get('bindings', [])) > 0:
                    existing_capabilities.append(f"{category}: {test['description']}")
                else:
                    missing_capabilities.append(f"{category}: {test['description']}")
        
        print(f"✅ Working capabilities: {len(existing_capabilities)}")
        for cap in existing_capabilities[:10]:  # Show top 10
            print(f"   - {cap}")
        
        print(f"\n❌ Missing/non-working capabilities: {len(missing_capabilities)}")
        for cap in missing_capabilities[:10]:  # Show top 10
            print(f"   - {cap}")


if __name__ == "__main__":
    tester = JOLUXTester()
    tester.run_all_tests()