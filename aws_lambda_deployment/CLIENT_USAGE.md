# 🏛️ Luxembourg Legal Assistant - Interactive Client Usage Guide

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
# Create virtual environment
python3 -m venv client_venv

# Activate virtual environment
source client_venv/bin/activate

# Install dependencies
pip install requests
```

### 2. Ask Questions

**Method 1: Command Line (Quick)**
```bash
# Simple question
./ask_question.sh "Comment créer une SARL au Luxembourg?"

# Specify provider
./ask_question.sh "Legal question here" "anthropic"
./ask_question.sh "Legal question here" "openai"  
./ask_question.sh "Legal question here" "groq"
```

**Method 2: Python Script (Advanced)**
```bash
# Activate venv first
source client_venv/bin/activate

# Basic usage
python interactive_client.py --question "Your legal question"

# With provider selection
python interactive_client.py --question "Your question" --provider anthropic

# Interactive mode (will prompt for question)
python interactive_client.py
```

## 🤖 AI Providers

| Provider | Speed | Quality | Cost | Best For |
|----------|-------|---------|------|----------|
| **anthropic** (Claude) | Moderate | Highest | Medium | Complex legal analysis |
| **openai** (GPT-4.1-mini) | Fast | High | Lowest | Quick questions |
| **groq** (Llama) | Fastest | Good | Low | Simple queries |

## 📋 Command Options

```bash
python interactive_client.py [OPTIONS]

Options:
  --question TEXT        Question to ask (if not provided, will prompt)
  --provider CHOICE      AI provider: anthropic, openai, groq (default: anthropic)
  --api-url TEXT         API Gateway URL (auto-configured)
  --api-key TEXT         API Key (auto-configured)
  --company-id TEXT      Company ID (default: default)
  --user-id TEXT         User ID (default: default)
  --max-wait INTEGER     Maximum wait time in minutes (default: 10)
  --help                 Show help message
```

## 🎯 Usage Examples

### A) Asynchronous Multi-Tool Research (ask_question)

```bash
# Corporate law
./ask_question.sh "Quelles sont les obligations d'un gérant de SARL?"

# Employment law
./ask_question.sh "Quelle est la durée maximale du travail au Luxembourg?"

# Tax law
./ask_question.sh "Comment calculer l'impôt sur les sociétés?"
```

### B) Single-Tool Invocations (tool_cli_client)

```bash
# Run the tool CLI to pick and execute one MCP tool
python tool_cli_client.py

# Example manual invocation:
#   (choose extract_content when prompted)
python tool_cli_client.py
```

```bash
# Long analysis with Claude
python interactive_client.py \
  --question "Analysez les implications fiscales d'une fusion-acquisition" \
  --provider anthropic \
  --max-wait 15

# Quick answer with GPT-4
python interactive_client.py \
  --question "Délai de prescription civile au Luxembourg?" \
  --provider openai \
  --max-wait 5

# Fast response with Groq
python interactive_client.py \
  --question "Définition juridique d'une SARL" \
  --provider groq \
  --max-wait 3
```

## 📊 Real-time Progress Monitoring

The client shows live progress updates:

```
📡 Monitoring job progress...
[15:28:11] [████░░░░░░░░░░░░░░░░] 24% - mcp_tools_execution
           📋 Executing MCP tools - iteration 1/15
           🔧 Iteration 1, Tools: 0
           🤖 AI calls: 2, Tokens: 1547

[15:28:33] [████████████████████] 100% - completed
           📋 Enhanced legal research completed with structured output
```

## 📖 Output Structure

The client provides comprehensive results:

- **⚡ Performance**: Processing time, tools executed, iterations
- **🤖 Model Info**: Provider, model name, settings
- **📖 Legal Analysis**: Summary, key points, detailed analysis
- **📚 Legal Sources**: Primary laws, supporting regulations
- **🔗 Citations Network**: Citation relationships and strength
- **⚖️ Legal Validity**: Current status and confidence level

## 🛠️ Troubleshooting

### Virtual Environment Issues
```bash
# If venv is missing
python3 -m venv client_venv
source client_venv/bin/activate
pip install requests
```

### Permission Errors
```bash
# Make scripts executable
chmod +x ask_question.sh
chmod +x interactive_client.py
```

### API Connection Issues
```bash
# Test API connectivity
curl https://h9791kaj7h.execute-api.eu-west-2.amazonaws.com/prod/health
```

### Timeout Issues
```bash
# Increase wait time for complex questions
python interactive_client.py --question "Complex question" --max-wait 20
```

## 🔧 Configuration

Default settings are pre-configured, but you can customize:

```bash
# Custom API endpoint
export LEGAL_API_URL="your-custom-endpoint"

# Custom API key
export LEGAL_API_KEY="your-custom-key"

# Use in script
python interactive_client.py --api-url "$LEGAL_API_URL" --api-key "$LEGAL_API_KEY"
```

## 📝 Examples by Topic

### Corporate Law
```bash
./ask_question.sh "Procédure de dissolution d'une SA au Luxembourg" anthropic
./ask_question.sh "Capital minimum pour créer une SARL" openai
./ask_question.sh "Obligations comptables des entreprises" groq
```

### Employment Law
```bash
./ask_question.sh "Durée du préavis de licenciement" anthropic
./ask_question.sh "Calcul des congés payés" openai
./ask_question.sh "Contrat de travail temporaire" groq
```

### Tax Law
```bash
./ask_question.sh "Taux d'imposition des dividendes" anthropic
./ask_question.sh "Déductions fiscales autorisées" openai
./ask_question.sh "TVA sur les services digitaux" groq
```

## 💡 Tips for Best Results

1. **Be Specific**: "SARL capital requirements" vs "company rules"
2. **Use French**: Questions in French get better results for Luxembourg law
3. **Choose Right Provider**: 
   - Complex analysis → Claude (anthropic)
   - Quick facts → GPT-4 (openai)
   - Simple definitions → Llama (groq)
4. **Allow Time**: Legal analysis can take 2-5 minutes for thorough results

## 🎯 Interactive Mode

For exploratory research, use interactive mode:

```bash
python interactive_client.py

# Will prompt:
# Please enter your legal question:
# ❓ Question: [Type your question here]
```

This gives you the full interactive experience with provider selection and real-time monitoring.