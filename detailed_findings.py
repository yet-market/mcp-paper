#!/usr/bin/env python3
"""
Detailed analysis of JOLUX SPARQL capabilities based on initial findings
"""

import requests
import json
import time


class DetailedJOLUXAnalysis:
    def __init__(self):
        self.endpoint = "https://data.legilux.public.lu/sparqlendpoint"
        self.headers = {
            'Accept': 'application/sparql-results+json',
            'User-Agent': 'JOLUX-Detailed-Analysis/1.0'
        }
    
    def execute_query(self, query: str, description: str = "") -> dict:
        """Execute SPARQL query and return results"""
        try:
            print(f"\n🔍 {description}")
            params = {'query': query}
            response = requests.get(self.endpoint, params=params, headers=self.headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('results', {}).get('bindings', []))
                print(f"✅ {count} results")
                return data
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                return {}
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {}
    
    def analyze_treaty_capabilities(self):
        """Deep dive into treaty capabilities"""
        print("\n" + "="*60)
        print("DETAILED TREATY ANALYSIS")
        print("="*60)
        
        # Get sample treaty documents
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        PREFIX eli: <http://data.europa.eu/eli/ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?treaty ?title ?date ?status
        WHERE {
          ?treaty rdf:type jolux:TreatyDocument .
          OPTIONAL { ?treaty eli:title ?title }
          OPTIONAL { ?treaty eli:date_document ?date }
          OPTIONAL { ?treaty jolux:status ?status }
        }
        ORDER BY DESC(?date)
        LIMIT 5
        '''
        result = self.execute_query(query, "Sample treaty documents with metadata")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                treaty = binding.get('treaty', {}).get('value', 'N/A')
                title = binding.get('title', {}).get('value', 'No title')
                date = binding.get('date', {}).get('value', 'No date')
                status = binding.get('status', {}).get('value', 'No status')
                print(f"   {treaty}")
                print(f"   Title: {title}")
                print(f"   Date: {date}")
                print(f"   Status: {status}")
                print()
        
        # Test jolux:transposes usage
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        SELECT ?subject ?object
        WHERE {
          ?subject jolux:transposes ?object .
        }
        LIMIT 5
        '''
        result = self.execute_query(query, "Sample jolux:transposes relationships")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                subject = binding.get('subject', {}).get('value', 'N/A')
                obj = binding.get('object', {}).get('value', 'N/A')
                print(f"   {subject} transposes {obj}")
    
    def analyze_directive_capabilities(self):
        """Deep dive into EU directive capabilities"""
        print("\n" + "="*60)
        print("DETAILED EU DIRECTIVE ANALYSIS")
        print("="*60)
        
        # Get sample EU directives
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        PREFIX eli: <http://data.europa.eu/eli/ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?directive ?title ?date
        WHERE {
          ?directive rdf:type jolux:EUDirective .
          OPTIONAL { ?directive eli:title ?title }
          OPTIONAL { ?directive eli:date_document ?date }
        }
        ORDER BY DESC(?date)
        LIMIT 5
        '''
        result = self.execute_query(query, "Sample EU directives")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                directive = binding.get('directive', {}).get('value', 'N/A')
                title = binding.get('title', {}).get('value', 'No title')
                date = binding.get('date', {}).get('value', 'No date')
                print(f"   {directive}")
                print(f"   Title: {title}")
                print(f"   Date: {date}")
                print()
        
        # Get sample transpositions
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        PREFIX eli: <http://data.europa.eu/eli/ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?transposition ?directive ?national_law
        WHERE {
          ?transposition rdf:type jolux:Transposition .
          OPTIONAL { ?transposition jolux:transposesDirective ?directive }
          OPTIONAL { ?transposition jolux:isTransposedBy ?national_law }
        }
        LIMIT 5
        '''
        result = self.execute_query(query, "Sample transposition relationships")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                trans = binding.get('transposition', {}).get('value', 'N/A')
                directive = binding.get('directive', {}).get('value', 'N/A')
                law = binding.get('national_law', {}).get('value', 'N/A')
                print(f"   Transposition: {trans}")
                print(f"   Directive: {directive}")
                print(f"   National Law: {law}")
                print()
    
    def analyze_predictive_capabilities(self):
        """Analyze what predictive properties actually exist"""
        print("\n" + "="*60)
        print("DETAILED PREDICTIVE ANALYSIS")
        print("="*60)
        
        # Find all properties with "foresee" in name
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        SELECT DISTINCT ?property (COUNT(?s) as ?count)
        WHERE {
          ?s ?property ?o .
          FILTER(CONTAINS(STR(?property), "foresee"))
        }
        GROUP BY ?property
        ORDER BY DESC(?count)
        '''
        result = self.execute_query(query, "All properties containing 'foresee'")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                prop = binding.get('property', {}).get('value', 'N/A')
                count = binding.get('count', {}).get('value', '0')
                print(f"   {prop}: {count} uses")
        
        # Test specific predictive properties
        for prop in ['foreseesModificationOf', 'foreseesRepealOf', 'foreseesRectificationOf']:
            query = f'''
            PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
            SELECT ?subject ?object
            WHERE {{
              ?subject jolux:{prop} ?object .
            }}
            LIMIT 3
            '''
            result = self.execute_query(query, f"Sample jolux:{prop} usage")
            
            if result and 'results' in result:
                for binding in result['results']['bindings']:
                    subject = binding.get('subject', {}).get('value', 'N/A')
                    obj = binding.get('object', {}).get('value', 'N/A')
                    print(f"   {subject} {prop} {obj}")
    
    def analyze_document_types(self):
        """Analyze document type structure"""
        print("\n" + "="*60)
        print("DETAILED DOCUMENT TYPE ANALYSIS")
        print("="*60)
        
        # Check if eli:type_document is used
        query = '''
        PREFIX eli: <http://data.europa.eu/eli/ontology#>
        SELECT DISTINCT ?type (COUNT(?doc) as ?count)
        WHERE {
          ?doc eli:type_document ?type .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        LIMIT 20
        '''
        result = self.execute_query(query, "eli:type_document distribution")
        
        if not result or not result.get('results', {}).get('bindings'):
            print("   ❌ eli:type_document not used in this dataset")
        
        # Try alternative document type properties
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        SELECT DISTINCT ?property (COUNT(?s) as ?count)
        WHERE {
          ?s ?property ?o .
          FILTER(CONTAINS(LCASE(STR(?property)), "type"))
        }
        GROUP BY ?property
        ORDER BY DESC(?count)
        LIMIT 10
        '''
        result = self.execute_query(query, "Properties containing 'type'")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                prop = binding.get('property', {}).get('value', 'N/A')
                count = binding.get('count', {}).get('value', '0')
                print(f"   {prop}: {count} uses")
        
        # Check document classification via rdf:type
        query = '''
        PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?type (COUNT(?doc) as ?count)
        WHERE {
          ?doc rdf:type ?type .
          FILTER(STRSTARTS(STR(?type), "http://data.legilux.public.lu/resource/ontology/jolux#"))
          FILTER(?type != jolux:LegalResource && ?type != jolux:NationalLegalResource)
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        LIMIT 15
        '''
        result = self.execute_query(query, "Document types via rdf:type (JOLUX classes)")
        
        if result and 'results' in result:
            for binding in result['results']['bindings']:
                doc_type = binding.get('type', {}).get('value', 'N/A')
                count = binding.get('count', {}).get('value', '0')
                print(f"   {doc_type}: {count} documents")
    
    def analyze_working_samples(self):
        """Get working sample queries for each capability"""
        print("\n" + "="*60)
        print("WORKING SAMPLE QUERIES")
        print("="*60)
        
        samples = {
            "Treaty Search": '''
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX eli: <http://data.europa.eu/eli/ontology#>
SELECT ?treaty ?title WHERE {
  ?treaty rdf:type jolux:TreatyDocument .
  ?treaty eli:title ?title .
} LIMIT 5''',
            
            "EU Directive Search": '''
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX eli: <http://data.europa.eu/eli/ontology#>
SELECT ?directive ?title WHERE {
  ?directive rdf:type jolux:EUDirective .
  ?directive eli:title ?title .
} LIMIT 5''',
            
            "Transposition Relationship": '''
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?subject ?object WHERE {
  ?subject jolux:transposes ?object .
} LIMIT 5''',
            
            "Predictive Properties": '''
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?subject ?object WHERE {
  ?subject jolux:foreseesModificationOf ?object .
} LIMIT 3''',
            
            "Legislative Opinions": '''
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX eli: <http://data.europa.eu/eli/ontology#>
SELECT ?opinion ?title WHERE {
  ?opinion rdf:type jolux:Opinion .
  ?opinion eli:title ?title .
} LIMIT 3'''
        }
        
        for name, query in samples.items():
            print(f"\n📝 {name}:")
            print("```sparql")
            print(query)
            print("```")
            
            result = self.execute_query(query, f"Testing {name}")
            if result and result.get('results', {}).get('bindings'):
                print("✅ This query works!")
            else:
                print("❌ This query returns no results")
    
    def run_detailed_analysis(self):
        """Run all detailed analyses"""
        print("🔬 Starting Detailed JOLUX SPARQL Analysis")
        print(f"Endpoint: {self.endpoint}")
        
        self.analyze_treaty_capabilities()
        self.analyze_directive_capabilities()
        self.analyze_predictive_capabilities()
        self.analyze_document_types()
        self.analyze_working_samples()


if __name__ == "__main__":
    analyzer = DetailedJOLUXAnalysis()
    analyzer.run_detailed_analysis()