# Backend Setup

## Install Dependencies

Ensure you have Python 3.9+ and a virtual environment activated. Then install all required packages:

```bash
pip install -r requirements.txt
```

## Launch the Development Server

Navigate to the project root and start the FastAPI server with hot-reloading enabled:

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at: [http://localhost:8000](http://localhost:8000)
You may run [http://localhost:8000/test](http://localhost:8000/test) to test it. 

## Table draft
```
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender text check (sender in ('user', 'assistant')) not null,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    course_id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    term VARCHAR(50),
    created_by TEXT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    model_id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE course_models (
    course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
    model_id TEXT REFERENCES models(model_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, model_id)
);

CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
    term VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_embeddings (
    embedding_id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

<!-- CREATE TABLE logs (
    log_id TEXT PRIMARY KEY,
    log_type VARCHAR(50) CHECK (log_type IN ('info', 'error', 'debug')),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); -->
```