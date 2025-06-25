# Machine Learning Components

This directory contains the modernized machine learning components for the Oliver teaching chatbot system.

## 🏗️ **Directory Structure**

```
machine_learning/
├── rag_system/          # Modern RAG system (replaces oliver legacy)
│   ├── embedding/       # Google text-embedding-004 client
│   ├── services/        # RAG services and text processing
│   ├── vector_db/       # Supabase vector database
│   ├── llm_clients/     # LLM integration
│   ├── examples/        # Usage examples
│   └── README.md        # Detailed documentation
├── scripts/             # Utility scripts and demos
├── tests/              # Test suites
└── README.md           # This file
```

## 🚀 **Components**

### **RAG System** (`rag_system/`)
The core RAG (Retrieval-Augmented Generation) system featuring:
- **Google text-embedding-004**: 768-dimensional embeddings
- **Supabase Vector Database**: Cloud-based, scalable vector storage
- **Adaptive Chunking**: Semantic boundary-aware text processing
- **Enhanced Preprocessing**: Google-recommended text normalization
- **Production Ready**: Health checks, monitoring, error handling

**See `rag_system/README.md` for detailed documentation.**

### **Scripts** (`scripts/`)
Utility scripts for testing, demos, and data processing.

### **Tests** (`tests/`)
Comprehensive test suites for all components.

## 🎯 **Quick Start**

1. **Navigate to RAG system**: `cd rag_system/`
2. **Follow setup guide**: See `rag_system/README.md`
3. **Run examples**: `python examples/basic_usage.py`

## 📚 **Migration from Legacy**

This modernized system replaces the outdated `oliver legacy/` RAG implementation with significant improvements:

- ✅ **No more 200-word chunking limits**
- ✅ **768D embeddings** (vs 384D legacy)
- ✅ **Cloud vector storage** (vs local ChromaDB)
- ✅ **Semantic chunking** with proper buffers
- ✅ **Modular architecture** (vs monolithic scripts)

For detailed migration information, see `rag_system/MIGRATION_SUMMARY.md`.

## 🤝 **Contributing**

When working with these components:
1. **Follow the modular structure**
2. **Use proper type hints**
3. **Add comprehensive tests**
4. **Update documentation**
5. **Run health checks**

---

**Ready to build the next generation of AI-powered teaching tools! 🎓🤖**