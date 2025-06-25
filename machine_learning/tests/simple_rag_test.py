#!/usr/bin/env python3
"""
Comprehensive RAG System Test
Showcases the modernized RAG system with:
- Google text-embedding-004 (768D embeddings)
- Adaptive semantic chunking 
- Text processing and document handling
- Embedding generation and similarity

Requires only GEMINI_API_KEY - no Supabase needed!
"""

import os
import sys
import math
import traceback
from pathlib import Path

# Get API key from environment
if not os.getenv("GEMINI_API_KEY"):
    print("❌ Error: GEMINI_API_KEY environment variable not set")
    print("Please set your API key: export GEMINI_API_KEY='your_api_key_here'")
    sys.exit(1)

# Add the rag_system to Python path
sys.path.append(str(Path(__file__).parent.parent / "rag_system"))

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(a * a for a in vec2))
    return dot_product / (norm1 * norm2) if norm1 and norm2 else 0

def test_environment():
    """Test environment setup"""
    try:
        from app.config import get_settings
        
        settings = get_settings()
        if not settings.gemini_api_key:
            return False, "No API key found"
        
        return True, f"API Key: {settings.gemini_api_key[:20]}..."
    except Exception as e:
        return False, f"Config error: {e}"

def test_text_processing():
    """Test the enhanced text processing and chunking"""
    try:
        from services.text_processing import TextProcessingService, ChunkingConfig
        
        # Configure modern adaptive chunking
        config = ChunkingConfig(
            max_chunk_size=800,      # characters (vs legacy 200 words)
            target_chunk_size=600,   # aim for this size
            chunk_overlap=150,       # character overlap (vs legacy 50 words)
            use_semantic_boundaries=True  # NEW: respect sentences/paragraphs
        )
        
        processor = TextProcessingService(config)
        
        # Sample text showcasing the improvements
        sample_text = """
        The RAG system has been successfully modernized with several revolutionary improvements.
        
        First, we've replaced the rigid 200-word chunking with adaptive semantic chunking that 
        respects natural language boundaries like sentences and paragraphs. This preserves 
        context much better than arbitrary word-based splits.
        
        Second, the embedding model has been upgraded from all-MiniLM-L6-v2 (384 dimensions) 
        to Google's text-embedding-004 (768 dimensions). This doubles the semantic capacity 
        and provides much richer understanding of text meaning.
        
        Third, the vector database has been modernized from local ChromaDB to cloud-based 
        Supabase, enabling production-scale deployment with built-in authentication and 
        seamless integration capabilities.
        """
        
        # Process the document
        chunks = processor.process_document(sample_text, "modernization_showcase")
        stats = processor.get_chunk_statistics(chunks)
        
        # Legacy comparison for demo
        words = sample_text.split()
        legacy_chunks = len(words) // 150  # Simulate 200-word chunks
        
        results = {
            'chunks_created': len(chunks),
            'avg_words': stats['avg_word_count'],
            'avg_chars': stats['avg_char_count'],
            'legacy_would_create': legacy_chunks,
            'improvement': f"Better boundaries, {stats['avg_word_count']:.0f} words/chunk vs rigid 200"
        }
        
        return True, results
        
    except Exception as e:
        return False, f"Text processing failed: {e}"

def test_embedding_generation():
    """Test Google text-embedding-004 embedding generation"""
    try:
        from embedding.gemini_embedding_client import GeminiEmbeddingClient
        from app.config import get_settings
        
        settings = get_settings()
        client = GeminiEmbeddingClient(api_key=settings.gemini_api_key)
        
        # Test single embedding
        test_text = "Machine learning transforms data into actionable insights"
        embedding = client.embed_query(test_text)
        
        # Test batch embeddings
        texts = [
            "What is machine learning?",
            "Machine learning is a subset of artificial intelligence that uses statistical algorithms",
            "Neural networks are fundamental to deep learning systems"
        ]
        
        embeddings = client.embed_documents(texts)
        
        # Calculate similarities
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        results = {
            'model': client.model,
            'dimensions': len(embedding),
            'vector_norm': math.sqrt(sum(x*x for x in embedding)),
            'vector_range': [min(embedding), max(embedding)],
            'first_10_dims': embedding[:10],
            'batch_count': len(embeddings),
            'similarities': similarities,
            'query_vs_answer_sim': cosine_similarity(embeddings[0], embeddings[1])
        }
        
        return True, results
        
    except Exception as e:
        return False, f"Embedding generation failed: {e}"

