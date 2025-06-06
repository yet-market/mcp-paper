# 🔍 JOLUX SPARQL ENDPOINT USAGE GUIDE

**Complete guide for professional Luxembourg legal research using the JOLUX SPARQL endpoint**

---

## **📊 ENDPOINT INFORMATION**

### **Connection Details**
- **Endpoint URL**: `https://data.legilux.public.lu/sparqlendpoint`
- **Protocol**: SPARQL 1.1 Query Language
- **Format**: JSON results
- **Timeout**: 15-30 seconds recommended
- **Authentication**: None required

### **Setup**
```python
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper('https://data.legilux.public.lu/sparqlendpoint')
sparql.setReturnFormat(JSON)
sparql.setTimeout(30)
```

---

## **🏗️ JOLUX ONTOLOGY STRUCTURE**

### **Core Namespace**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
```

### **Document Hierarchy (217,446+ documents)**
```sparql
# Document types by authority and count:
BaseAct           (123,578)  # Foundational legislation (highest authority)
Act               (142,989)  # Regular parliamentary legislation  
LegalResource     (217,446)  # General legal documents
NationalLegalResource (212,244)  # Luxembourg-specific documents
Memorial          (64,119)   # Official gazette publications
Manifestation     (506,128)  # Physical document representations
Expression        (238,518)  # Document versions/expressions
Work              (362,475)  # Abstract legal works
ComplexWork       (143,349)  # Multi-part legal documents
```

### **Core Structure Pattern**
```sparql
# All Luxembourg legal documents follow this pattern:
?entity jolux:isRealizedBy ?expression .
?expression jolux:title ?title .
?entity a ?type .
?entity jolux:dateDocument ?date .
```

---

## **🔍 ESSENTIAL SPARQL QUERIES**

### **1. Basic Document Search**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?entity ?date ?title ?type WHERE {
    ?entity jolux:dateDocument ?date ;
            a ?type ;
            jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
    FILTER(regex(str(?title), "SARL", "i"))
}
ORDER BY DESC(?date)
LIMIT 50
```

### **2. Multi-Field Enhanced Search**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT DISTINCT ?entity ?date ?title ?type ?pubDate ?entryForce ?authority ?basedOn WHERE {
    ?entity jolux:dateDocument ?date ;
            a ?type ;
            jolux:isRealizedBy ?expression .
    ?expression jolux:title ?title .
    
    OPTIONAL { ?entity jolux:publicationDate ?pubDate }
    OPTIONAL { ?entity jolux:dateEntryInForce ?entryForce }
    OPTIONAL { ?entity jolux:responsibilityOf ?authority }
    OPTIONAL { ?entity jolux:basedOn ?basedOn }
    
    # Multi-field search strategy
    {
        FILTER(regex(str(?title), "KEYWORDS", "i"))
    } UNION {
        ?entity jolux:basedOn ?base .
        ?base jolux:isRealizedBy/jolux:title ?baseTitle .
        FILTER(regex(str(?baseTitle), "KEYWORDS", "i"))
    } UNION {
        FILTER(regex(str(?authority), "KEYWORDS", "i"))
    }
}
ORDER BY DESC(?date)
LIMIT 500
```

### **3. Legal Relationship Discovery**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?related ?title ?relationship ?date ?type WHERE {
    {
        # Documents this one is based on (legal foundation)
        <DOCUMENT_URI> jolux:basedOn+ ?related .
        BIND("based_on" as ?relationship)
    } UNION {
        # Documents that are based on this one (implementations)
        ?related jolux:basedOn+ <DOCUMENT_URI> .
        BIND("implements" as ?relationship)
    } UNION {
        # Documents that are part of the same legal work
        <DOCUMENT_URI> jolux:isMemberOf ?work .
        ?related jolux:isMemberOf ?work .
        FILTER(?related != <DOCUMENT_URI>)
        BIND("same_work" as ?relationship)
    }
    
    ?related jolux:isRealizedBy/jolux:title ?title ;
             jolux:dateDocument ?date ;
             a ?type .
}
ORDER BY ?relationship DESC(?date)
LIMIT 50
```

