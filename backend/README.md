# Task2 Backend

FastAPI backend for the Task2 sentiment annotation system.

## Run

```bash
cd task2/backend
pip install -r requirements.txt
PYTHONPATH=src uvicorn task2_backend.main:app --reload
```

## Checks

```bash
cd task2/backend
PYTHONPATH=src pytest
lint-imports --config importlinter.ini
```
