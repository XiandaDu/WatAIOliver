#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add rag_system to path  
rag_path = str(Path(__file__).parent.parent / "rag_system")
sys.path.insert(0, rag_path)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / "rag_system" / ".env"
load_dotenv(env_path)


def test_embedding_client():
    """Test the modular embedding client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        return False
    
    print(f"🔑 Using GOOGLE_API_KEY (length: {len(api_key)} characters)")
    
    try:
        from embedding.google_embedding_client import GoogleEmbeddingClient
        from langchain.schema import Document
        
        print("🧠 Testing Embedding Client")
        
        # Create embedding client
        embedding_client = GoogleEmbeddingClient(api_key=api_key)
        
        # Test document
        doc = Document(page_content="""
        Machine learning is a method of data analysis that automates analytical model building.
        It uses algorithms that iteratively learn from data, allowing computers to find hidden 
        insights without being explicitly programmed where to look.
        """)
        
        # Test splitting
        chunks = embedding_client.split_documents([doc])
        print(f"📄 Split into {len(chunks)} chunks")
        
        # Test embedding
        embedding = embedding_client.embed_query("What is machine learning?")
        print(f"✅ Query embedding: {len(embedding)}D vector")
        print(f"   Vector: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding client test failed: {e}")
        return False


def test_llm_client():
    """Test the modular LLM client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found")
        return False
    
    try:
        from llm_clients.gemini_client import GeminiClient
        
        print("🤖 Testing LLM Client")
        
        # Create LLM client
        llm_client = GeminiClient(api_key=api_key)
        
        # Test generation
        response = llm_client.generate("What is 2+2?")
        print(f"✅ LLM Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False


def test_imports():
    """Test all modular imports work."""
    try:
        print("🚀 Testing Modular Imports")
        
        from embedding.google_embedding_client import GoogleEmbeddingClient
        from llm_clients.gemini_client import GeminiClient
        from vector_db.supabase_client import SupabaseVectorClient
        from services.rag_service import RAGService
        print("✅ All modular imports work")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Run: pip install -r rag_system/requirements.txt")
        return False


def main():
    print("🧪 Modular RAG System Test")
    print("=" * 35)
    
    if not test_imports():
        return
    
    # Test individual components
    embedding_ok = test_embedding_client()
    llm_ok = test_llm_client()
    
    print("\n📊 Test Results:")
    print(f"  Embedding Client: {'✅ PASS' if embedding_ok else '❌ FAIL'}")
    print(f"  LLM Client: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    print(f"  Vector Client: ⏭️ SKIP (requires Supabase)")
    
    if embedding_ok and llm_ok:
        print("\n🎉 Modular system working!")
    else:
        print("\n⚠️ Some components failed")
    
    print("\n✨ Test complete!")


if __name__ == "__main__":
    main() 