### **4. Temporal Analysis with Multiple Dates**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?entity ?title ?docDate ?pubDate ?entryForce ?type WHERE {
    VALUES ?entity { <URI1> <URI2> <URI3> }
    
    ?entity jolux:dateDocument ?docDate ;
            jolux:isRealizedBy/jolux:title ?title ;
            a ?type .
    
    OPTIONAL { ?entity jolux:publicationDate ?pubDate }
    OPTIONAL { ?entity jolux:dateEntryInForce ?entryForce }
}
ORDER BY DESC(?docDate)
```

### **5. Authority and Document Type Analysis**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?entity ?title ?authority ?docType ?typeDocument WHERE {
    ?entity jolux:isRealizedBy/jolux:title ?title ;
            a ?docType .
    
    OPTIONAL { ?entity jolux:responsibilityOf ?authority }
    OPTIONAL { ?entity jolux:typeDocument ?typeDocument }
    
    FILTER(regex(str(?title), "KEYWORDS", "i"))
}
LIMIT 100
```

---

## **⚖️ PROFESSIONAL LEGAL RESEARCH PATTERNS**

### **Pattern 1: Constitutional to Implementation Hierarchy**
```sparql
# Find complete legal hierarchy for a topic
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?entity ?title ?type ?authority ?based_on WHERE {
    ?entity jolux:isRealizedBy/jolux:title ?title ;
            a ?type .
    
    OPTIONAL { ?entity jolux:responsibilityOf ?authority }
    OPTIONAL { ?entity jolux:basedOn ?based_on }
    
    FILTER(regex(str(?title), "société", "i"))
    
    # Prioritize by legal authority
    FILTER(?type IN (
        jolux:BaseAct,           # Constitutional/foundational
        jolux:Act,               # Parliamentary legislation
        jolux:LegalResource,     # Legal documents
        jolux:Memorial           # Official gazette
    ))
}
ORDER BY 
    IF(?type = jolux:BaseAct, 1,
    IF(?type = jolux:Act, 2,
    IF(?type = jolux:Memorial, 3, 4)))
    DESC(?date)
```

### **Pattern 2: Amendment Chain Discovery**
```sparql
# Trace complete amendment history
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?original ?amendment ?amendDate ?title WHERE {
    ?original jolux:isRealizedBy/jolux:title ?originalTitle .
    FILTER(regex(?originalTitle, "Code de commerce", "i"))
    
    # Follow amendment chain (transitive)
    ?amendment jolux:basedOn+ ?original ;
               jolux:dateDocument ?amendDate ;
               jolux:isRealizedBy/jolux:title ?title .
}
ORDER BY ?amendDate
```

### **Pattern 3: EU Law Integration Discovery**
```sparql
# Find EU law relationships
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?luxembourgDoc ?euDoc ?title ?euTitle WHERE {
    ?luxembourgDoc jolux:basedOn ?euDoc ;
                   jolux:isRealizedBy/jolux:title ?title .
    
    ?euDoc jolux:isRealizedBy/jolux:title ?euTitle .
    
    # EU documents often contain "directive" or "regulation"
    FILTER(regex(str(?euTitle), "directive|regulation|règlement", "i"))
    
    # Luxembourg documents for specific topic
    FILTER(regex(str(?title), "SARL|société", "i"))
}
```

