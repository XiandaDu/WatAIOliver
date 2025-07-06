-- Setup Vector Database for RAG System
-- This script creates the necessary table and index for vector storage in Supabase

-- Enable the vector extension (run this in Supabase SQL editor)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table for vector storage
-- Note: Using a different table name to avoid conflicts with existing documents table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id bigserial PRIMARY KEY,
    content text NOT NULL,
    metadata jsonb DEFAULT '{}',
    embedding vector(512) -- 512-dimensional vectors for gemini-embedding-001
);

-- Create an index for efficient similarity search
-- Using HNSW index which is optimized for high-dimensional vectors
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx 
ON document_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- Optional: Create additional indexes for metadata filtering
CREATE INDEX IF NOT EXISTS document_embeddings_metadata_idx 
ON document_embeddings 
USING gin (metadata);

-- Grant necessary permissions (adjust based on your security needs)
-- Grant permissions to the authenticated role
GRANT ALL ON document_embeddings TO authenticated;
GRANT ALL ON document_embeddings TO service_role;

-- Grant usage on the sequence
GRANT USAGE, SELECT ON SEQUENCE document_embeddings_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE document_embeddings_id_seq TO service_role;

-- Example query to test vector similarity search
-- SELECT content, metadata, 1 - (embedding <=> query_embedding) as similarity
-- FROM document_embeddings
-- WHERE metadata->>'course_id' = 'specific_course'
-- ORDER BY embedding <=> query_embedding
-- LIMIT 5; 