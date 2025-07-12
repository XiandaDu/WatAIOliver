# WatAIOliver Project: Manual Setup Guide (Windows, VS Code)

This guide outlines the steps to set up and run the WatAIOliver project on Windows (VS Code environment).

Please note: 
- Lines surrounded by "<>" should be replaced with relevant lines specific to your computer
- Please ensure that you have included a .env file in the backend folder and in the machine_learning folder with the right setup info. If you have not or are not sure if you have written your .env file correctly, please ask for help

---

## 1. Environment Setup

### a. Create & Activate Virtual Environment

```powershell
cd <Path to project route>
python3.12 -m venv venv
.\venv\Scripts\activate
```

### b. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

---

## 2. Install Python Dependencies 

### a. Install backend dependencies

```powershell
pip install -r backend/requirements.txt
```

### b. Install PDF processor dependencies

```powershell
pip install -r machine_learning/pdf_processor/requirements.txt
```

### c. Install RAG system dependencies

```powershell
pip install -r machine_learning/rag_system/requirements.txt
```

> ✅ Note: If there are package conflicts, resolve them manually by installing the correct versions as shown by pip error messages.

---

## 3. Install Frontend Dependencies

```powershell
cd frontend
npm install
```

Ensure the `marked` package is installed:

```powershell
npm list marked
```

If not installed:

```powershell
npm install marked
```

---

## 4. Run Each Service (Use Separate Terminal Tabs)

### a. Tab 1: Frontend (Vite Server)

```powershell
cd <Path to project root>\frontend
npm run dev
```

### b. Tab 2: Backend API

```powershell
cd <Path to project root>\backend
..\venv\Scripts\python.exe -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### c. Tab 3: PDF Processor

```powershell
cd <Path to project root>\machine_learning\pdf_processor
& "<Path to project root>\venv\Scripts\python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### d. Tab 4: RAG System (Make sure you have `.env` loaded)

```powershell
cd <Path to project root>\machine_learning\rag_system
& "<Path to project root>\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

---

## ✅ Tips:

* Always **cd into the correct directory** for backend, PDF processor, and RAG system before running Uvicorn.
* Always use the **absolute path** to Python executable inside your venv to avoid path issues.
* If you see import errors, double-check your **working directory**.

---

## Final Notes

* Run each service in its own VS Code terminal tab.
* Ensure your `.env` is correctly placed and loaded for services requiring credentials.
* Always activate the virtual environment before running any commands:

```powershell
.\venv\Scripts\activate
```

You're done! Your entire project should now run successfully.

---