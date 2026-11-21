# DisputeGuard — Production Deployment Guide

DisputeGuard is an evidence-grounded AI decisioning system for chargeback representment. This guide details the production deployment process for the **Next.js 15 Frontend on Vercel** and the **FastAPI Backend on Render**.

---

## 1. System Architecture

```
┌───────────────────────────────────────┐            HTTPS / JSON REST API            ┌──────────────────────────────────────────────┐
│           Vercel Frontend             │ ──────────────────────────────────────────> │                Render Backend                │
│                                       │ <────────────────────────────────────────── │                                              │
│ • Next.js 15 (App Router, React 19)   │               CORS Allowed:                 │ • FastAPI (Python 3.12, Uvicorn)             │
│ • TypeScript + Tailwind CSS           │      Origin: https://*.vercel.app           │ • LangGraph StateGraph Workflow              │
│ • Static prerender + Client hydration │      Header: Access-Control-Allow-Origin    │ • XGBoost Win Probability Calibrator         │
│ • Base URL: NEXT_PUBLIC_API_URL       │                                             │ • ReportLab PDF Packet Generation            │
│ • Health polling via api.ts           │                                             │ • Fixture Store: data/fixtures/cases.json    │
└───────────────────────────────────────┘                                             └──────────────────────────────────────────────┘
```

---

## 2. Prerequisites & Repository Structure

