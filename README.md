# WatAIOliver

This is the **Oliver** repo for **WatAI** — an LLM-based RAG (Retrieval-Augmented Generation) project.

Oliver is an intelligent assistant to help instructors and students interact with course materials through conversational AI. This is a new implementation based on the legacy Oliver project.

Instructors can upload course content, and Oliver will use a RAG pipeline to generate better, more context-aware answers when students ask questions about their courses.

## Technology Stack

* **Frontend**: React, TailwindCSS
* **Backend**: FastAPI
* **LLM**: Newer LLM APIs (replacing legacy APIs)
* **Database**: Supabase (PostgreSQL)
* **Vector DB**: ChromaDB *or* pgvector (choose based on team preference)
* **CI/CD**: GitHub Actions *(or deploy scripts for separate parts)*


## Git Workflow

We will maintain **three main branches**:

* `main`: production branch
* `staging`: pre-production
* `development`: active development

**Branching rules**:

* Only `staging` can be merged into `main`.
* Only `development` can be merged into `staging`.
* For feature work, create a branch off `development`, I suggest to named it as:
  `@frontend/feature-name` or `@backend/feature-name`

Example:
`@frontend/login`
`@backend/chat-api`

Make a PR when a feature is implemented — as it is easier for peer review and debug.

## First Mission 🚀
Those tasks are for the first (few) weeks. I've included all the first steps I thought of, so it's okay if you can't complete them all in a week.
### Frontend Team

The old frontend was a static page. We will now rebuild it with React + TailwindCSS.

**Tasks**:
1. Choose one of:
* Use an existing React template (e.g. [openai-react-chat](https://github.com/elebitzero/openai-react-chat))
* Build from scratch

Once you decide on an approach, post it in the Discord channel.

2. Based on your choice:
* If using a template:
→ Get familiar with the codebase, remove/disable features we currently don't need.

* If building from scratch:
→ Focus first on creating a clean, scalable project structure with one very simple demo page and routing.
→ Keep maintainability in mind — frontend code can easily become hard to manage.

### Backend & Machine Learning Team

**Tasks**:

* Review the **legacy repo**: [https://github.com/XiandaDu/Oliver-Legacy](https://github.com/XiandaDu/Oliver-Legacy)
* Understand the old architecture: API flow, ChromaDB integration.
* Set up the project and run it locally.
* Replace old LLM APIs with modern ones (reference provided).
* Start designing the new backend architecture.

**Collaboration**: The initial analyses between Backend and ML Engineers will overlap but with different focus areas.

# Let’s build an awesome new Oliver together!