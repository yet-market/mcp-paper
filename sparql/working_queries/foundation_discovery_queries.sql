-- FOUNDATION DISCOVERY QUERIES
-- Extracted from server/luxembourg_legal/tools.py discover_foundation_laws method
-- These are the proven working queries used in production

-- METHOD 1: CITATION ANALYSIS
-- Finds documents by citation count (most cited = most foundational)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count)  WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(CONTAINS(LCASE(?title), "société"))
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 10

-- METHOD 2: MODIFICATION FREQUENCY ANALYSIS  
-- Finds documents by modification frequency (most modified = most active/foundational)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?modified_doc ?title ?date (COUNT(?modifier) as ?modification_count) WHERE {
    ?modifier jolux:modifies ?modified_doc .
    ?modified_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?modified_doc jolux:dateDocument ?date .
    FILTER(CONTAINS(LCASE(?title), "société"))
}
GROUP BY ?modified_doc ?title ?date
ORDER BY DESC(?modification_count)
LIMIT 10

-- METHOD 3: LEGAL STATUS PRIORITY
-- Finds currently active laws (not repealed)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?doc ?title ?date ?type_doc WHERE {
    ?doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?doc jolux:dateDocument ?date .
    OPTIONAL { ?doc jolux:typeDocument ?type_doc }
    FILTER(CONTAINS(LCASE(?title), "société"))
    FILTER NOT EXISTS { ?repealer jolux:repeals ?doc }
}
ORDER BY DESC(?date)
LIMIT 10

-- METHOD 4: DOCUMENT TYPE AUTHORITY ANALYSIS
-- Prioritizes LOI and CODE documents (highest legal authority)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?doc ?title ?date ?type_doc WHERE {
    ?doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?doc jolux:dateDocument ?date .
    ?doc jolux:typeDocument ?type_doc .
    FILTER(CONTAINS(LCASE(?title), "société"))
    FILTER(CONTAINS(STR(?type_doc), "LOI") || CONTAINS(STR(?type_doc), "CODE"))
}
ORDER BY ?date
LIMIT 10

-- BASIC DOCUMENT SEARCH
-- Simple keyword search in document titles
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
LIMIT 50

-- CITATION NETWORK ANALYSIS
-- Get what document cites (outbound citations)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited ?title ?date ?type WHERE {
    <DOCUMENT_URI> jolux:cites ?cited .
    ?cited jolux:isRealizedBy/jolux:title ?title .
    ?cited jolux:dateDocument ?date .
    OPTIONAL { ?cited jolux:typeDocument ?type }
}
ORDER BY DESC(?date)

-- Get what cites document (inbound citations)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?citing ?title ?date ?type WHERE {
    ?citing jolux:cites <DOCUMENT_URI> .
    ?citing jolux:isRealizedBy/jolux:title ?title .
    ?citing jolux:dateDocument ?date .
    OPTIONAL { ?citing jolux:typeDocument ?type }
}
ORDER BY DESC(?date)

-- AMENDMENT HISTORY
-- Get what document modifies
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?modified ?title ?date ?type WHERE {
    <DOCUMENT_URI> jolux:modifies ?modified .
    ?modified jolux:isRealizedBy/jolux:title ?title .
    ?modified jolux:dateDocument ?date .
    OPTIONAL { ?modified jolux:typeDocument ?type }
}
ORDER BY DESC(?date)

-- Get what modifies document
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?modifier ?title ?date ?type WHERE {
    ?modifier jolux:modifies <DOCUMENT_URI> .
    ?modifier jolux:isRealizedBy/jolux:title ?title .
    ?modifier jolux:dateDocument ?date .
    OPTIONAL { ?modifier jolux:typeDocument ?type }
}
ORDER BY DESC(?date)

-- LEGAL STATUS CHECK
-- Check if document is repealed
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?repealer ?title ?date WHERE {
    ?repealer jolux:repeals <DOCUMENT_URI> .
    ?repealer jolux:isRealizedBy/jolux:title ?title .
    ?repealer jolux:dateDocument ?date .
}
ORDER BY DESC(?date)

-- Check consolidations
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?consolidated ?title ?date WHERE {
    <DOCUMENT_URI> jolux:consolidates ?consolidated .
    ?consolidated jolux:isRealizedBy/jolux:title ?title .
    ?consolidated jolux:dateDocument ?date .
}
ORDER BY DESC(?date)

-- LEGAL RELATIONSHIPS
-- Get legal foundations (what document is based on)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?foundation ?title ?date ?type WHERE {
    <DOCUMENT_URI> jolux:basedOn ?foundation .
    ?foundation jolux:isRealizedBy/jolux:title ?title .
    ?foundation jolux:dateDocument ?date .
    OPTIONAL { ?foundation jolux:typeDocument ?type }
}
ORDER BY DESC(?date)

-- Get implementations (what is based on document)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?implementation ?title ?date ?type WHERE {
    ?implementation jolux:basedOn <DOCUMENT_URI> .
    ?implementation jolux:isRealizedBy/jolux:title ?title .
    ?implementation jolux:dateDocument ?date .
    OPTIONAL { ?implementation jolux:typeDocument ?type }
}
ORDER BY DESC(?date)