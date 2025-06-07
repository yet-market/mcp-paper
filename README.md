# 🏛️ Luxembourg Legal Intelligence MCP Server - Professional Edition

**Single-keyword precision search with complete JOLUX relationship intelligence**

![MCP Compliant](https://img.shields.io/badge/MCP-Fully%20Compliant-green)
![JOLUX Powered](https://img.shields.io/badge/JOLUX-Proven%20Capabilities-orange)
![Professional Grade](https://img.shields.io/badge/Legal%20Research-Professional%20Grade-blue)

---

## 🎯 **System Overview**

Professional Luxembourg legal research system with **6 specialized tools** leveraging **proven JOLUX endpoint capabilities**. Built on single-keyword search strategy and complete legal relationship intelligence.

### **Core Capabilities Verified:**
- **75,123 citation relationships** (jolux:cites) - 0.06s queries
- **26,826 amendment relationships** (jolux:modifies) - 0.06s queries  
- **17,910 repeal relationships** (jolux:repeals) - 0.07s queries
- **368 consolidation relationships** (jolux:consolidates) - 0.06s queries
- **300,000+ legal documents** with complete metadata
- **Context-safe responses** (30-60KB per tool)

---

## 🔧 **Professional Legal Intelligence Tools (6 Tools)**

### **Tool 1: `search_documents`**
**Purpose**: Find relevant legal documents with complete metadata using proven single-keyword strategy

**How it works**:
- Takes single precise keywords (e.g., "SARL", "société", "règlement")
- Searches Luxembourg legal document titles 
- Returns 50-100 documents with ALL available metadata:
  - Document URI and title
  - Document type (LOI, RGD, AMIN, PA, etc.)
  - Legal subject domain (1597=Social Impact, 674=Education Services, etc.)
  - Publishing authority (Parliament, Ministry, Administration)
  - Publication date and entry-into-force date

**Key advantage**: No assumptions about legal language - AI sees raw data and discovers patterns like "SARL documents are AMIN type in domain 1597"

**Performance**: 0.08-0.22s, 30-60KB response size

---

### **Tool 2: `get_citations`**
**Purpose**: Map complete citation network for legal precedent analysis

**How it works**:
- Takes specific document URI from search results
- Queries JOLUX citation database (75,123 relationships)
- Returns bidirectional citation data:
  - **Outbound citations**: What this document cites (legal foundation)
  - **Inbound citations**: What documents cite this (legal influence)
  - Complete metadata for all cited/citing documents

**Legal value**: Reveals precedent networks, legal authority chains, and cross-references between laws

**Performance**: 0.06s queries, typically 2-20 citations per document

---

### **Tool 3: `get_amendments`**
**Purpose**: Track complete legal evolution and modification history

**How it works**:
- Takes document URI and queries amendment database (26,826 relationships)
- Uses jolux:modifies and jolux:modifiedBy properties
- Returns complete modification timeline:
  - **What this document modifies** (laws it changes)
  - **What modifies this document** (subsequent amendments)
  - Chronological amendment history with dates
  - Complete metadata for all modifying documents

**Legal value**: Track legal evolution from original 1915 laws to current 2025 versions, understand legislative history

**Performance**: 0.06s queries, comprehensive modification tracking

---

### **Tool 4: `check_legal_status`**
**Purpose**: Verify current legal validity and find official consolidated versions

**How it works**:
- Takes document URI and checks against repeal database (17,910 relationships)
- Queries consolidation database (368 official consolidations)
- Returns current legal status:
  - **Legal currency**: CURRENT, REPEALED, or SUPERSEDED
  - **Repealing documents**: What law superseded this (if any)
  - **Consolidated versions**: Official current text versions available
  - **Effective dates**: When changes took effect

**Legal value**: Critical for professional practice - ensures you're citing current law, not outdated versions

**Performance**: 0.07s queries, definitive legal currency validation

---

### **Tool 5: `get_relationships`**
**Purpose**: Discover broader legal foundations and hierarchical dependencies

**How it works**:
- Takes document URI and queries structural relationships
- Uses jolux:basedOn and related properties to map legal hierarchy
- Returns legal framework structure:
  - **Legal foundation**: What higher laws authorize this document
  - **Legal hierarchy**: Constitutional → Laws → Regulations → Administrative orders
  - **Implementation chain**: How legal principles flow down to specific regulations
  - **Authority chain**: Which institutions have jurisdiction

**Legal value**: Understand complete legal context - what constitutional or legal framework supports specific regulations

**Performance**: Fast structural queries, reveals complete legal dependency tree

---

### **Tool 6: `extract_content`**
**Purpose**: Get actual legal text for detailed analysis

**How it works**:
- Takes document URIs from search results (limited to 5-10 to avoid context explosion)
- Extracts actual legal text from Luxembourg official publications
- Handles both HTML and PDF document formats
- Returns structured legal content:
  - **Full legal text**: Articles, sections, chapters
  - **Document structure**: Legal organization and numbering
  - **Procedural details**: Specific requirements, deadlines, obligations
  - **Technical specifications**: Forms, procedures, compliance requirements

**Legal value**: Essential final step - after finding and analyzing documents, get the actual legal text to read specific requirements

**Performance**: Content extraction with structure preservation, context-aware sizing

---

## 🚀 **Professional Legal Research Workflow**

### **Typical Legal Question Process:**

**Question**: "Comment créer une SARL au Luxembourg?"

1. **`search_documents("SARL")`** 
   - Finds 50 SARL-related documents
   - AI discovers: Most are AMIN type (ministerial orders) in domain 1597
   - Also finds LOI type documents (general company law)

2. **`search_documents("société")`** 
   - Finds broader company law framework
   - AI discovers: General company legislation, commercial code references

3. **`get_citations(main_company_law_uri)`**
   - Shows what the main company law references
   - Reveals regulatory framework and constitutional basis

4. **`get_amendments(main_company_law_uri)`**
   - Shows how SARL law evolved: 1915 → 2016 reform → 2024 updates
   - Reveals recent changes affecting current procedures

5. **`check_legal_status(main_company_law_uri)`**
   - Confirms current law is valid, not repealed
   - Finds official consolidated version for current practice

6. **`extract_content([company_law_uri, recent_amendments_uri])`**
   - Gets actual legal text: capital requirements, procedures, obligations
   - Provides specific articles and procedural details

---

## ⚖️ **MCP Philosophy Compliance**

### **✅ Tools Provide Data, AI Synthesizes**
- Each tool returns structured legal data only
- No hardcoded guidance or domain mappings
- AI discovers legal patterns autonomously
- No predetermined workflows or assumptions

### **✅ Composable and Independent**
- Tools can be used in any order or combination
- Each serves single, focused purpose
- AI determines optimal research strategy
- No tool dependencies or forced sequences

### **✅ Rich Legal Data Exchange**
- Complete JOLUX metadata in all responses
- Professional-grade legal intelligence quality
- Context-safe response sizing (30-60KB)
- All Luxembourg legal relationships accessible

---

## 📊 **Proven Performance Metrics**

### **SPARQL Query Performance (Tested)**
- Basic document search: 0.22s for 10 results
- Citation queries: 0.06s average
- Amendment queries: 0.06s average
- Repeal queries: 0.07s average
- Complex multi-property: 0.08s for 20 results
- Large result sets: 0.13s for 500 results

### **Context Management (Verified)**
- 50 documents: 30KB (optimal)
- 100 documents: 60KB (safe)
- 200 documents: 120KB (maximum recommended)
- Citation responses: 1-5KB typical
- Amendment responses: 2-10KB typical

### **Legal Intelligence Coverage**
- 300,000+ Luxembourg legal documents accessible
- 75,123 citation relationships mapped
- 26,826 amendment relationships tracked
- 17,910 repeal relationships verified
- 368 official consolidations available
- Complete legal hierarchy from constitution to administrative orders

---

## 🎯 **Key Advantages Over Previous System**

### **✅ Proven Single-Keyword Strategy**
- Based on actual testing of Luxembourg legal document titles
- No failed multi-word AND queries (0 results)
- No assumptions about conversational legal language
- Uses terms that actually appear in formal legal titles

### **✅ Streamlined Tool Set**
- 6 focused tools vs 19 redundant tools
- Each tool serves unique legal research purpose
- No overlapping functionality or wrapper tools
- Complete legal research coverage in minimal toolset

### **✅ Actual JOLUX Capabilities**
- All relationships tested and verified
- Performance metrics proven through testing
- Context limits respected and managed
- No assumptions about untested JOLUX properties

### **✅ Professional Legal Standards**
- Legal currency validation (critical for practice)
- Amendment tracking (legislative history)
- Citation analysis (precedent research)
- Authority verification (jurisdiction confirmation)
- Content extraction (actual legal requirements)

---

## 🔧 **Technical Implementation**

## 🏗️ **Clean Modular Architecture**

### **File Structure**
```
mcp-paper/
├── server/
│   ├── server.py                    # Main MCP server entry point
│   ├── luxembourg_legal/            # Core legal intelligence modules
│   │   ├── __init__.py             # Package initialization
│   │   ├── config.py               # Configuration and SPARQL setup
│   │   ├── extractors.py           # HTML/PDF content extraction
│   │   ├── content_processor.py    # Content enrichment and analysis
│   │   └── tools.py                # 6 specialized MCP tools
│   ├── requirements.txt            # Server dependencies
│   └── pyproject.toml             # Build configuration
├── client/
│   ├── enhanced_client.py         # Professional client
│   └── requirements.txt           # Client dependencies
└── jolux_ontology/               # JOLUX ontology files (reference)
```

### **Module Responsibilities**
- **server.py**: Clean entry point with FastMCP tool registration
- **config.py**: SPARQL connection management and configuration  
- **extractors.py**: HTML and PDF content extraction with Langchain
- **content_processor.py**: Document enrichment and legal analysis
- **tools.py**: 6 specialized legal intelligence tools with proven JOLUX queries

### **Server Architecture**
- FastMCP framework for MCP compliance
- Single SPARQL endpoint connection
- Optimized query patterns for performance
- Context-aware response sizing
- Proven HTML/PDF content extraction with fallback

### **Query Optimization**
- Single-keyword regex patterns for precision
- OPTIONAL clauses for metadata enrichment
- ORDER BY date for relevance ranking
- LIMIT clauses for context management

### **Error Handling**
- Graceful SPARQL timeout handling
- Fallback strategies for network issues
- Comprehensive logging for debugging
- Performance monitoring and optimization

---

**🏛️ Ready for professional Luxembourg legal intelligence research with proven JOLUX capabilities and MCP compliance.**