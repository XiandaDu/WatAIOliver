# Agent System Overview

The optional agent system provides advanced multi‑agent reasoning. It lives under `machine_learning/ai_agents`.

## Running the Service

After installing dependencies from `machine_learning/ai_agents/requirements.txt`, start the server:
```bash
cd machine_learning/ai_agents
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

Windows example:
```bat
set PYTHONPATH=machine_learning
python -m uvicorn ai_agents.app.main:app --reload --host 0.0.0.0 --port 8003
```

See the README in that folder for architecture details and API examples.
