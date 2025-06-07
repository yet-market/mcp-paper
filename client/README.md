# Luxembourg Legal Intelligence Client

Professional client for the 6-tool legal research system with multiple AI model options.

## Available Clients

### 1. Claude Client (Recommended)
```bash
cd client
source venv/bin/activate
export ANTHROPIC_API_KEY="your-key-here"
python claude_client.py
```

### 2. Llama Client (Experimental with URI validation)
```bash
cd client
source venv/bin/activate
export GROQ_API_KEY="your-groq-key-here"
python llama_client.py
```

### 3. Enhanced Client (Flexible - both models)
```bash
cd client
source venv/bin/activate
export MODEL_PROVIDER="anthropic"  # or "groq"
python enhanced_client.py
```

## Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` - For Claude models
- `GROQ_API_KEY` - For Groq/Llama models

**Optional:**
- `MODEL_PROVIDER` - "anthropic" (default) or "groq"
- `MCP_SERVER_URL` - Server URL (default: http://localhost:8080)

## Client Comparison

| Client | Model | Reliability | Tool Usage | Best For |
|--------|-------|-------------|------------|----------|
| claude_client.py | Claude 3.5 Sonnet | ✅ Excellent | ✅ All 6 tools | Professional legal research |
| llama_client.py | Llama 3.3 70B | ⚠️ Experimental | ❌ Limited (URI validation) | Testing & development |
| enhanced_client.py | Both models | 🔄 Variable | 🔄 Depends on model | Comparison testing |

## Tools Available

1. **search_documents** - Single-keyword precision search
2. **get_citations** - Citation network analysis  
3. **get_amendments** - Legal evolution tracking
4. **check_legal_status** - Legal currency validation
5. **get_relationships** - Legal hierarchy discovery
6. **extract_content** - Legal text extraction

## Usage Examples

### Switch to Groq for faster responses:
```bash
export MODEL_PROVIDER="groq"
python enhanced_client.py
```

### Use Anthropic for highest quality:
```bash
export MODEL_PROVIDER="anthropic"  # or unset
python enhanced_client.py
```