### **Pattern 4: Contemporary Legal Clustering**
```sparql
# Find related documents by temporal proximity
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?doc1 ?doc2 ?title1 ?title2 ?date1 ?date2 WHERE {
    ?referenceDoc jolux:isRealizedBy/jolux:title "REFERENCE_TITLE" ;
                  jolux:dateDocument ?refDate .
    
    ?doc1 jolux:dateDocument ?date1 ;
          jolux:isRealizedBy/jolux:title ?title1 .
    
    ?doc2 jolux:dateDocument ?date2 ;
          jolux:isRealizedBy/jolux:title ?title2 .
    
    # Documents published within 1 year of each other
    FILTER(ABS(YEAR(?date1) - YEAR(?refDate)) <= 1)
    FILTER(ABS(YEAR(?date2) - YEAR(?refDate)) <= 1)
    FILTER(?doc1 != ?doc2)
    FILTER(?doc1 != ?referenceDoc)
    FILTER(?doc2 != ?referenceDoc)
}
```

---

## **🎯 OPTIMIZATION STRATEGIES**

### **Query Performance**
```sparql
# ✅ GOOD: Specific filters early
SELECT ?entity ?title WHERE {
    ?entity a jolux:Act .                    # Filter by type first
    ?entity jolux:isRealizedBy/jolux:title ?title .
    FILTER(regex(?title, "SARL", "i"))       # Then filter by content
}
LIMIT 50                                     # Always limit results

# ❌ AVOID: Broad queries without limits
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(regex(str(?o), "société", "i"))
}
# This will timeout!
```

### **Efficient Multi-Field Search**
```sparql
# Use UNION for OR logic, not multiple FILTER statements
{
    FILTER(regex(str(?title), "keyword", "i"))
} UNION {
    FILTER(regex(str(?authority), "keyword", "i"))
} UNION {
    ?entity jolux:basedOn ?base .
    ?base jolux:isRealizedBy/jolux:title ?baseTitle .
    FILTER(regex(str(?baseTitle), "keyword", "i"))
}
```

### **Relationship Queries**
```sparql
# ✅ GOOD: Use transitive property with limits
?document jolux:basedOn+ ?foundation
LIMIT 50

# ✅ GOOD: Specify direction clearly
<specific_uri> jolux:basedOn+ ?related     # What this is based on
?related jolux:basedOn+ <specific_uri>     # What is based on this

# ❌ AVOID: Bidirectional transitive without limits
?doc1 jolux:basedOn* ?doc2 .
?doc2 jolux:basedOn* ?doc1 .
# Will cause timeout!
```

---

## **📅 DATE PROPERTY USAGE**

### **Three Critical Date Properties**
```sparql
# Document lifecycle dates
?entity jolux:dateDocument ?creationDate .      # When document was created
?entity jolux:publicationDate ?pubDate .        # When officially published  
?entity jolux:dateEntryInForce ?effectiveDate . # When law takes effect
```

### **Currency Analysis Pattern**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?entity ?title ?created ?published ?effective ?age WHERE {
    ?entity jolux:isRealizedBy/jolux:title ?title ;
            jolux:dateDocument ?created .
    
    OPTIONAL { ?entity jolux:publicationDate ?published }
    OPTIONAL { ?entity jolux:dateEntryInForce ?effective }
    
    # Calculate age in years
    BIND(YEAR(NOW()) - YEAR(?created) as ?age)
    
    FILTER(regex(?title, "SARL", "i"))
    FILTER(?age <= 10)  # Only documents from last 10 years
}
ORDER BY DESC(?created)
```

---

## **🔗 RELATIONSHIP PROPERTIES**

### **Core Relationships**
```sparql
jolux:basedOn        # Legal foundation (A is based on B)
jolux:isRealizedBy   # Document to expression link
jolux:responsibilityOf # Publishing authority
jolux:isMemberOf     # Part of larger work
jolux:isPartOf       # Structural hierarchy
jolux:typeDocument   # Document classification
```

### **Relationship Discovery Pattern**
```sparql
# Complete relationship map for a document
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>

