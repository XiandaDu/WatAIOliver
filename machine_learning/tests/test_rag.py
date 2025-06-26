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

def test_embedding():
    """Test embedding generation"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        return
    
    print(f"🔑 Using GOOGLE_API_KEY (length: {len(api_key)} characters)")
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain.schema import Document
        
        print("🧠 Testing Embeddings")
        
        # Create embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Create text splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=50
        )
        
        # Test text
        text = """
        Machine learning is a method of data analysis that automates analytical model building.
        It uses algorithms that iteratively learn from data, allowing computers to find hidden 
        insights without being explicitly programmed where to look.
        """
        
        # Split text
        docs = splitter.split_documents([Document(page_content=text)])
        print(f"📄 Split into {len(docs)} chunks")
        
        # Generate embeddings
        for i, doc in enumerate(docs):
            embedding = embeddings.embed_query(doc.page_content)
            print(f"✅ Chunk {i+1}: {len(embedding)}D embedding")
            print(f"   Text: {doc.page_content[:50]}...")
            print(f"   Vector: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
        
        print("🎉 Embeddings working!")
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")

def test_imports():
    """Test basic imports work"""
    try:
        print("🚀 Testing Imports")
        
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        print("✅ LangChain imports work")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Run: pip install -r rag_system/requirements.txt")
        return False

def main():
    print("🧪 Simple Embedding Test")
    print("=" * 30)
    
    if test_imports():
        test_embedding()
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    main() 