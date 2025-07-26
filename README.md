# WatAIOliver

**Note:** A FastAPI backend is being added in the `backend/` folder. The chat logic from Oliver-Legacy is being migrated here to support real Qwen model chat functionality.

This is the **Oliver** repo for **WatAI** — an LLM-based RAG project. Oliver is an intelligent assistant who helps instructors and students interact with course materials through conversational AI. This implementation is a refresh of the legacy Oliver project.

Instructors can upload course content, and Oliver uses a RAG pipeline to generate context-aware answers when students ask questions. The first scheduled course for deployment is MTE 182 by Albert Jiang in the Fall term.

WatAIOliver combines a React frontend with a FastAPI backend and a modern RAG system. Users can upload material and chat with the assistant.

## Repository Layout

- `frontend/` – React application built with Vite and TailwindCSS
- `backend/` – FastAPI service exposing chat and file APIs
- `machine_learning/` – Embedding and RAG services, plus optional agent system

## Quick Start

1. **Install dependencies**

   
    On macOS/Linux you can run the helper script:
    ```bash
    ./setup.sh
    ```

   remember to run chmod +x setup.sh before ./ it.

```
./setup.sh          # setup + run everything (default)
./setup.sh setup    # setup only
./setup.sh start    # run services
./setup.sh stop     # stop services
./setup.sh status   # status
```
---

   Or install manually:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r machine_learning/pdf_processor/requirements.txt
   pip install -r machine_learning/rag_system/requirements.txt -c constraints.txt --upgrade --upgrade-strategy eager
   pip install -r machine_learning/ai_agents/requirements.txt
   ```
   Windows users should follow `windows_proj_env_setup.md`.
3. **Environment files** – copy the provided examples to `.env` inside `backend/` and `machine_learning/rag_system/` and update credentials.
4. **Run services**
   ```bash
   # Backend
   PYTHONPATH=backend python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   # Frontend
   cd frontend && npm ci
   npm run dev
   ```
   Optional services:
   ```bash
   # PDF processor
   PYTHONPATH=machine_learning python -m uvicorn pdf_processor.main:app --reload --host 0.0.0.0 --port 8001
   # RAG system
   PYTHONPATH=machine_learning python -m uvicorn rag_system.app.main:app --reload --host 0.0.0.0 --port 8002
   # Agent system
   PYTHONPATH=machine_learning python -m uvicorn ai_agents.app.main:app --reload --host 0.0.0.0 --port 8003
   ```



## Logging

The backend uses a rotating file logger located at `backend/src/app.log`. All requests are logged with their status code and processing time, making it easy to trace errors.

## Features

- Chat with persistent conversations
- File uploads (PDF and text)
- KaTeX formula rendering
- Retrieval‑augmented responses using the RAG system
- Optional multi‑agent debate mode

## Building Frontend

To create a production build of the frontend:
```bash
cd frontend
npm run build
```
The output is placed in `frontend/dist`.

## Technology Stack

* **Frontend**: React, TailwindCSS
* **Backend**: FastAPI
* **LLM**: Newer LLM APIs (replacing legacy APIs)
* **Database**: Supabase (PostgreSQL)
* **Vector DB**: ChromaDB *or* pgvector (choose based on team preference)
* **CI/CD**: GitHub Actions *(or deploy scripts for separate parts)*

## Git Workflow

We maintain three main branches:

* `main`: production branch
* `staging`: pre-production
* `development`: active development

**Branching rules**:

* Only `staging` can be merged into `main`.
* Only `development` can be merged into `staging`.
* Create feature branches from `development`, e.g. `@frontend/login` or `@backend/chat-api`.
* Make a PR when a feature is implemented for easier review.

# Let's build an awesome new Oliver together!
