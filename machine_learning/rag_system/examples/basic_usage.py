#!/usr/bin/env python3
"""
Basic Usage Example for Enhanced RAG System

This example demonstrates how to use the modernized RAG system with:
- Google text-embedding-004 model
- Supabase vector database
- Enhanced chunking and preprocessing
- Better document management

Run this after setting up your environment variables:
- GEMINI_API_KEY
- SUPABASE_URL  
- SUPABASE_SERVICE_KEY
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the rag_system to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings
from services.rag_service import RAGService
from services.text_processing import ChunkingConfig
from services.document_utils import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_rag_example():
    """Basic RAG usage example"""
    print("🚀 Enhanced RAG System - Basic Usage Example")
    print("=" * 50)
    
    # 1. Initialize the system
    print("\n1. Initializing RAG System...")
    settings = get_settings()
    
    # Configure chunking for better performance
    chunking_config = ChunkingConfig(
        max_chunk_size=800,
        chunk_overlap=150,
        target_chunk_size=600,
        use_semantic_boundaries=True
    )
    
    rag_service = RAGService(settings, chunking_config)
    
    # 2. Health check
    print("\n2. Performing health check...")
    health = await rag_service.health_check()
    print(f"System health: {'✅ Healthy' if health['overall_healthy'] else '❌ Issues detected'}")
    
    if not health['overall_healthy']:
        print("Health issues found:")
        for component, status in health['components'].items():
            if not status.get('healthy', False):
                print(f"  - {component}: {status.get('error', 'Unknown error')}")
        return
    
    # 3. Process a sample document
    print("\n3. Processing sample document...")
    
    sample_text = """
    # Introduction to Machine Learning
    
    Machine learning is a method of data analysis that automates analytical model building. 
    It is a branch of artificial intelligence (AI) based on the idea that systems can learn 
    from data, identify patterns and make decisions with minimal human intervention.
    
    ## Types of Machine Learning
    
    ### Supervised Learning
    Supervised learning uses labeled training data to learn a mapping function from input 
    variables to an output variable. Common examples include classification and regression problems.
    
    ### Unsupervised Learning  
    Unsupervised learning finds hidden patterns or intrinsic structures in input data without 
    labeled examples. Clustering and association rule learning are common unsupervised learning tasks.
    
    ### Reinforcement Learning
    Reinforcement learning is about taking suitable action to maximize reward in a particular 
    situation. It is employed by various software and machines to find the best possible behavior 
    or path it should take in a specific situation.
    
    ## Applications
    
    Machine learning applications include:
    - Image recognition and computer vision
    - Natural language processing
    - Recommendation systems
    - Fraud detection
    - Autonomous vehicles
    - Medical diagnosis
    
    ## Conclusion
    
    Machine learning continues to evolve and find new applications across industries. 
    Understanding its fundamentals is crucial for anyone working in technology today.
    """
    
    course_id = "ml_intro_101"
    result = await rag_service.process_document(
        course_id=course_id,
        content=sample_text,
        document_id="ml_basics_intro",
        metadata={
            "topic": "machine_learning_intro",
            "difficulty": "beginner",
            "author": "system_example"
        }
    )
    
    if result['success']:
        print(f"✅ Document processed successfully!")
        print(f"   - Created: {result['chunks_created']} chunks")
        print(f"   - Processing time: {result['processing_time_seconds']:.2f}s")
        print(f"   - Embedding dimension: {result['embedding_dimension']}")
        
        # Show chunking statistics
        stats = result['statistics']
        print(f"   - Average chunk size: {stats['avg_word_count']:.0f} words, {stats['avg_char_count']:.0f} chars")
    else:
        print(f"❌ Document processing failed: {result.get('error')}")
        return
    
    # 4. Ask questions
    print("\n4. Asking questions...")
    
    questions = [
        "What is machine learning?",
        "What are the types of machine learning?",
        "Give me examples of machine learning applications",
        "How does supervised learning work?"
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        
        answer_result = await rag_service.answer_question(
            course_id=course_id,
            question=question,
            top_k=3,
            include_metadata=True
        )
        
        if answer_result['success']:
            print(f"🤖 Answer: {answer_result['answer']}")
            print(f"📊 Retrieved {answer_result['retrieved_chunks']} chunks in {answer_result['processing_time_seconds']:.2f}s")
            
            if 'chunk_metadata' in answer_result:
                print("📄 Source chunks:")
                for i, meta in enumerate(answer_result['chunk_metadata']):
                    print(f"   {i+1}. Document: {meta['document_id']}, Chunk: {meta['chunk_index']}, "
                          f"Similarity: {meta['similarity_score']:.3f}")
        else:
            print(f"❌ Question failed: {answer_result.get('error')}")
    
    # 5. Get course statistics
    print("\n5. Course statistics...")
    stats_result = await rag_service.get_course_statistics(course_id)
    
    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"📈 Course '{course_id}' statistics:")
        print(f"   - Total chunks: {stats['total_chunks']}")
        print(f"   - Unique documents: {stats['unique_documents']}")
        print(f"   - Average chunk size: {stats['avg_word_count']:.0f} words")
        print(f"   - Embedding dimension: {stats['embedding_dimension']}")
    
    print("\n✅ Example completed successfully!")


async def document_processing_example():
    """Example of processing different document types"""
    print("\n" + "=" * 50)
    print("📄 Document Processing Example")
    print("=" * 50)
    
    processor = DocumentProcessor()
    
    # Create a sample text file
    sample_file = Path("sample_document.txt")
    sample_content = """
    This is a sample document for testing the document processor.
    
    It contains multiple paragraphs and demonstrates how the system
    can process various types of text content.
    
    The processor will extract metadata and prepare the content
    for RAG processing.
    """
    
    try:
        # Write sample file
        with open(sample_file, 'w') as f:
            f.write(sample_content)
        
        # Process the file
        text, metadata = processor.process_file(str(sample_file))
        
        print(f"✅ Processed file: {metadata['filename']}")
        print(f"   - File type: {metadata['file_type']}")
        print(f"   - File size: {metadata['file_size']} bytes")
        print(f"   - Word count: {metadata['word_count']}")
        print(f"   - Character count: {metadata['char_count']}")
        print(f"   - Success: {metadata['success']}")
        
        if text:
            print(f"   - Sample text: {text[:100]}...")
    
    finally:
        # Clean up
        if sample_file.exists():
            sample_file.unlink()


def chunking_comparison_example():
    """Example comparing legacy vs new chunking"""
    print("\n" + "=" * 50)
    print("🔄 Chunking Comparison Example")
    print("=" * 50)
    
    from services.text_processing import TextProcessingService, ChunkingConfig
    from services.document_utils import LegacyMigrationHelper
    
    sample_text = """
    Artificial Intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals. Colloquially, the term 
    "artificial intelligence" is often used to describe machines that mimic 
    "cognitive" functions that humans associate with the human mind, such as 
    "learning" and "problem solving". As machines become increasingly capable, 
    tasks considered to require "intelligence" are often removed from the 
    definition of AI, a phenomenon known as the AI effect. A quip in Tesler's 
    Theorem says "AI is whatever hasn't been done yet." For instance, optical 
    character recognition is frequently excluded from things considered to be AI, 
    having become a routine technology.
    """
    
    # Legacy chunking (200 words)
    legacy_chunks = []
    words = sample_text.split()
    chunk_size = 50  # Simulating 200 words with smaller text
    overlap = 10
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        legacy_chunks.append(chunk)
    
    print(f"📊 Legacy chunking (50-word simulation):")
    print(f"   - Number of chunks: {len(legacy_chunks)}")
    print(f"   - Average words per chunk: {sum(len(chunk.split()) for chunk in legacy_chunks) / len(legacy_chunks):.1f}")
    
    # New semantic chunking
    config = ChunkingConfig(
        max_chunk_size=400,  # Smaller for demo
        target_chunk_size=300,
        chunk_overlap=75,
        use_semantic_boundaries=True
    )
    
    processor = TextProcessingService(config)
    new_chunks = processor.process_document(sample_text, "demo_doc")
    
    print(f"\n🆕 New semantic chunking:")
    print(f"   - Number of chunks: {len(new_chunks)}")
    if new_chunks:
        avg_words = sum(metadata.word_count for _, metadata in new_chunks) / len(new_chunks)
        print(f"   - Average words per chunk: {avg_words:.1f}")
        print(f"   - Uses semantic boundaries: {config.use_semantic_boundaries}")
        print(f"   - Chunk overlap: {config.chunk_overlap} characters")
    
    # Migration estimation
    migration_helper = LegacyMigrationHelper()
    improvement = migration_helper.estimate_rechunking_improvement(legacy_chunks)
    
    print(f"\n📈 Improvement estimation:")
    print(f"   - Chunk reduction: {improvement['improvement_summary']['chunk_reduction']}")
    print(f"   - Better boundaries: {improvement['improvement_summary']['better_boundaries']}")
    print(f"   - Enhanced metadata: {improvement['improvement_summary']['enhanced_metadata']}")


async def main():
    """Main example runner"""
    try:
        # Check environment variables
        settings = get_settings()
        if not settings.gemini_api_key:
            print("❌ GEMINI_API_KEY environment variable not set")
            return
        if not settings.supabase_url or not settings.supabase_key:
            print("❌ Supabase environment variables not set (SUPABASE_URL, SUPABASE_SERVICE_KEY)")
            return
        
        # Run examples
        await basic_rag_example()
        await document_processing_example()
        chunking_comparison_example()
        
        print("\n" + "=" * 50)
        print("🎉 All examples completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 