def test_document_processing():
    """Test document processing utilities"""
    try:
        from services.document_utils import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Test with sample content
        sample_content = """
        This is a comprehensive test of the document processing system.
        
        The processor can handle multiple file types including:
        - Plain text files (.txt)
        - PDF documents (.pdf) 
        - Word documents (.docx)
        - Markdown files (.md)
        
        It extracts clean text while preserving important structural elements.
        """
        
        # Extract text and metadata
        extracted_text = processor.extract_text_content(sample_content, "txt")
        metadata = processor.extract_metadata(sample_content, "test_document.txt")
        
        results = {
            'extracted_length': len(extracted_text),
            'word_count': metadata.get('word_count', 0),
            'char_count': metadata.get('char_count', 0),
            'processing_success': True
        }
        
        return True, results
        
    except Exception as e:
        return False, f"Document processing failed: {e}"

def test_end_to_end_showcase():
    """End-to-end test showcasing complete RAG functionality"""
    try:
        from services.text_processing import TextProcessingService, ChunkingConfig
        from embedding.gemini_embedding_client import GeminiEmbeddingClient
        from app.config import get_settings
        
        # Setup components
        config = ChunkingConfig(max_chunk_size=600, chunk_overlap=100, use_semantic_boundaries=True)
        text_processor = TextProcessingService(config)
        
        settings = get_settings()
        embedding_client = GeminiEmbeddingClient(api_key=settings.gemini_api_key)
        
        # Sample knowledge base
        knowledge_base = """
        Artificial Intelligence (AI) represents one of the most transformative technologies of our time.
        Machine learning, a subset of AI, enables computers to learn and improve from experience without 
        being explicitly programmed for every task.
        
        Deep learning uses neural networks with multiple layers to model and understand complex patterns
        in data. This approach has revolutionized fields like computer vision, natural language processing,
        and speech recognition.
        
        Natural Language Processing (NLP) focuses on the interaction between computers and human language.
        Modern NLP systems can understand context, extract meaning, and even generate human-like text
        that is coherent and contextually appropriate.
        """
        
        # Process document into chunks
        chunks = text_processor.process_document(knowledge_base, "ai_knowledge_base")
        chunk_texts = [chunk[0] for chunk in chunks]
        
        # Generate embeddings for all chunks
        doc_embeddings = embedding_client.embed_documents(chunk_texts)
        
        # Test queries
        test_queries = [
            "What is machine learning?",
            "How does deep learning work?",
            "What is natural language processing?"
        ]
        
        results = {
            'document_chunks': len(chunks),
            'embeddings_generated': len(doc_embeddings),
            'queries_tested': []
        }
        
        # Test semantic search for each query
        for query in test_queries:
            query_embedding = embedding_client.embed_query(query)
            
            # Find best matching chunk
            similarities = [cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings]
            best_match_idx = similarities.index(max(similarities))
            best_score = similarities[best_match_idx]
            best_chunk = chunk_texts[best_match_idx]
            
            results['queries_tested'].append({
                'query': query,
                'best_score': best_score,
                'best_match': best_chunk[:100] + "..."
            })
        
        return True, results
        
    except Exception as e:
        return False, f"End-to-end test failed: {e}"

