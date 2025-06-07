# JOLUX SPARQL Endpoint Capability Verification Report

## Executive Summary

After comprehensive testing of the JOLUX SPARQL endpoint (https://data.legilux.public.lu/sparqlendpoint), I've verified what capabilities actually exist versus theoretical assumptions. The endpoint has substantial data (500K+ documents) but many assumed capabilities are missing or work differently than expected.

## Key Findings

### ✅ WHAT ACTUALLY WORKS

#### 1. Treaty Capabilities (Partial)
- **jolux:TreatyDocument class**: 1,673 documents exist
- **jolux:TreatyProcess class**: 1,153 instances exist  
- **jolux:transposes property**: 3,293 relationships (WORKS WELL)
- **jolux:TaskForTreaty class**: 43,851 instances

**Working Query:**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?subject ?object WHERE {
  ?subject jolux:transposes ?object .
} LIMIT 5
```

#### 2. EU Directive Capabilities (Partial)
- **jolux:EUDirective class**: 2,498 documents exist
- **jolux:Transposition class**: 5,468 instances exist
- **Transposition relationships**: Complex structure but data exists

#### 3. Predictive Properties (EXCELLENT)
- **jolux:foreseesModificationOf**: 1,909 uses ✅
- **jolux:foreseesRepealOf**: 454 uses ✅
- **jolux:foreseesTranspositionOf**: 123 uses ✅
- **jolux:foreseesRectificationOf**: 1 use ✅
- **jolux:foreseesBasedOn**: 1 use ✅

**Working Query:**
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?subject ?object WHERE {
  ?subject jolux:foreseesModificationOf ?object .
} LIMIT 3
```

#### 4. Legislative Process (Partial)
- **jolux:Opinion class**: 97 instances
- **jolux:DraftRelatedDocument**: 21,753 instances
- **Various opinion types**: ConseilEtat, ProfessionalOrganisation opinions exist

#### 5. Document Type Classification
- Uses **jolux:typeDocument** property (180,069 uses)
- Does NOT use **eli:type_document** (0 uses)
- Document types via rdf:type work well

### ❌ WHAT DOESN'T WORK / IS MISSING

#### 1. Title and Metadata Access
- **Critical Issue**: Most documents lack accessible titles via eli:title
- Treaties and directives exist but titles are not exposed
- Date metadata often missing (eli:date_document not populated)

#### 2. Missing Classes
- **jolux:TreatyRatification**: Does not exist
- **jolux:TranspositionAction**: Does not exist  
- **jolux:InfringementProcedure**: Does not exist
- **jolux:Draft** and **jolux:Vote**: Do not exist

#### 3. Document Type Codes
- No TRAIT or DIRECTIVE type codes found
- Standard eli:type_document completely unused
- Must rely on rdf:type classification instead

#### 4. Text Search Limitations
- Cannot search documents by title content for "treaty" or "directive"
- Title fields are not populated or accessible

## Data Volumes by Capability

| Capability | Volume | Status |
|------------|--------|---------|
| Treaty Documents | 1,673 | ✅ Exists |
| Treaty Processes | 1,153 | ✅ Exists |
| EU Directives | 2,498 | ✅ Exists |
| Transpositions | 5,468 | ✅ Exists |
| Transposition Relationships | 3,293 | ✅ Works Well |
| Predictive Modifications | 1,909 | ✅ Excellent |
| Predictive Repeals | 454 | ✅ Excellent |
| Legislative Opinions | 97 | ✅ Limited |
| Draft Documents | 21,753 | ✅ Via DraftRelatedDocument |

## Working Sample Queries

### 1. Find Transposition Relationships
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?national_law ?eu_directive WHERE {
  ?national_law jolux:transposes ?eu_directive .
}
```

### 2. Find Laws That Will Be Modified
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?draft ?target_law WHERE {
  ?draft jolux:foreseesModificationOf ?target_law .
}
```

### 3. Find Treaties by Type
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?treaty WHERE {
  ?treaty rdf:type jolux:TreatyDocument .
}
```

### 4. Find EU Directives
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?directive WHERE {
  ?directive rdf:type jolux:EUDirective .
}
```

### 5. Document Type Distribution
```sparql
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?type_value (COUNT(?doc) as ?count) WHERE {
  ?doc jolux:typeDocument ?type_value .
}
GROUP BY ?type_value
ORDER BY DESC(?count)
```

## Recommendations for MCP Tools

### HIGH PRIORITY (Implement First)
1. **Transposition Tracking**: jolux:transposes works excellently
2. **Predictive Analysis**: All foresees* properties work well
3. **Document Classification**: Use jolux:typeDocument instead of eli:type_document

### MEDIUM PRIORITY 
1. **Treaty Search**: Can find treaties but titles not accessible
2. **EU Directive Search**: Can find directives but metadata limited
3. **Legislative Process**: Basic opinion tracking available

### LOW PRIORITY / SKIP
1. **Document Type Filtering by TRAIT/DIRECTIVE codes**: Not available
2. **Title-based search**: Titles not populated
3. **Advanced legislative workflow**: Classes don't exist

## Critical Implementation Notes

1. **Do NOT assume eli:title is available** - most documents lack this
2. **Use jolux:typeDocument not eli:type_document** for document classification
3. **Predictive properties are the strongest feature** - implement these first
4. **Transposition relationships work well** - priority for EU compliance tools
5. **Document URIs follow predictable patterns** but metadata is sparse

## Bottom Line

The JOLUX endpoint has substantial legal data but is structured differently than assumed. Focus on what works well (transpositions, predictive properties, document classification) rather than trying to force capabilities that don't exist. The endpoint is suitable for Luxembourg legal research but requires adapted approaches for metadata access.