SELECT ?property ?value ?valueTitle WHERE {
    <DOCUMENT_URI> ?property ?value .
    
    # Get titles for related documents
    OPTIONAL {
        ?value jolux:isRealizedBy/jolux:title ?valueTitle
    }
    
    # Focus on legal relationships
    FILTER(?property IN (
        jolux:basedOn,
        jolux:responsibilityOf,
        jolux:isMemberOf,
        jolux:isPartOf,
        jolux:typeDocument
    ))
}
```

---

## **⚠️ PERFORMANCE GUIDELINES**

### **Query Limits**
- **Always use LIMIT**: Never run unlimited queries
- **Timeout handling**: Queries timeout after ~15-30 seconds
- **Batch processing**: Process large result sets in chunks
- **Specific filters**: Apply restrictive filters early

### **Efficient Patterns**
```sparql
# ✅ EFFICIENT: Filter by type first, then content
?entity a jolux:BaseAct .
?entity jolux:isRealizedBy/jolux:title ?title .
FILTER(regex(?title, "keyword", "i"))

# ✅ EFFICIENT: Use VALUES for specific URIs
VALUES ?entity { <uri1> <uri2> <uri3> }
?entity jolux:dateDocument ?date .

# ❌ INEFFICIENT: Complex regex on large datasets
FILTER(regex(str(?anyProperty), "complex.*pattern", "i"))
```

### **Common Timeout Causes**
- Transitive properties without limits (`jolux:basedOn*`)
- Complex regex patterns on text fields
- Queries without type restrictions
- Bidirectional relationship traversal

---

## **🚀 PRODUCTION IMPLEMENTATION**

### **Connection Setup**
```python
def create_jolux_connection():
    sparql = SPARQLWrapper('https://data.legilux.public.lu/sparqlendpoint')
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(30)
    sparql.setMethod('GET')  # Only GET requests supported
    return sparql

def execute_safe_query(sparql, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            sparql.setQuery(query)
            results = sparql.query().convert()
            return results
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)  # Brief delay before retry
```

### **Error Handling**
```python
def handle_jolux_response(results):
    if 'results' in results and 'bindings' in results['results']:
        return results['results']['bindings']
    else:
        logger.warning(f"Unexpected JOLUX response format: {results}")
        return []
```

### **Legal Research Workflow**
```python
# 1. Multi-field search
docs = multi_field_search("SARL", limit=500)

# 2. Legal relationships
for doc in docs[:10]:
    relationships = discover_legal_relationships(doc['uri'])

# 3. Temporal analysis  
timeline = temporal_legal_analysis([doc['uri'] for doc in docs])

# 4. Authority ranking
ranked_docs = assess_legal_authority(docs)

# 5. Content extraction
content = extract_document_content([doc['uri'] for doc in ranked_docs[:15]])
```

---

## **📈 EXPECTED RESULTS**

### **Query Performance**
- **Basic search**: 50-200 documents in 2-5 seconds
- **Multi-field search**: 100-500 documents in 5-10 seconds  
- **Relationship discovery**: 20-50 relationships in 3-8 seconds
- **Temporal analysis**: Complete timeline in 5-15 seconds

### **Data Quality**
- **Document coverage**: 217,446+ legal documents
- **Relationship depth**: 3-5 levels of legal hierarchy
- **Temporal range**: 1800s to present day
- **Authority verification**: Complete publishing source data

### **Professional Standards**
- **Legal hierarchy**: Constitutional → Parliamentary → Ministerial → Administrative
- **Currency validation**: Amendment chain tracking
- **EU integration**: Directive transposition discovery
- **Citation quality**: Official legal document URIs and metadata

---

## **🎯 SUCCESS METRICS**

**For SARL research query, expect:**
- 50-100 relevant documents discovered
- Code de commerce (foundational law) identified and prioritized
- Amendment chains from 1915 → 2016 → 2020 tracked
- EU directive relationships discovered
- Current legal status validated
- Complete procedural guidance extracted

**Professional legal research standard achieved through optimal JOLUX endpoint utilization.**