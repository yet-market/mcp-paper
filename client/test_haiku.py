#!/usr/bin/env python3
"""
Test script for Claude 3.5 Haiku Anthropic API Luxembourg Legal Client
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from haiku_client import ClaudeHaikuClient

load_dotenv()


async def test_claude_haiku():
    """Test Claude 3.5 Haiku with Luxembourg legal questions."""
    
    print("🚀 Testing Claude 3.5 Haiku Anthropic API")
    print("=" * 50)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in .env file")
        return
    
    try:
        client = ClaudeHaikuClient()
        
        # Display model info
        model_info = client.get_model_info()
        print("\n📋 Model Information:")
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
        # Test questions focused on Luxembourg legal content
        test_questions = [
            "Comment créer une SARL au Luxembourg?",
            "Quelles sont les obligations fiscales d'une entreprise luxembourgeoise?",
            "Quels sont les droits des travailleurs au Luxembourg?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📋 Test {i}/3: {question}")
            print("-" * 60)
            
            try:
                result = await client.chat(question)
                
                print(f"🇱🇺 Réponse:")
                print("-" * 40)
                print(result["response"])
                
                # Show tool usage
                if result["tools_used"]:
                    print(f"\n🔧 Outils utilisés: {', '.join(result['tools_used'])}")
                    print(f"🔄 Itérations: {result['iterations']}")
                
                # Show cost information
                cost_info = result.get("cost_info", {})
                if cost_info:
                    print(f"\n💰 Coût:")
                    print(f"  Tokens d'entrée: {cost_info.get('input_tokens', 0)}")
                    print(f"  Tokens de sortie: {cost_info.get('output_tokens', 0)}")
                    print(f"  Coût estimé: ${cost_info.get('estimated_cost_usd', 0):.6f}")
                    print(f"  Temps de traitement: {cost_info.get('processing_time_ms', 0):.2f}ms")
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
            
            if i < len(test_questions):
                print("\n" + "=" * 60)
                await asyncio.sleep(1)
        
        # Show session summary
        cost_summary = client.get_cost_summary()
        print(f"\n🎯 Résumé de session:")
        print(f"  Requêtes totales: {cost_summary['total_queries']}")
        print(f"  Tokens d'entrée totaux: {cost_summary['total_input_tokens']}")
        print(f"  Tokens de sortie totaux: {cost_summary['total_output_tokens']}")
        print(f"  Coût total estimé: ${cost_summary['estimated_cost_usd']:.6f}")
        
        print(f"\n🎉 Test Claude 3.5 Haiku terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")


if __name__ == "__main__":
    asyncio.run(test_claude_haiku())