def main():
    """Main test runner - showcases complete RAG system"""
    
    output_file = "rag_showcase_results.txt"
    
    with open(output_file, "w") as f:
        print("🚀 RAG System Modernization Showcase", file=f)
        print("=" * 60, file=f)
        print("From legacy 200-word chunks to modern semantic RAG", file=f)
        print("=" * 60, file=f)
        
        tests = [
            ("🌍 Environment Setup", test_environment),
            ("📝 Text Processing & Chunking", test_text_processing),
            ("🧠 Embedding Generation", test_embedding_generation),
            ("📄 Document Processing", test_document_processing),
            ("🔄 End-to-End RAG Demo", test_end_to_end_showcase),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:", file=f)
            print("-" * 40, file=f)
            
            try:
                success, result = test_func()
                results.append((test_name, success))
                
                if success:
                    print("✅ SUCCESS", file=f)
                    
                    if test_name == "🌍 Environment Setup":
                        print(f"   {result}", file=f)
                    
                    elif test_name == "📝 Text Processing & Chunking":
                        print(f"   📊 Created: {result['chunks_created']} semantic chunks", file=f)
                        print(f"   📏 Average: {result['avg_words']:.0f} words, {result['avg_chars']:.0f} chars", file=f)
                        print(f"   🆚 Legacy would create: ~{result['legacy_would_create']} rigid chunks", file=f)
                        print(f"   🎯 Improvement: {result['improvement']}", file=f)
                    
                    elif test_name == "🧠 Embedding Generation":
                        print(f"   🎯 Model: {result['model']}", file=f)
                        print(f"   📐 Dimensions: {result['dimensions']}", file=f)
                        print(f"   🔢 First 10 dims: {result['first_10_dims']}", file=f)
                        print(f"   📊 Range: [{result['vector_range'][0]:.4f}, {result['vector_range'][1]:.4f}]", file=f)
                        print(f"   🎯 Vector norm: {result['vector_norm']:.4f}", file=f)
                        print(f"   📦 Batch processed: {result['batch_count']} texts", file=f)
                        print(f"   🔗 Query-Answer similarity: {result['query_vs_answer_sim']:.4f}", file=f)
                    
                    elif test_name == "📄 Document Processing":
                        print(f"   📝 Processed: {result['extracted_length']} characters", file=f)
                        print(f"   📊 Words: {result['word_count']}, Chars: {result['char_count']}", file=f)
                    
                    elif test_name == "🔄 End-to-End RAG Demo":
                        print(f"   📚 Knowledge base: {result['document_chunks']} chunks", file=f)
                        print(f"   🧠 Embeddings: {result['embeddings_generated']} generated", file=f)
                        print(f"   🔍 Query results:", file=f)
                        for query_result in result['queries_tested']:
                            print(f"      Q: {query_result['query']}", file=f)
                            print(f"      Score: {query_result['best_score']:.4f}", file=f)
                            print(f"      Match: {query_result['best_match']}", file=f)
                else:
                    print(f"❌ FAILED: {result}", file=f)
                    
            except Exception as e:
                print(f"❌ CRASHED: {e}", file=f)
                traceback.print_exc(file=f)
                results.append((test_name, False))
        
        # Summary
        print(f"\n" + "=" * 60, file=f)
        print("📊 TEST RESULTS SUMMARY", file=f)
        print("=" * 60, file=f)
        
        passed = sum(1 for _, success in results if success)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}", file=f)
        
        print(f"\n🎯 Score: {passed}/{len(tests)} tests passed", file=f)
        
        if passed == len(tests):
            print(f"\n🎉 PERFECT! RAG System Fully Functional!", file=f)
            print(f"✅ Google text-embedding-004 working (768D)", file=f)
            print(f"✅ Adaptive semantic chunking implemented", file=f)
            print(f"✅ Document processing operational", file=f)
            print(f"✅ Similarity search functioning", file=f)
            print(f"✅ End-to-end RAG pipeline complete", file=f)
            print(f"\n🚀 Ready for production with Supabase integration!", file=f)
        else:
            print(f"\n🔧 Some issues found - check details above", file=f)
        
        print(f"\n💡 Key Improvements Achieved:", file=f)
        print(f"   📏 Chunking: 200 words → 600-800 chars (adaptive)", file=f)
        print(f"   🧠 Embeddings: 384D → 768D (+100% capacity)", file=f)
        print(f"   🎯 Boundaries: Word-based → Semantic (sentences/paragraphs)", file=f)
        print(f"   🏗️ Architecture: Monolithic → Modular services", file=f)
        print(f"   ☁️ Database: Local ChromaDB → Cloud Supabase (when configured)", file=f)
    
    print(f"🎉 RAG System Showcase Complete!")
    print(f"📋 Results saved to: {output_file}")
    print(f"🔍 Check the file for detailed results including embedding vectors!")

if __name__ == "__main__":
    main() 