# LLM Migration Factory

LLM Migration Factory is a FastAPI + React application that helps teams migrate
LLM-powered Python scripts from one provider/model stack to another with confidence.

## What problem this project solves

Teams shipping LLM applications often need to move between providers for cost,
performance, availability, or strategy reasons. In practice, migration is slow
because prompts, model behavior, and SDK integrations are tightly coupled.

LLM Migration Factory turns that migration into a structured workflow:
- discover where LLM calls exist in real code,
- benchmark current behavior as a baseline,
- adapt prompts for the target stack,
- validate semantic quality with an automated judge,
- produce refactored source + a migration report.

This reduces manual trial-and-error and gives a measurable path from "current model"
to "target model" for hackathon demos and beyond.

## How it works (end-to-end)

1. **Upload & Parse**  
   A Python file is uploaded, and the AST parser finds `chat.completions.create`
   call sites with relevant parameters (messages, model, temperature, etc.).

2. **Golden Baseline Capture**  
   The source model is called to capture baseline outputs ("golden responses")
   for each discovered call site.

3. **Prompt Optimization Loop**  
   For each call site, the system iterates:
   - translate prompt for target model,
   - run target model,
   - evaluate with judge model against golden output,
   - refine prompt based on judge feedback until threshold/max iterations.

4. **Code Refactor**  
   The code surgeon rewrites the original script to target configuration and injects
   optimized prompts into migrated calls.

5. **Report & Download**  
   A report is generated with semantic fidelity, latency, and estimated cost metrics,
   and the refactored Python file is available for download.

<img width="2459" height="4055" alt="LLM Migration Factory README flow" src="https://github.com/user-attachments/assets/debc4c49-243e-48e2-aa5c-9b7ba076dbe9" />


## What you get from the tool

- A **working migration pipeline** from source to target model stack
- A **quantitative quality signal** (judge scoring) for each migrated call site
- A **developer-friendly report** for comparisons and iteration history
- A **downloadable migrated script** ready for integration testing

---

## 1) Architecture

### Backend (`backend/`)
- **API server**: `main.py` (upload, status, report, config, websocket events)
- **Pipeline orchestration**: `pipeline/orchestrator.py`
- **Parser**: `parser/ast_parser.py` (extracts call sites from Python AST)
- **Golden capture**: `benchmarking/golden_capture.py`
- **Optimization loop**:
  - `optimizer/prompt_translator.py`
  - `optimizer/target_runner.py`
  - `optimizer/evaluator.py`
- **Code rewrite**: `surgeon/code_refactor.py`
- **Report**: `reporting/report_generator.py`
- **Job persistence abstraction**: `job_store.py`
  - default in-memory store
  - optional DynamoDB-backed store

### Frontend (`frontend/`)
- React + Vite app in `src/App.tsx`
- pulls public runtime config from `GET /api/config`
- real-time pipeline logs via websocket `/ws/{job_id}`

### Utility scripts (`scripts/`)
- `verify.mjs`: full project verify command (backend + frontend + tests)
- `smoke_job.py`: fetch a specific job status/report quickly

---

## 2) Prerequisites

- **Python 3.10+**
- **Node.js 20+**
- Network access to whichever model providers you configure

Optional (only if using DynamoDB persistence):
- AWS account + IAM credentials + DynamoDB table

---

## 3) Environment Configuration

### Backend env
Copy:
- `backend/.env.example` -> `backend/.env`

Important variables:
- `USE_MOCK_APIS=true|false`
- Source model: `SOURCE_MODEL`, `SOURCE_BASE_URL`, `SOURCE_API_KEY`
- Target model: `TARGET_PROVIDER`, `TARGET_MODEL`, `TARGET_BASE_URL`, `TARGET_API_KEY`
- Judge model: `JUDGE_MODEL`, `JUDGE_BASE_URL`, `JUDGE_API_KEY`
- Optimizer model: `OPTIMIZER_MODEL`, `OPTIMIZER_BASE_URL`, `OPTIMIZER_API_KEY`
- CORS: `ALLOWED_ORIGINS`
- Optional labels shown in UI: `SOURCE_LABEL`, `TARGET_LABEL`, `JUDGE_LABEL`, `OPTIMIZER_LABEL`
- Optional target cost estimate knobs:
  - `TARGET_COST_INPUT_PER_1K`
  - `TARGET_COST_OUTPUT_PER_1K`
- Optional persistence:
  - `JOB_STORE_BACKEND=memory|dynamodb`
  - `JOBS_TABLE_NAME`
  - `AWS_REGION`

Note: `backend/config.py` uses `load_dotenv(..., override=True)`, so values in `backend/.env`
override shell env variables for this process.

### Frontend env
Copy:
- `frontend/.env.example` -> `frontend/.env`

Key variable:
- `VITE_API_BASE=http://localhost:8000` (or your deployed API origin)

Optional:
- `VITE_WS_BASE` (if websocket host differs from API host)

---

## 4) Run Locally

### Start backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Sanity check:
- Open `http://localhost:8000/health` -> `{"status":"ok"}`
- Open `http://localhost:8000/api/config` -> config JSON (no secrets)

### Start frontend
```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`; if busy it may use 5174/5175).
Default backend CORS already allows these dev ports.

---

## 5) Verification / QA

From repository root:
```bash
npm run verify
```

This runs:
1. `verify_backend.py` (core backend smoke)
2. Frontend lint (`eslint`)
3. Frontend production build (`vite build`)
4. Backend tests (`pytest`)

Backend tests are in `backend/tests/`.

---

## 6) API Overview

### HTTP endpoints
- `GET /health`
- `GET /api/config` (public non-secret config for UI)
- `POST /api/upload` (multipart `.py` upload)
- `GET /api/jobs/{job_id}` (status/logs)
- `GET /api/jobs/{job_id}/report` (final report)
- `GET /api/jobs/{job_id}/download` (refactored Python source)

### Websocket
- `WS /ws/{job_id}`
  - streams `log`, `phase`, `report_ready`, `error`, `heartbeat` events

---

## 7) Deployment Notes

For hackathon simplicity:
- deploy frontend static build to Vercel (or similar),
- deploy FastAPI backend on a process host (Render/Railway/Fly/AWS),
- set frontend `VITE_API_BASE` to backend public origin,
- add frontend origin to backend `ALLOWED_ORIGINS`.

If you enable DynamoDB:
- configure `JOB_STORE_BACKEND=dynamodb`,
- set `JOBS_TABLE_NAME` and AWS credentials/region.

---

## 8) Repository Layout

- `backend/` - API, pipeline, optimizer, parser, refactor, reporting, tests
- `frontend/` - React UI
- `scripts/` - verification/smoke scripts
- `.github/workflows/verify.yml` - CI verification pipeline

---

## 9) Common Troubleshooting

- **"Could not load backend configuration" in UI**
  - backend not running or `VITE_API_BASE` mismatch
  - CORS origin missing from `ALLOWED_ORIGINS`

- **Very low semantic scores**
  - check optimizer/judge keys and model availability
  - inspect iteration feedback in report
  - verify source prompt content is fully preserved in optimized user prompts

- **Pipeline fails during golden capture**
  - source credentials invalid
  - source base URL/model not reachable

