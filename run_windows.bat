@echo off
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
echo Put GEMINI_API_KEY in .env before starting.
python -m uvicorn main:app --host 0.0.0.0 --port 8000
