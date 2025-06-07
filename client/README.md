# Luxembourg Legal Intelligence Client

Simple client for the 6-tool professional legal research system.

## Usage

```bash
cd client
python enhanced_client.py
```

## Requirements

- Python 3.8+
- ANTHROPIC_API_KEY environment variable
- MCP server running on localhost:8080 (or set MCP_SERVER_URL)

## Tools Available

1. **search_documents** - Single-keyword precision search
2. **get_citations** - Citation network analysis  
3. **get_amendments** - Legal evolution tracking
4. **check_legal_status** - Legal currency validation
5. **get_relationships** - Legal hierarchy discovery
6. **extract_content** - Legal text extraction