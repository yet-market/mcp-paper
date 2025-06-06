# 🏛️ Luxembourg Legal Intelligence MCP Server

**Professional Luxembourg legal research system with full JOLUX ontology intelligence**

![Legal Intelligence](https://img.shields.io/badge/Legal%20Intelligence-Professional%20Grade-blue)
![MCP Compliant](https://img.shields.io/badge/MCP-Fully%20Compliant-green)
![Luxembourg Law](https://img.shields.io/badge/Luxembourg-Legal%20System-red)
![JOLUX Powered](https://img.shields.io/badge/JOLUX-Full%20Ontology%20Power-orange)

---

## 🎯 **System Overview**

This is a **professional-grade Luxembourg legal intelligence system** built as an MCP (Model Context Protocol) server. It leverages the **complete power of the JOLUX ontology** with **18 specialized tools** to provide comprehensive legal research comparable to experienced Luxembourg lawyers.

### **Legal Intelligence Capabilities**
- **🔗 Citation Network Analysis** (75,123 citation relationships)
- **📝 Amendment Chain Tracking** (26,826+ modifications)
- **💰 Legal Currency Validation** (17,910 repeal relationships)
- **📋 Consolidated Version Discovery** (368 consolidations)
- **🌍 Multilingual Support** (238,518 language versions)
- **🔍 Multi-field legal search** across titles, relationships, and authorities
- **📅 Temporal legal analysis** for currency validation
- **⚖️ Legal authority hierarchy** ranking (BaseAct > Act > Regulation)
- **📄 Luxembourg-specific content extraction** (HTML/PDF parsing)
- **🇪🇺 EU law integration** with directive transposition tracking

---

## 🚀 **Quick Start**

### **1. Start the Legal Intelligence Server**
```bash
cd server
python server.py --endpoint https://data.legilux.public.lu/sparqlendpoint
```

### **2. Test with Enhanced Client**
```bash
cd client
python enhanced_client.py
```

### **3. Use with Claude Desktop (MCP)**
Add to your Claude Desktop MCP configuration:
```json
{
  "mcpServers": {
    "luxembourg-legal": {
      "command": "python",
      "args": ["server/server.py", "--endpoint", "https://data.legilux.public.lu/sparqlendpoint"],
      "cwd": "/path/to/mcp-paper"
    }
  }
}
```

---

## 🔧 **Legal Intelligence MCP Tools (18 Professional Tools)**

### **🔍 Smart Search Tool** 🆕

#### **`smart_legal_search`**
- **Purpose**: AI-driven keyword search with smart multi-word handling
- **Features**: Automatic keyword extraction and OR logic, handles complex legal queries
- **MCP Compliant**: AI chooses precise legal keywords, tool provides data
- **Output**: Documents with relevance scoring and keyword matching

### **🏛️ Core Legal Research Tools**

#### **`identify_legal_domain`**
- **Purpose**: Legal domain identification with enhanced metadata
- **Input**: Legal question text
- **Output**: Domain + keywords + document types + relevant authorities

#### **`multi_field_legal_search`**
- **Purpose**: Search across titles, relationships, and authorities simultaneously  
- **JOLUX Features**: `jolux:title` + `jolux:basedOn` + `jolux:responsibilityOf`
- **Output**: 50-500 documents with comprehensive metadata

#### **`discover_legal_relationships`**
- **Purpose**: Find amendment chains, implementations, and legal dependencies
- **JOLUX Features**: `jolux:basedOn+` (transitive), `jolux:isMemberOf`
- **Output**: Complete legal relationship network

#### **`temporal_legal_analysis`**
- **Purpose**: Analyze legal currency and temporal context
- **JOLUX Features**: `jolux:dateDocument`, `jolux:publicationDate`, `jolux:dateEntryInForce`
- **Output**: Timeline analysis + currency assessment

#### **`assess_legal_authority`**
- **Purpose**: Rank by JOLUX hierarchy, authority, and relevance
- **JOLUX Features**: Document type hierarchy + `jolux:responsibilityOf`
- **Output**: Authoritative documents with legal priority scores

#### **`extract_document_content`**
- **Purpose**: Extract actual legal text with Luxembourg-specific parsing
- **Features**: HTML/PDF content extraction + legal structure analysis
- **Output**: Full legal content with metadata

### **🔗 Citation Intelligence Tools** 🆕

#### **`analyze_citation_network`**
- **Purpose**: Analyze complete citation network (75K+ relationships)
- **JOLUX Features**: `jolux:cites` (75,123 relations)
- **Output**: Citation network with precedent analysis

#### **`find_citing_documents`**
- **Purpose**: Find documents that cite a specific law
- **Output**: Legal documents that reference/rely on the target law

#### **`find_cited_documents`**
- **Purpose**: Find documents cited by a specific law
- **Output**: Legal foundation and authorities referenced

### **📝 Amendment Intelligence Tools** 🆕

#### **`analyze_amendment_chain`**
- **Purpose**: Complete amendment history analysis
- **JOLUX Features**: `jolux:modifies/modifiedBy` (26K+ modifications)
- **Output**: Chronological amendment timeline + activity analysis

#### **`find_latest_amendments`**
- **Purpose**: Find most recent amendments to a law
- **Output**: Recent modifications affecting current legal status

### **💰 Legal Currency Tools** 🆕

#### **`check_legal_currency`**
- **Purpose**: Verify if document is still legally current
- **JOLUX Features**: `jolux:repeals` (17,910 repeal relationships)
- **Output**: CURRENT/REPEALED status with details

#### **`analyze_replacement_chain`**
- **Purpose**: Analyze complete repeal/replacement relationships
- **Output**: What this law repeals vs. what repeals it

### **📋 Version Intelligence Tools** 🆕

#### **`find_consolidated_versions`**
- **Purpose**: Find official consolidated versions
- **JOLUX Features**: `jolux:consolidates` (368 consolidations)
- **Output**: Current effective consolidated text versions

#### **`find_multilingual_versions`**
- **Purpose**: Find different language versions
- **JOLUX Features**: `jolux:language` (238,518 language versions)
- **Output**: French, German, English versions available

#### **`get_current_effective_version`**
- **Purpose**: Determine most current effective version
- **Output**: Recommended version for legal practice

### **📋 Workflow Intelligence Tool**

#### **`get_enhanced_workflow_guidance`**
- **Purpose**: Professional workflow guidance
- **Output**: 3 specialized workflows for different research needs

---

## ⚖️ **Professional Legal Intelligence Workflows**

### **Workflow 1: Comprehensive Legal Research**
```
Question: "Comment créer une SARL au Luxembourg?"

1. identify_legal_domain → Droit Commercial
2. multi_field_legal_search → 85+ documents
3. analyze_citation_network → Legal precedent network
4. analyze_amendment_chain → SARL law evolution 2016-2025
5. check_legal_currency → Validity confirmation
6. find_consolidated_versions → Official current text
7. extract_document_content → Articles 175-218 + procedures
```

### **Workflow 2: Legal Relationship Intelligence**
```
Focus: Understanding legal networks and dependencies

1. multi_field_legal_search → Base documents
2. analyze_citation_network → Complete citation web
3. find_citing_documents → Who references these laws
4. find_cited_documents → Legal foundations
5. analyze_amendment_chain → Legislative evolution
6. analyze_replacement_chain → Repeal/replacement history
```

### **Workflow 3: Legal Currency & Version Analysis**
```
Focus: Current, valid legal text

1. multi_field_legal_search → Relevant documents
2. check_legal_currency → Validity status
3. find_latest_amendments → Recent changes
4. find_consolidated_versions → Official versions
5. find_multilingual_versions → Language options
6. get_current_effective_version → Final recommendation
```

---

## 📊 **Legal Intelligence Comparison**

| Capability | Before | Legal Intelligence System |
|------------|--------|---------------------------|
| **MCP Tools** | 6 basic | 18 specialized |
| **Documents Found** | 5-20 | 50-500+ |
| **Search Fields** | Title only | Title + Relationships + Authority |
| **Citation Analysis** | None | 75,123 citation relationships |
| **Amendment Tracking** | None | 26,826 modifications tracked |
| **Legal Currency** | None | 17,910 repeal relationships |
| **Consolidation** | None | 368 official consolidated versions |
| **Multilingual** | None | 238,518 language versions |
| **Legal Hierarchy** | Basic | BaseAct > Act > Regulation > Admin |
| **Authority Ranking** | None | Parliament > Ministry > Administration |
| **Professional Grade** | Demo | Law firm intelligence standard |

---

## 🎯 **JOLUX Ontology Utilization**

### **Full Ontology Power Exploited**
- **Citation Network**: `jolux:cites` (75,123 relationships) 
- **Amendment Chains**: `jolux:modifies/modifiedBy` (26,826+ modifications)
- **Legal Currency**: `jolux:repeals` (17,910 repeal relationships)
- **Consolidation**: `jolux:consolidates` (368 consolidations)
- **Multilingual**: `jolux:language` (238,518 versions)
- **Multi-field search**: `jolux:title` + `jolux:basedOn` + `jolux:responsibilityOf`
- **Legal relationships**: `jolux:basedOn+` transitive queries
- **Authority hierarchy**: Document type + `jolux:responsibilityOf` ranking
- **Temporal analysis**: Multi-date properties for currency validation
- **Document structure**: `jolux:isRealizedBy` for expression linking

### **Professional Legal Intelligence Achieved**
- ✅ **Citation network analysis** → Legal precedent discovery
- ✅ **Amendment chain tracking** → Complete legislative evolution
- ✅ **Legal currency validation** → Current law verification
- ✅ **Consolidated version discovery** → Official text access
- ✅ **Multilingual support** → French/German/English versions
- ✅ **EU law integration** → Directive transposition tracking
- ✅ **Authority hierarchy** → Parliament > Ministry > Administration
- ✅ **Comprehensive search** → 500+ document discovery

---

## 📋 **MCP Philosophy Compliance**

### **✅ Fully Compliant Implementation**

#### **Tools Provide Data, AI Synthesizes**
- Each tool returns structured legal intelligence data only
- No interpretation or analysis in tools
- AI combines tool outputs into comprehensive legal analysis

#### **Composable Workflow**
- 18 independent, specialized tools
- Can be used in any combination/order
- Each tool has single responsibility
- AI discovers optimal research patterns

#### **Rich Legal Data Exchange**
- Comprehensive legal metadata in all responses
- Structured citation networks and amendment chains
- Professional-grade legal intelligence quality

---

## 📚 **Documentation**

### **Technical Documentation**
- **[JOLUX SPARQL Usage Guide](JOLUX_SPARQL_USAGE_GUIDE.md)** - Complete SPARQL endpoint usage with new patterns
- **[Enhanced System Summary](ENHANCED_SYSTEM_SUMMARY.md)** - Legal intelligence transformation overview
- **[JOLUX Endpoint Capabilities](JOLUX_ENDPOINT_CAPABILITIES.md)** - Full endpoint analysis
- **[MCP Compliance Verification](MCP_COMPLIANCE_VERIFICATION.md)** - MCP philosophy compliance

---

## 🛠️ **Installation & Setup**

### **Prerequisites**
```bash
Python 3.8+
pip install -r server/requirements.txt
pip install -r client/requirements.txt
```

### **Environment Variables**
```bash
# For client testing
ANTHROPIC_API_KEY=your_api_key_here
MCP_SERVER_URL=http://localhost:8080  # or remote server
```

### **Server Configuration**
```bash
# Start with JOLUX endpoint
python server/server.py --endpoint https://data.legilux.public.lu/sparqlendpoint

# Available options:
--endpoint      SPARQL endpoint URL (required)
--transport     Transport type (stdio|streamable-http) 
--host          Host for HTTP transport (default: localhost)
--port          Port for HTTP transport (default: 8080)
```

---

## 🚀 **Production Deployment**

### **For Claude Desktop**
1. Add server to MCP configuration
2. Start Claude Desktop
3. Ask Luxembourg legal questions
4. System automatically uses all 18 legal intelligence tools

### **For Custom Applications** 
1. Start MCP server with JOLUX endpoint
2. Connect via MCP client library
3. Use tools in professional legal intelligence workflows
4. AI synthesizes comprehensive legal analysis

### **Expected Results**
- **50-500 relevant documents** per legal question
- **Citation network analysis** showing legal precedents
- **Amendment chain discovery** with complete evolution
- **Legal currency validation** ensuring current law
- **Consolidated version access** to official text
- **Multilingual support** for Luxembourg's language diversity
- **EU law integration** with directive transposition tracking
- **Professional legal intelligence** with proper citations and hierarchy

---

## 🎉 **Success Metrics**

**For SARL research query, system delivers:**
- ✅ 50-100 relevant documents discovered
- ✅ Complete citation network showing legal precedents
- ✅ Amendment chains from 1915 → 2016 → 2025 tracked
- ✅ Legal currency validated (current/repealed status)
- ✅ Consolidated versions identified for current practice
- ✅ EU directive relationships discovered
- ✅ Multilingual versions found (French/German/English)
- ✅ Complete procedural guidance extracted

**Professional legal intelligence standard achieved through full JOLUX ontology utilization.**

---

## 📞 **Support & Contributing**

### **Issues & Feedback**
- Report issues via GitHub Issues
- Enhancement requests welcome
- Professional legal feedback valued

### **Architecture Notes**
- Built with FastMCP for MCP compliance
- Full JOLUX ontology integration for Luxembourg law specificity
- Professional legal intelligence methodology
- Complete citation and amendment analysis capability
- EU law integration capability

---

**🏛️ Ready for professional Luxembourg legal intelligence research!**