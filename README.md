# WatAIOliver

**Note:** A FastAPI backend is being added in the `backend/` folder. The chat logic from Oliver-Legacy is being migrated here to support real Qwen model chat functionality.

This is the **Oliver** repo for **WatAI** — an LLM-based RAG project. Oliver is an intelligent assistant who helps instructors and students interact with course materials through conversational AI. This implementation is a refresh of the legacy Oliver project.

Instructors can upload course content, and Oliver will use an RAG pipeline to generate better, more context-aware answers when students ask questions about their courses. Current scheduled course for deployment is MTE 182 by Albert Jiang in Fall term.

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
