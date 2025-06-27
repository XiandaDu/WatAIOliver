# RAG System Setup Guide

Simple RAG system using `gemini-embedding-001` with 512D vectors.

## 🚀 Quick Setup

### Step 1: Google Cloud Setup
1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create Project:**
   - Click "New Project" 
   - Name it anything you want
   - Note your **Project ID** (you'll need this)

3. **Enable Billing:**
   - Go to **Billing** → Link a billing account
   - ⚠️ **Required** - won't work without billing

4. **Enable APIs:**
   - Go to **APIs & Services** → **Library**
   - Search and enable:
     - ✅ **Vertex AI API** 
     - ✅ **Generative Language API**

5. **Create Service Account:**
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **"+ CREATE SERVICE ACCOUNT"**
   - Name: `rag-system`
   - Add role: **Vertex AI User**
   - Click **"CREATE AND CONTINUE"** → **"DONE"**

6. **Download Credentials:**
   - Find your service account in the list
   - Click **⋮** → **"Manage keys"**
   - Click **"ADD KEY"** → **"Create new key"** → **"JSON"**
   - Save the JSON file to this folder: `machine_learning/`

### Step 2: Supabase Setup
1. **Go to [Supabase](https://supabase.com/)**
2. **Create Project** (free tier works)
3. **Create Table:**
   ```sql
   CREATE TABLE documents (
     id bigserial primary key,
     content text,
     metadata jsonb,
     embedding vector(512)
   );
   
   CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
   ```
4. **Get Credentials:**
   - Go to **Settings** → **API**
   - Copy your **URL** and **Service Key**

### Step 3: Configure Environment
1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file:**
   ```bash
   # Update the JSON filename to match yours
   GOOGLE_APPLICATION_CREDENTIALS=machine_learning/your-service-account-file.json
   GOOGLE_CLOUD_PROJECT=your-actual-project-id
   
   # Add your Supabase credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-key
   ```

### Step 4: Install & Test
```bash
# Install dependencies
pip install -r requirements.txt

# Test it works
cd ../tests
python test_rag.py
```

## ✅ Success Output
You should see:
```
📋 Model Configuration:
   Model: gemini-embedding-001
   Expected Dimensions: 512

🔍 Testing Query Embedding:
✅ Query: 'What is machine learning?'
   Embedding Dimensions: 512
   Vector Preview: [0.123456, -0.789012, ...]

✅ ALL TESTS PASSED!
```

## 🐛 Common Issues

**401 UNAUTHENTICATED:**
- ❌ Billing not enabled → Enable billing
- ❌ APIs not enabled → Enable Vertex AI API
- ❌ Wrong file path → Check your JSON file path in `.env`

**File not found:**
- ❌ JSON file in wrong location → Move to `machine_learning/` folder
- ❌ Wrong filename in `.env` → Update `GOOGLE_APPLICATION_CREDENTIALS`

**404 Model not found:**
- ❌ Using wrong project → Check `GOOGLE_CLOUD_PROJECT` matches your actual project ID

## 💡 Usage

```python
from services.rag_service import RAGService
from app.config import get_settings

# Initialize
rag = RAGService(get_settings())

# Process document
result = rag.process_document("course_id", "content")

# Ask question
answer = rag.answer_question("course_id", "What is this about?")
```

That's it! 🎉 