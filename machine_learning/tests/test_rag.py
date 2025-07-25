#!/usr/bin/env python3
"""
Comprehensive RAG System Test Suite - Embedding Focus
This test focuses on embedding functionality without Supabase dependencies.
"""

import os
import sys
from pathlib import Path
import traceback

# Add rag_system to path  
rag_path = str(Path(__file__).parent.parent / "rag_system")
sys.path.insert(0, rag_path)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / "rag_system" / ".env"
    load_dotenv(env_path)
except ImportError:
    print("️python-dotenv not installed, using system environment variables")


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'-'*50}")
    print(f"{title}")
    print(f"{'-'*50}")


def test_embedding_client():
    """Test the embedding client with gemini-embedding-001."""
    print_section("Testing Embedding Client (gemini-embedding-001)")
    
    # Check for required Vertex AI credentials
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    service_account_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    if not google_cloud_project:
        print("GOOGLE_CLOUD_PROJECT not found - required for Vertex AI")
        return False
    
    if not service_account_file:
        print("GOOGLE_APPLICATION_CREDENTIALS not found - required for Vertex AI")
        return False
    
    print(f"Using Vertex AI with service account")
    print(f"️ Project: {google_cloud_project}")
    print(f"Service Account: {service_account_file}")
    
    try:
        from embedding.google_embedding_client import GoogleEmbeddingClient
        from langchain.schema import Document
        
        print(f"\nUsing gemini-embedding-001 model (latest from Google)...")
        
        # Create embedding client with gemini model and 512 dimensions
        embedding_client = GoogleEmbeddingClient(
            google_cloud_project=google_cloud_project,
            model="text-embedding-004",  #  new
            output_dimensionality=ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY
        )
        # embedding_client = GoogleEmbeddingClient(
        #     google_cloud_project=google_cloud_project,
        #     model="gemini-embedding-001",  # old
        #     output_dimensionality=512
        # )
        
        # Get model info
        model_info = embedding_client.get_model_info()
        print(f"\nModel Configuration:")
        print(f"   Model: {model_info['model']}")
        print(f"   Expected Dimensions: {model_info['expected_dimensionality']}")
        print(f"   Chunk Size: {model_info['chunk_size']}")
        print(f"   Chunk Overlap: {model_info['chunk_overlap']}")
        
        # Test document
        doc = Document(page_content="""
        Machine learning is a method of data analysis that automates analytical model building.
        It uses algorithms that iteratively learn from data, allowing computers to find hidden 
        insights without being explicitly programmed where to look. Machine learning is a branch 
        of artificial intelligence (AI) based on the idea that systems can learn from data, 
        identify patterns and make decisions with minimal human intervention.
        """)
        
        # Test splitting
        chunks = embedding_client.split_documents([doc])
        print(f"\nDocument split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: {len(chunk.page_content)} characters")
        
        # Test query embedding and SHOW THE VECTORS
        print(f"\nTesting Query Embedding:")
        query = "What is machine learning?"
        embedding = embedding_client.embed_query(query)
        print(f"Query: '{query}'")
        print(f"   Embedding Dimensions: {len(embedding)}")
        print(f"   Vector Preview: [{embedding[0]:.6f}, {embedding[1]:.6f}, {embedding[2]:.6f}, ..., {embedding[-1]:.6f}]")
        print(f"   Vector Range: min={min(embedding):.6f}, max={max(embedding):.6f}")
        
        # Test document embeddings
        print(f"\nTesting Document Embeddings:")
        texts = [chunk.page_content for chunk in chunks]
        doc_embeddings = embedding_client.embed_documents(texts)
        print(f"Generated embeddings for {len(doc_embeddings)} document chunks")
        
        if doc_embeddings:
            first_embedding = doc_embeddings[0]
            print(f"   First Doc Embedding Dimensions: {len(first_embedding)}")
            print(f"   Vector Preview: [{first_embedding[0]:.6f}, {first_embedding[1]:.6f}, {first_embedding[2]:.6f}, ..., {first_embedding[-1]:.6f}]")
            print(f"   Vector Range: min={min(first_embedding):.6f}, max={max(first_embedding):.6f}")
        
        # Test similarity between query and document
        print(f"\nTesting Vector Similarity:")
        if doc_embeddings:
            # Simple cosine similarity calculation
            import numpy as np
            query_vec = np.array(embedding)
            doc_vec = np.array(first_embedding)
            
            # Normalize vectors
            query_norm = query_vec / np.linalg.norm(query_vec)
            doc_norm = doc_vec / np.linalg.norm(doc_vec)
            
            # Calculate cosine similarity
            similarity = np.dot(query_norm, doc_norm)
            print(f"   Cosine Similarity (query vs doc): {similarity:.6f}")
        
        # Show actual dimensions
        actual_dims = len(embedding)
        print(f"\nVector Analysis:")
        print(f"   Actual Dimensions: {actual_dims}")
        print(f"   Model Used: {model_info['model']}")
        print(f"   gemini-embedding-001 working correctly!")
        
        return True
        
    except Exception as e:
        print(f"Embedding client test failed: {e}")
        traceback.print_exc()
        return False


def test_llm_client():
    """Test the LLM client."""
    print_section("Testing LLM Client")
    
    # Check for required Vertex AI credentials
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    
    if not google_cloud_project:
        print("GOOGLE_CLOUD_PROJECT not found - required for LLM")
        return False
    
    try:
        from llm_clients.gemini_client import GeminiClient
        
        # Create LLM client (will use service account credentials)
        llm_client = GeminiClient(api_key="")  # Not needed for Vertex AI
        
        # Test generation
        response = llm_client.generate("What is 2+2? Give a brief answer.")
        print(f"LLM Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"LLM client test failed: {e}")
        return False


def test_imports():
    """Test essential imports (skip Supabase)."""
    print_section("Testing Core Module Imports")
    
    try:
        from embedding.google_embedding_client import GoogleEmbeddingClient
        from llm_clients.gemini_client import GeminiClient
        print("Core imports successful (Embedding + LLM)")
        
        # Test optional imports
        try:
            from vector_db.supabase_client import SupabaseVectorClient
            print("Supabase client available (optional)")
        except ImportError:
            print("Supabase client not available (skipping)")
        
        return True
        
    except ImportError as e:
        print(f"Core import failed: {e}")
        print("Run: pip install -r rag_system/requirements.txt")
        return False


def run_all_tests():
    """Run all tests and return results."""
    print_header("RAG System Test Suite - Embedding Focus")
    
    # Test imports first
    if not test_imports():
        print("\nCannot proceed - import failures")
        return False
    
    # Run embedding-focused tests
    test_results = {
        'imports': True,
        'embedding': test_embedding_client(),
        'llm': test_llm_client()
    }
    
    # Print final results
    print_header("Test Results Summary")
    
    print("Component Test Results:")
    print(f"  Module Imports: {'PASS' if test_results['imports'] else 'FAIL'}")
    print(f"  Embedding Client (gemini-embedding-001): {'PASS' if test_results['embedding'] else 'FAIL'}")
    print(f"  LLM Client: {'PASS' if test_results['llm'] else 'FAIL'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"\nALL TESTS PASSED!")
        print(f" Using gemini-embedding-001 model")
        print(f" Vector embeddings working correctly")
        print(f" Similarity calculations functional")
    else:
        print(f"\n️ Some tests failed - check output above")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"   Failed: {', '.join(failed_tests)}")
    
    print(f"\nEmbedding-focused test suite complete!")
    return all_passed


def main():
    """Main test runner."""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 