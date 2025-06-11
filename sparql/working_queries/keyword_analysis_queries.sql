-- KEYWORD ANALYSIS QUERIES
-- Extracted from test_sparql_keyword_analysis.py and test_all_foundation_queries.py
-- These queries demonstrate the keyword problem and solution

-- PROBLEMATIC QUERY: SARL keyword (finds only 2 irrelevant results)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(CONTAINS(LCASE(?title), "sarl"))
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 20

-- SUCCESSFUL QUERY: société keyword (finds 1915 Commercial Law with 146 citations)
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
LIMIT 20

-- SUCCESSFUL QUERY: commercial keyword (also finds 1915 Commercial Law)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(CONTAINS(LCASE(?title), "commercial"))
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 20

-- DIRECT SEARCH: Find 1915 Commercial Law
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?doc ?title ?date ?type WHERE {
    ?doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?doc jolux:dateDocument ?date .
    OPTIONAL { ?doc jolux:typeDocument ?type }
    FILTER(STRSTARTS(?date, "1915"))
    FILTER(CONTAINS(LCASE(?title), "société") || CONTAINS(LCASE(?title), "commercial"))
}
ORDER BY ?date

-- ENHANCED KEYWORDS: Multi-keyword approach (solution implemented in client)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(
        CONTAINS(LCASE(?title), "commercial") ||
        CONTAINS(LCASE(?title), "société") ||
        CONTAINS(LCASE(?title), "entreprise") ||
        CONTAINS(LCASE(?title), "sarl")
    )
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 20

-- BASELINE QUERY: Pure SARL citation analysis (fails)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(CONTAINS(LCASE(?title), "sarl"))
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 10

-- ENHANCED QUERY: Historical commercial laws (succeeds)
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?cited_doc ?title ?date (COUNT(?citing_doc) as ?citation_count) WHERE {
    ?citing_doc jolux:cites ?cited_doc .
    ?cited_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?cited_doc jolux:dateDocument ?date .
    FILTER(
        CONTAINS(LCASE(?title), "commercial") ||
        CONTAINS(LCASE(?title), "société") ||
        CONTAINS(LCASE(?title), "entreprise") ||
        CONTAINS(LCASE(?title), "registre")
    )
    FILTER(?date < "1980-01-01"^^xsd:date)
}
GROUP BY ?cited_doc ?title ?date
ORDER BY DESC(?citation_count)
LIMIT 15

-- VALIDATION QUERY: Most modified commercial laws
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?modified_doc ?title ?original_date (COUNT(?modifier) as ?modification_count) WHERE {
    ?modifier jolux:modifies ?modified_doc .
    ?modified_doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?modified_doc jolux:dateDocument ?original_date .
    FILTER(
        CONTAINS(LCASE(?title), "commercial") ||
        CONTAINS(LCASE(?title), "société") ||
        CONTAINS(LCASE(?title), "code") ||
        CONTAINS(LCASE(?title), "registre")
    )
    FILTER(?original_date < "1990-01-01"^^xsd:date)
}
GROUP BY ?modified_doc ?title ?original_date
ORDER BY DESC(?modification_count)
LIMIT 15

-- AUTHORITY ANALYSIS: LOI documents only
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?doc ?title ?date ?type_doc ?authority WHERE {
    ?doc jolux:isRealizedBy ?expr .
    ?expr jolux:title ?title .
    ?doc jolux:dateDocument ?date .
    ?doc jolux:typeDocument ?type_doc .
    OPTIONAL { ?doc jolux:responsibilityOf ?authority }
    FILTER(CONTAINS(STR(?type_doc), "LOI"))
    FILTER(
        CONTAINS(LCASE(?title), "commercial") ||
        CONTAINS(LCASE(?title), "société") ||
        CONTAINS(LCASE(?title), "entreprise") ||
        CONTAINS(LCASE(?title), "code")
    )
}
ORDER BY ?date
LIMIT 20