# WatAIOliver

**Note:** A FastAPI backend is being added in the `backend/` folder. The chat logic from Oliver-Legacy is being migrated here to support real Qwen model chat functionality.

This is the **Oliver** repo for **WatAI** — an LLM-based RAG (Retrieval-Augmented Generation) project.

Oliver is an intelligent assistant who helps instructors and students interact with course materials through conversational AI. This is a new implementation based on the legacy Oliver project.

Instructors can upload course content, and Oliver will use an RAG pipeline to generate better, more context-aware answers when students ask questions about their courses. Current scheduled course for deployment is MTE 182 by Albert Jiang in Fall term.

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
* To create a new feature, create a branch from the `development`, I suggest naming it:
  `@frontend/feature-name` or `@backend/feature-name`

Example:
`@frontend/login`
`@backend/chat-api`

Make a PR when a feature is implemented — as it is easier for peer review and debug.

## Week 2 🚀
I hope you guys have some understanding of the legacy workflow. Let's ship some code now.

### Frontend Team
Based on your choice of technology stack, ignoring the login page for now, let's try to create a ChatGPT-like front page. It needs to have:
* a conversation window for users to input prompts and agents to give answers.
* a sidebar that can separate different conversations.
Potential things to keep in mind or to leave a space for:
* model choice dropdown bar
* a search icon to search a keyword from past conversations
* able to hide the sidebar

### Backend & Machine Learning Team
There are two directions:
* Set up a Supabase on your local, try to create a `conversation` table. It needs to contain at least,
```
| Field Name        | Type               | Description                                      |
| ----------------- | ------------------ | ------------------------------------------------ |
| `id`              | UUID (Primary Key) | Unique identifier for the message                |
| `user_id`         | UUID (Foreign Key) | Owner of the conversation                        |
| `sender`          | `text` (or enum)   | `"user"` or `"assistant"`                        |
| `message`         | `text`             | Prompt/response if sender="user"/"assistant"     |
| `created_at`      | `timestamp`        | Time the message was created                     |
| `updated_at`      | `timestamp`        | Time the message was updated                     |
```
* Then, implement the CRUD (create, read, update and delete) methods based on the table. The point for these two tasks is to have a skeleton for the backend.

* The other direction is, while going through the legacy code, check whether any useful APIs can be reused in the new repo. Move them here.

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

# Let's build an awesome new Oliver together!
