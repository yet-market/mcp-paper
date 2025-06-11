#!/bin/bash

# Demo script showing different ways to use the Luxembourg Legal Assistant

echo "🏛️  LUXEMBOURG LEGAL ASSISTANT - DEMO COMMANDS"
echo "=============================================="
echo ""

echo "📋 Available Commands:"
echo ""

echo "1. Quick Questions (Wrapper Script):"
echo "   ./ask_question.sh \"Your question here\""
echo "   ./ask_question.sh \"Your question here\" \"provider\""
echo ""

echo "2. Interactive Mode:"
echo "   source client_venv/bin/activate"
echo "   python interactive_client.py"
echo ""

echo "3. Command Line with Options:"
echo "   source client_venv/bin/activate"
echo "   python interactive_client.py --question \"Your question\" --provider anthropic"
echo ""

echo "🤖 Available Providers:"
echo "   • anthropic (Claude) - Most accurate, takes 10-20 seconds"
echo "   • openai (GPT-4.1)   - Fast and cheap, takes 2-5 seconds"
echo "   • groq (Llama)       - Fastest, takes 1-3 seconds"
echo ""

echo "📝 Example Questions:"
echo "   • \"Quelles sont les étapes pour créer une SARL au Luxembourg?\""
echo "   • \"Capital minimum requis pour une SA?\""
echo "   • \"Obligations comptables d'une entreprise?\""
echo "   • \"Durée du préavis de licenciement?\""
echo "   • \"Calcul de l'impôt sur les sociétés?\""
echo ""

echo "🚀 Quick Test Commands:"
echo ""
echo "# Test with OpenAI (fastest)"
echo "./ask_question.sh \"Test rapide\" \"openai\""
echo ""
echo "# Test with Claude (most accurate)"  
echo "./ask_question.sh \"Analyse détaillée\" \"anthropic\""
echo ""
echo "# Test with Groq (good balance)"
echo "./ask_question.sh \"Question simple\" \"groq\""
echo ""

echo "📖 Full Documentation: See CLIENT_USAGE.md"
echo ""
echo "💡 Tip: Start with OpenAI for quick tests, use Claude for detailed analysis!"