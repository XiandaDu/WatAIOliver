#!/usr/bin/env python3
"""
RAG System - Full Embedding Vector Showcase
Shows the complete 768-dimensional embedding vectors
"""

import os
import sys
import json
from pathlib import Path

# Get API key from environment
if not os.getenv("GEMINI_API_KEY"):
    print("❌ Error: GEMINI_API_KEY environment variable not set")
    print("Please set your API key: export GEMINI_API_KEY='your_api_key_here'")
    sys.exit(1)

# Add the rag_system to Python path
sys.path.append(str(Path(__file__).parent.parent / "rag_system"))

def main():
    """Show complete embedding vectors"""
    
    try:
        from embedding.gemini_embedding_client import GeminiEmbeddingClient
        from app.config import get_settings
        
        settings = get_settings()
        client = GeminiEmbeddingClient(api_key=settings.gemini_api_key)
        
        # Test texts
        test_texts = [
            "Machine learning transforms data into insights",
            "What is artificial intelligence?",
            "Neural networks process information like the brain"
        ]
        
        output_file = "full_embeddings_output.txt"
        
        with open(output_file, "w") as f:
            print("🧠 Complete Embedding Vectors Showcase", file=f)
            print("=" * 60, file=f)
            print(f"Model: {client.model}", file=f)
            print(f"Dimensions: {client.get_embedding_dimension()}", file=f)
            print("=" * 60, file=f)
            
            for i, text in enumerate(test_texts):
                print(f"\n📝 Text {i+1}: {text}", file=f)
                print("-" * 40, file=f)
                
                # Generate embedding
                embedding = client.embed_query(text)
                
                print(f"✅ Generated {len(embedding)}-dimensional vector:", file=f)
                print(f"📊 Range: [{min(embedding):.6f}, {max(embedding):.6f}]", file=f)
                print(f"🎯 Vector norm: {sum(x*x for x in embedding)**0.5:.6f}", file=f)
                
                # Show full vector in chunks for readability
                print(f"\n🔢 Complete Vector (768 dimensions):", file=f)
                for j in range(0, len(embedding), 10):
                    chunk = embedding[j:j+10]
                    chunk_str = ", ".join(f"{x:.8f}" for x in chunk)
                    print(f"   [{j:3d}-{min(j+9, len(embedding)-1):3d}]: [{chunk_str}]", file=f)
                
                # Also save as JSON for easy parsing
                json_file = f"embedding_{i+1}_vector.json"
                with open(json_file, "w") as jf:
                    json.dump({
                        "text": text,
                        "model": client.model,
                        "dimensions": len(embedding),
                        "vector": embedding,
                        "norm": sum(x*x for x in embedding)**0.5,
                        "range": [min(embedding), max(embedding)]
                    }, jf, indent=2)
                
                print(f"💾 Full vector saved to: {json_file}", file=f)
            
            # Show similarity matrix
            print(f"\n🔗 Similarity Matrix:", file=f)
            print("-" * 40, file=f)
            
            embeddings = [client.embed_query(text) for text in test_texts]
            
            import math
            def cosine_similarity(v1, v2):
                dot = sum(a*b for a,b in zip(v1, v2))
                norm1 = math.sqrt(sum(a*a for a in v1))
                norm2 = math.sqrt(sum(a*a for a in v2))
                return dot / (norm1 * norm2)
            
            for i in range(len(test_texts)):
                for j in range(len(test_texts)):
                    sim = cosine_similarity(embeddings[i], embeddings[j])
                    print(f"   Text {i+1} ↔ Text {j+1}: {sim:.6f}", file=f)
            
            print(f"\n🎉 Complete embedding analysis saved!", file=f)
            print(f"📋 Check the JSON files for machine-readable vectors", file=f)
        
        print(f"🎉 Full embedding analysis complete!")
        print(f"📋 Results in: {output_file}")
        print(f"💾 Individual vectors saved as JSON files")
        print(f"🔍 You now have the complete 768-dimensional vectors!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 