Before deploying, ensure you have:
- A [Vercel](https://vercel.com) account linked to your GitHub/GitLab/Bitbucket.
- A [Render](https://render.com) account linked to your Git provider.
- Optional: A [Google AI Studio](https://aistudio.google.com/) API Key (`GEMINI_API_KEY`) if using Gemini LLM narrative generation (the system automatically falls back to deterministic rule-based narratives if omitted).

### Directory Layout
The repository contains both frontend and backend services:
```
.
├── backend/                  # FastAPI service
│   ├── api/                  # REST endpoints (/cases, /health, etc.)
│   ├── ml/                   # XGBoost model, calibration & feature schema
│   ├── services/             # Case store, packet generator, LLM narrative
│   ├── workflow/             # LangGraph state graph engine
│   ├── .env.example          # Backend environment variable template
│   ├── requirements.txt      # Python dependencies (fastapi, langgraph, xgboost, etc.)
│   └── main.py               # Application entry point, CORS, root /, and CLI
├── data/
│   ├── fixtures/             # 1,000 synthetic dispute cases (cases.json)
│   └── held_out/             # 200 validation dispute cases
├── frontend/                 # Next.js 15 web application
│   ├── src/                  # App Router pages, UI components, API client
│   ├── .env.example          # Frontend environment variable template
│   ├── .eslintrc.json        # ESLint configuration
│   ├── vercel.json           # Vercel deployment configuration
│   └── package.json          # Node.js dependencies and scripts
├── tests/                    # Backend pytest suite
├── .dockerignore             # Docker build context filters
├── Dockerfile                # Production containerfile for backend
├── render.yaml               # Render Blueprint specification
├── .env.example              # Unified environment variable reference
└── DEPLOYMENT.md             # This deployment manual
```

---

## 3. Backend Deployment on Render

Deploy the backend first so you have its production URL (`https://<service-name>.onrender.com`) ready to configure in the frontend.

### Option A: Automated Deployment via Render Blueprint (Recommended)

1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your Git repository containing DisputeGuard.
4. Render detects the `render.yaml` file in the repository root.
5. Review the service definition:
   - **Service Name**: `disputeguard-backend`
   - **Runtime**: `Python`
   - **Root Directory**: `.` (Repository root)
   - **Build Command**: `pip install --upgrade pip && pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
6. If using Google Gemini for narrative generation, set `GEMINI_API_KEY` under the prompted environment variables (it is marked `sync: false` for security).
7. Click **Apply**. Render will provision, build, and deploy the service.

### Option B: Manual Web Service Creation

If not using Blueprints:
1. In Render Dashboard, click **New +** > **Web Service**.
2. Connect your Git repository.
3. Configure the settings:
   | Setting | Value |
   |---|---|
   | **Name** | `disputeguard-backend` |
   | **Region** | Oregon (or closest to your users) |
   | **Branch** | `main` |
   | **Root Directory** | `.` *(CRITICAL: Must remain root so `backend` package and `data/` fixtures are accessible)* |
   | **Runtime** | `Python` |
   | **Build Command** | `pip install --upgrade pip && pip install -r backend/requirements.txt` |
   | **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Free (or Starter/Standard) |
4. Expand **Advanced**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: `Yes`
5. Add the following **Environment Variables**:
   | Variable | Recommended Production Value | Description |
   |---|---|---|
   | `PYTHON_VERSION` | `3.12.5` | Pinned Python runtime |
   | `ENVIRONMENT` | `production` | Disables debug reloading |
   | `BACKEND_HOST` | `0.0.0.0` | Container host binding |
   | `ALLOWED_ORIGIN_REGEX` | `^https://.*\.vercel\.app$` | Matches all Vercel preview & production URLs |
   | `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Optional comma-separated origins |
   | `GEMINI_API_KEY` | *(Your Gemini API key)* | Optional; falls back to rule-based templates if omitted |
6. Click **Create Web Service**.

### Option C: Docker Container Deployment

If you prefer containerized deployment:
1. In Render Dashboard, click **New +** > **Web Service**.
2. Set **Runtime** to `Docker`.
3. Set **Root Directory** to `.` and specify `Dockerfile` at the repository root.
4. Render will run the multi-stage build, install system dependencies (`libgomp1` for XGBoost), bundle `backend` and `data`, and run the container with dynamic `$PORT`.

### Verifying Backend Deployment

Once deployment completes, Render assigns a public URL (e.g., `https://disputeguard-backend.onrender.com`). Verify it with:

```bash
# 1. Root Service Metadata (HTTP 200)
curl -s https://<your-backend-service>.onrender.com/

# 2. Health Check (HTTP 200)
curl -s https://<your-backend-service>.onrender.com/health

# 3. Test Cases List (HTTP 200)
curl -s https://<your-backend-service>.onrender.com/cases | head -c 200
```

---

## 4. Frontend Deployment on Vercel

### Step-by-Step Vercel Setup

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import your Git repository.
4. In the **Configure Project** screen:
   - **Project Name**: `disputeguard-frontend` (or your choice).
   - **Framework Preset**: `Next.js` (automatically detected).
   - **Root Directory**: Click **Edit** and select **`frontend`** *(CRITICAL: The Next.js project is located in the `frontend` subfolder)*.
   - **Build and Output Settings**:
     - Build Command: `next build` (or leave default enabled)
     - Output Directory: `.next` (default)
     - Install Command: `npm install` (default)
5. Under **Environment Variables**, add:
   | Key | Value | Target Environments |
   |---|---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-backend-service>.onrender.com` | Production, Preview, Development |
6. Click **Deploy**.
7. Vercel will install dependencies, compile the TypeScript source, generate static pages, and produce an optimized edge deployment.

---

## 5. Environment Variables Reference

### Frontend (`frontend/.env.example`)
| Variable | Required | Default / Example | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes (in prod) | `http://localhost:8000` (local)<br>`https://disputeguard-backend.onrender.com` (prod) | Base URL of the DisputeGuard FastAPI backend. Trailing slashes are automatically normalized. |

### Backend (`backend/.env.example`)
| Variable | Required | Default / Example | Purpose |
|---|---|---|---|
| `PORT` | Auto (Render) | `8000` | Dynamic port assigned by Render hosting platform. |
| `BACKEND_HOST` | No | `0.0.0.0` | Interface to bind the Uvicorn web server to. |
| `BACKEND_PORT` | No | `8000` | Fallback port if `$PORT` is not defined. |
| `ENVIRONMENT` | No | `production` | Set to `production` in production; disables live reload. |
| `ALLOWED_ORIGIN_REGEX` | No | `^https://.*\.vercel\.app$` | Regular expression matching Vercel preview and production domains. |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of additional permitted web origins. |
| `GEMINI_API_KEY` | No | `AIzaSy...` | Optional API key for Google Gemini narrative generation. |

---

## 6. Local Build & Run Verification

To test the entire production build locally before triggering cloud deployments:

### Backend Local Verification
```powershell
# 1. Activate Python virtual environment
.venv\Scripts\Activate.ps1

# 2. Run backend test suite (unit tests, workflow tests, deployment & CORS tests)
pytest

# 3. Test CORS and endpoints with Python TestClient
python -c "
from fastapi.testclient import TestClient
from backend.main import app

c = TestClient(app)
assert c.get('/').status_code == 200
assert c.get('/health').status_code == 200
res = c.options('/health', headers={'Origin': 'https://disputeguard.vercel.app', 'Access-Control-Request-Method': 'GET'})
assert res.status_code == 200
assert res.headers.get('access-control-allow-origin') == 'https://disputeguard.vercel.app'
print('Backend local verification PASSED!')
"

# 4. Start local backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend Local Verification
```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Run linter (must pass non-interactively)
npm run lint

# 3. Run production build
npm run build

# 4. Start production server locally
npm run start
```

---

## 7. Troubleshooting & Operational FAQ

### 1. CORS Preflight Failures (`No 'Access-Control-Allow-Origin' header is present`)
- **Cause**: The browser sent an `OPTIONS` preflight request from a domain that does not match `allow_origins` or `allow_origin_regex`.
- **Solution**:
  - `backend/main.py` is configured with `allow_origin_regex=r"^https://.*\.vercel\.app$"`, covering all `*.vercel.app` production and preview URLs.
  - If you use a custom domain (e.g., `https://disputes.yourmerchant.com`), add it to `ALLOWED_ORIGINS` in Render environment variables:
    `ALLOWED_ORIGINS=https://disputes.yourmerchant.com,http://localhost:3000`

### 2. Mixed Content Security Blocks
- **Cause**: Vercel serves the frontend over `https://`, but `NEXT_PUBLIC_API_URL` was configured with `http://`.
- **Solution**: Always use `https://<service-name>.onrender.com` in Vercel environment settings. Browsers automatically block insecure HTTP subresource requests from HTTPS pages.

### 3. Trailing Slash / 404 / 307 Redirects
- **Cause**: An extra trailing slash in the base URL (`https://...onrender.com/`) causing double slashes like `https://...onrender.com//cases`.
- **Solution**: `frontend/src/lib/api.ts` automatically strips trailing slashes via `.replace(/\/+$/, '')`. You can safely enter the Render URL with or without a trailing slash.

### 4. Render Free-Tier Cold Starts (~50-second Delay)
- **Cause**: Render free-tier web services spin down after 15 minutes of inactivity. The initial incoming request triggers a spin-up, taking 30–50 seconds.
- **Behavior**: The dashboard health badge may show "Checking..." or temporarily fail on the very first visit after a spin-down.
- **Solution**: For zero-downtime production deployments, upgrade the Render instance to the **Starter** ($7/mo) tier or configure an external uptime monitor (e.g. UptimeRobot) to ping `GET /health` every 10 minutes.

### 5. `ModuleNotFoundError: No module named 'backend'` on Render
- **Cause**: The Render Web Service **Root Directory** was incorrectly set to `backend` instead of `.` (root).
- **Solution**: DisputeGuard uses absolute package namespace imports (`from backend.api...`). The Render Root Directory **must** be set to `.` (the repository root), and the start command must be `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

### 6. Interactive ESLint Prompt Blocks CI/CD
- **Cause**: Next.js 15 prompts for ESLint configuration if no `.eslintrc.json` is detected.
- **Solution**: `frontend/.eslintrc.json` is provided with `{"extends": "next/core-web-vitals"}`, ensuring non-interactive builds exit cleanly with code 0.
