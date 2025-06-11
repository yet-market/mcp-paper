# Lawyer-Like Legal Research Workflow Methodology

## 🏛️ FOUNDATION-FIRST HIERARCHICAL APPROACH

This document defines the lawyer-like methodology for legal research that mimics how experienced Luxembourg lawyers approach complex legal questions systematically.

## 📋 8-PHASE HIERARCHICAL WORKFLOW

### **PHASE 1: LEGAL DOMAIN ANALYSIS**
**Objective**: Identify the legal domain and foundation requirements like a real lawyer would

**Process**:
- Analyze the legal question to determine primary domain (commercial, civil, fiscal, social, etc.)
- Identify sub-domains and connected areas
- Determine expected foundation laws by priority
- Define strategic search keywords (single words, not phrases)
- Estimate historical periods for foundational texts

**Expected Output**:
```json
{
  "legal_domain": "droit commercial",
  "sub_domains": ["sociétés", "entreprises"],
  "expected_foundations": [
    {
      "type": "loi_generale",
      "description": "Loi sur les sociétés commerciales",
      "search_keywords": ["sociétés", "commercial", "SARL"],
      "expected_years": "1915-2020",
      "priority": 1
    }
  ],
  "methodology": "recherche fondateur droit commercial"
}
```

### **PHASE 2: FOUNDATION LAW DISCOVERY**
**Objective**: Discover foundational laws using multi-source methodology

**Methods** (in order of priority):
1. **Historical Foundation Discovery**: Find oldest laws in the domain (pre-1950)
2. **Citation-Based Foundation Discovery**: Find most cited documents (foundations)
3. **Authority-Based Foundation Discovery**: Find laws by highest authorities
4. **Document Type Foundation Discovery**: Find LOI-type foundations (highest authority)
5. **Strategic Keyword Search**: Enhanced single-keyword searches
6. **Subject Domain Discovery**: Find domain-specific foundations

**Scoring Criteria**:
- Document type hierarchy: LOI (500pts) > RGD (300pts) > AMIN (100pts)
- Historical age: Pre-1920 (+400pts), 1920-1950 (+350pts), etc.
- Citation frequency: High citations = foundation indicator
- Authority level: Parliament/Chambre (800pts) > Government (700pts)

**Expected Output**:
```json
{
  "foundations": [
    {
      "uri": "http://data.legilux.public.lu/eli/etat/leg/loi/1915/08/10/n1",
      "title": "Loi modifiée du 10 août 1915 concernant les sociétés commerciales",
      "importance_score": 950,
      "legal_domain": "droit commercial",
      "year": 1915,
      "foundation_type": "loi_generale"
    }
  ]
}
```

### **PHASE 3: HIERARCHICAL UNDERSTANDING**
**Objective**: Build legal hierarchy through citation and relationship analysis

**Process**:
- Analyze each foundation law for relationships
- Get citations (inbound and outbound)
- Map legal dependencies and hierarchies
- Understand foundation → implementation → execution chains

**Tools Needed**:
- `get_citations`: Get citation networks for foundations
- `get_relationships`: Get legal relationships and hierarchies

### **PHASE 4: CITATION CHAIN FOLLOWING**
**Objective**: Follow citation networks to discover connected laws

**Process**:
- Follow outbound citations (laws the foundation cites)
- Follow inbound citations (laws that cite the foundation)
- Build citation chains showing legal interconnections
- Identify key connected laws in the hierarchy

**Expected Output**:
```json
{
  "citation_chains": [
    {
      "foundation_uri": "http://data.legilux.public.lu/eli/etat/leg/loi/1915/08/10/n1",
      "chain_links": ["foundation_uri", "cited_law1", "cited_law2"],
      "chain_strength": 25,
      "legal_path": "Foundation → 15 cited → 10 citing"
    }
  ]
}
```

### **PHASE 5: AMENDMENT HISTORY TRACING**
**Objective**: Trace chronological legal evolution

**Process**:
- Get amendment history for priority laws
- Analyze major changes over time
- Understand legal evolution trends
- Identify current consolidation status

**Tools Needed**:
- `get_amendments`: Get amendment history for documents

### **PHASE 6: CONTENT EXTRACTION**
**Objective**: Extract detailed content from priority foundation documents

