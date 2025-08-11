# Machine Learning Services

This directory contains the Retrieval Augmented Generation (RAG) system and supporting services.

- `rag_system/` – Embedding API and vector database helpers
- `pdf_processor/` – Converts PDFs to text/markdown
- `ai_agents/` – Optional multi‑agent reasoning system

Each service has its own README with setup instructions. After activating a virtual environment you can start the RAG server with:
```bash
cd machine_learning/rag_system
uvicorn app.main:app --reload --port 8002
```

Windows example:
```bat
set PYTHONPATH=machine_learning
python -m uvicorn rag_system.app.main:app --reload --host 0.0.0.0 --port 8002
```

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
├── tests/               # Test suites
└── README.md            # This file
```
