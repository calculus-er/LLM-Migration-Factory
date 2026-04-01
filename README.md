# LLM Migration Factory

Hackathon project: upload a Python file that uses the OpenAI SDK, capture golden baselines, optimize prompts for a target model, and download refactored code with a migration report.

## Prerequisites

- **Python 3.10+** (for `zip(..., strict=True)` and the stack)
- **Node.js 20+** (for the Vite frontend)

## Local development

### 1. Backend API

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys (or USE_MOCK_APIS=true for offline demos)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Sanity check: open [http://localhost:8000/api/config](http://localhost:8000/api/config) — you should see JSON (no secrets).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# VITE_API_BASE should match the API (default http://localhost:8000)
npm run dev
```

Open the URL Vite prints (often `http://localhost:5173`; if that port is busy, Vite may use **5174** — the backend defaults allow common dev ports).

### 3. One-shot verification (CI / judges)

From the **repository root** (after `backend/venv` exists and `frontend` dependencies are installed):

```bash
npm run verify
```

Runs: `verify_backend.py` → ESLint → production build → `pytest`.

## Configuration notes

| Concern | What to set |
|--------|-------------|
| Frontend can’t load config | Start the API; ensure `VITE_API_BASE` matches it. |
| CORS errors in the browser | Add your exact dev origin to `ALLOWED_ORIGINS` in `backend/.env` (e.g. `http://localhost:5174` if Vite uses that port). Defaults include 5173–5175. |
| DynamoDB (optional deploy) | `JOB_STORE_BACKEND=dynamodb`, `JOBS_TABLE_NAME`, AWS credentials / `AWS_REGION`. Default is in-memory. |

See [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

## Deploy (outline)

- **Frontend:** Build `frontend` (`npm run build`) and host static assets (e.g. Vercel). Set **`VITE_API_BASE`** to your public API URL at build time.
- **Backend:** Run FastAPI on a process host (Render, Railway, Fly, AWS App Runner, etc.). WebSockets need the same host to support `/ws` unless you change architecture.
- **CORS:** Put your production site origin in **`ALLOWED_ORIGINS`** on the API.

## Project layout

- `backend/` — FastAPI app, pipeline, optimizer, job store
- `frontend/` — React + Vite UI
- `scripts/` — `verify.mjs`, `smoke_job.py` for quick checks