**Process**:
- Extract full content from top 3-5 foundation laws
- Focus on articles and sections relevant to the question
- Get detailed legal text for analysis

**Tools Needed**:
- `extract_content`: Extract detailed content from document URIs

### **PHASE 7: LEGAL STATUS VALIDATION**
**Objective**: Verify current validity and consolidation status

**Process**:
- Check legal status of all discovered documents
- Verify current validity (active, repealed, consolidated)
- Ensure recommendations are based on current law

**Tools Needed**:
- `check_legal_status`: Verify current status of documents

### **PHASE 8: STRUCTURED OUTPUT GENERATION**
**Objective**: Generate comprehensive legal analysis using foundation-first methodology

**Process**:
- Synthesize all discovered information
- Structure response hierarchically (foundations → implementations → details)
- Provide exhaustive analysis with proper legal citations
- Include practical guidance based on discovered foundations

**Expected Output**: Complete `LegalAnalysisResponse` with:
- Exhaustive legal content
- Reference sources organized hierarchically
- Citation networks showing relationships
- Amendment histories
- Validity status
- Practical recommendations

## 🎯 KEY PRINCIPLES

### **1. Foundation-First Approach**
- Always start with foundational laws before specific implementations
- Prioritize older, more cited, higher-authority documents
- Build understanding from foundation → hierarchy → specifics

### **2. Multi-Source Discovery**
- Use multiple methods to discover foundations (not just keyword search)
- Combine historical, citation, authority, and type-based discovery
- Consolidate and rank results by importance

### **3. Hierarchical Understanding**
- Understand legal hierarchy and relationships
- Follow citation chains to discover connected laws
- Respect legal authority levels (LOI > RGD > AMIN)

### **4. Chronological Awareness**
- Trace amendment history to understand legal evolution
- Ensure current validity of all recommendations
- Understand historical context of legal development

### **5. Comprehensive Coverage**
- Extract detailed content from priority documents
- Provide exhaustive analysis, not summaries
- Include practical guidance for implementation

## 🔧 REQUIRED MCP TOOLS

### **Current Tools Available**:
1. `search_documents`: Keyword-based document search
2. `get_citations`: Get citation networks
3. `get_relationships`: Get legal relationships
4. `get_amendments`: Get amendment history
5. `extract_content`: Extract document content
6. `check_legal_status`: Verify legal status

### **Recommended Additional Tools for Foundation Discovery**:
1. `discover_historical_foundations`: Find oldest foundational laws
2. `discover_citation_foundations`: Find most cited documents
3. `discover_authority_foundations`: Find laws by high authorities
4. `discover_loi_foundations`: Find LOI-type foundations
5. `discover_domain_foundations`: Find domain-specific foundations
6. `discover_active_foundations`: Find currently active foundations

## 🎯 SUCCESS CRITERIA

A successful lawyer-like workflow should:

1. **Discover 5-8 foundation laws** relevant to the question
2. **Build citation chains** connecting foundations to implementations
3. **Provide exhaustive legal analysis** (2000+ characters)
4. **Include 15+ reference sources** with proper URIs
5. **Show 20+ citations** demonstrating legal relationships
6. **Trace 10+ amendments** showing legal evolution
7. **Verify current validity** of all recommendations
8. **Provide practical guidance** for implementation

## 📝 EXAMPLE WORKFLOW

For question: "What are the current laws for creating a SARL in Luxembourg?"

1. **Domain Analysis**: Commercial law → company formation → SARL-specific
2. **Foundation Discovery**: Find 1915 commercial law, company formation laws
3. **Hierarchy Building**: Map commercial law → company law → SARL regulations
4. **Citation Following**: Follow connections to specific SARL provisions
5. **Amendment Tracing**: Understand recent changes to SARL law
6. **Content Extraction**: Get detailed SARL formation requirements
7. **Status Validation**: Verify all laws are current and valid
8. **Structured Output**: Comprehensive SARL creation guide with foundations

## 🔄 ITERATIVE IMPROVEMENT

The workflow should continuously improve by:
- Analyzing which foundation discovery methods work best
- Refining scoring algorithms based on results
- Adding new discovery methods as SPARQL capabilities are verified
- Optimizing performance while maintaining lawyer-like thoroughness

This methodology ensures that every legal question is answered with the same systematic, foundation-first approach that experienced Luxembourg lawyers use in practice.