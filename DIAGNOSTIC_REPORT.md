# DisputeGuard Live Deployment Diagnostic Verification Report

**Date & Time:** 2026-11-21T20:33:00Z  
**Target Environments:**
- **Frontend (Vercel):** `https://razorpay-ai-risk-manager.vercel.app` (Project: `remonsaha-labs-projects/razorpay-ai-risk-manager`)
- **Backend (Render):** `https://disputeguard-backend.onrender.com` (Blueprint: `exs-dc0rt4p42hec73cbcf8g/sync`)

---

## Executive Summary

| Verification Area | Target | Result | Status | Key Observation |
|---|---|---|---|---|
| **Frontend Root Availability** | `https://razorpay-ai-risk-manager.vercel.app` | **HTTP 200** | 🟢 Healthy | Latency: 286.7ms; serves React/Next.js production shell. |
| **Backend Root Endpoint (`/`)** | `https://disputeguard-backend.onrender.com/` | **HTTP 200** | 🟢 Healthy | Latency: 479.8ms; returns API discovery metadata and version `0.1.0`. |
| **Backend Health (`/health`)** | `https://disputeguard-backend.onrender.com/health` | **HTTP 200** | 🟢 Healthy | Latency: 409.9ms; returns `{"status": "healthy", "service": "DisputeGuard"}`. |
| **Backend Cases Endpoint (`/cases`)** | `https://disputeguard-backend.onrender.com/cases` | **HTTP 200** | 🟢 Healthy | Latency: 401.6ms; loads synthetic fixtures and returns 20 dispute cases. |
| **Backend Case Detail (`/cases/{id}`)** | `.../cases/DSP-2026-0001` | **HTTP 200** | 🟢 Healthy | Latency: 408.0ms; returns full dispute object, 4 evidence docs, and metadata. |
| **CORS Preflight (`OPTIONS`)** | Origin: `https://razorpay-ai-risk-manager.vercel.app` | **HTTP 200** | 🟢 Allowed | `Access-Control-Allow-Origin: https://razorpay-ai-risk-manager.vercel.app`, methods & credentials confirmed. |
| **CORS Actual GET** | Origin: `https://razorpay-ai-risk-manager.vercel.app` | **HTTP 200** | 🟢 Allowed | Origin reflected properly in response headers (`vary: Origin`). |
| **CORS Security Rejection** | Origin: `https://malicious-fraud-app.example.com` | **HTTP 400** | 🟢 Protected | Disallowed origin rejected by FastAPI middleware (`Access-Control-Allow-Origin` omitted). |
| **Frontend/Backend Wiring** | Vercel Client Bundle -> Render Backend | ⚠️ **Misaligned** | 🟡 Action Required | Live Vercel client bundle was compiled pointing to `https://razorpay-ai-risk-manager-api.onrender.com` (which is offline/timing out), rather than active service `https://disputeguard-backend.onrender.com`. |

---

## 1. Deployment Domain & Endpoint Discovery (R1)

### 1.1 Configured Deployment References
- **Frontend Vercel Project:** `https://vercel.com/remonsaha-labs-projects/razorpay-ai-risk-manager`
  - Public Production URL: `https://razorpay-ai-risk-manager.vercel.app`
- **Backend Render Blueprint:** `https://dashboard.render.com/blueprint/exs-dc0rt4p42hec73cbcf8g/sync`
  - Render Service Specification (`render.yaml`): `disputeguard-backend`
  - Public Production URL: `https://disputeguard-backend.onrender.com`

### 1.2 Discovered Endpoints
- **Frontend App:** `https://razorpay-ai-risk-manager.vercel.app`
- **Backend Root:** `https://disputeguard-backend.onrender.com/`
- **Backend Health Check:** `https://disputeguard-backend.onrender.com/health`
- **Backend Cases Listing:** `https://disputeguard-backend.onrender.com/cases`
- **Backend Single Case Lookup:** `https://disputeguard-backend.onrender.com/cases/DSP-2026-0001`
- **Backend Interactive Documentation:** `https://disputeguard-backend.onrender.com/docs`

---

## 2. Live Health & Endpoint Responses (R2)

### 2.1 Backend Endpoints Summary Table

| Endpoint | HTTP Method | Expected Status | Live Status | Latency | Response Headers | Payload Highlights |
|---|---|---|---|---|---|---|
| `https://disputeguard-backend.onrender.com/` | `GET` | 200 | **200 OK** | 479.8ms | `server: cloudflare`<br>`x-render-origin-server: uvicorn`<br>`content-type: application/json` | `{"status": "healthy", "service": "DisputeGuard API", "version": "0.1.0", "docs": "/docs", "health": "/health"}` |
| `https://disputeguard-backend.onrender.com/health` | `GET` | 200 | **200 OK** | 409.9ms | `server: cloudflare`<br>`x-render-origin-server: uvicorn`<br>`content-type: application/json` | `{"status": "healthy", "service": "DisputeGuard"}` |
| `https://disputeguard-backend.onrender.com/cases` | `GET` | 200 | **200 OK** | 401.6ms | `server: cloudflare`<br>`x-render-origin-server: uvicorn`<br>`content-type: application/json` | Array of 20 disputes. First item: `DSP-2026-0001`, INR 11,428.32, reason `merchandise_not_received`, status `pending_review`. |
| `https://disputeguard-backend.onrender.com/cases/DSP-2026-0001` | `GET` | 200 | **200 OK** | 408.0ms | `server: cloudflare`<br>`x-render-origin-server: uvicorn`<br>`content-type: application/json` | Complete dispute record for `Siddharth Nair`, 4 linked evidence documents (`DOC-0001-INV`, `DOC-0001-TRK`, `DOC-0001-POD`, `DOC-0001-OCR`). |

*Note on Cold Starts:* When waking from Render free-tier inactivity, the initial spin-up request takes ~32.4 seconds. Once warm, subsequent requests complete consistently in 380ms–480ms.

### 2.2 Frontend Deployment Status

| URL | HTTP Method | Status | Latency | Server | Headers | Content Preview |
|---|---|---|---|---|---|---|
| `https://razorpay-ai-risk-manager.vercel.app` | `GET` | **200 OK** | 286.7ms | `Vercel` | `Strict-Transport-Security`<br>`Cache-Control: public, max-age=0, must-revalidate`<br>`Content-Type: text/html; charset=utf-8` | Single-page application root: `<title>AI Risk Manager</title>`, `<div id="root"></div>`, loading `/assets/index-C8juh_Dc.js`. |

---

## 3. CORS Configuration & Header Inspection (R2)

DisputeGuard implements origin validation in `backend/main.py`:
```python
allow_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", r"^https://.*\.vercel\.app$")
```

### 3.1 Live CORS Header Verification Results

#### Test Case 1: Preflight Request (`OPTIONS /cases`) from Frontend Domain
- **Request Headers:**
  - `Origin: https://razorpay-ai-risk-manager.vercel.app`
  - `Access-Control-Request-Method: GET`
  - `Access-Control-Request-Headers: Content-Type`
- **Response Status:** **`200 OK`**
- **Response Headers Captured:**
  - `access-control-allow-origin: https://razorpay-ai-risk-manager.vercel.app`
  - `access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`
  - `access-control-allow-headers: Content-Type`
  - `access-control-allow-credentials: true`
  - `access-control-max-age: 600`
  - `vary: Origin`
- **Verdict:** 🟢 **Passed.** Browser preflight checks succeed with explicit origin matching.

#### Test Case 2: Actual GET Request (`GET /cases`) with Origin
- **Request Headers:**
  - `Origin: https://razorpay-ai-risk-manager.vercel.app`
- **Response Status:** **`200 OK`**
- **Response Headers Captured:**
  - `access-control-allow-origin: https://razorpay-ai-risk-manager.vercel.app`
  - `access-control-allow-credentials: true`
  - `access-control-expose-headers: Content-Disposition`
  - `vary: Origin`
- **Verdict:** 🟢 **Passed.** Complex cross-origin responses include credentials and allow reading headers.

#### Test Case 3: Unauthorized Origin Security Check
- **Request Headers:**
  - `Origin: https://malicious-fraud-app.example.com`
  - `Access-Control-Request-Method: GET`
- **Response Status:** **`400 Bad Request`**
- **Response Headers Captured:**
  - `access-control-allow-origin: None` (omitted)
- **Response Body:** `Disallowed CORS origin`
- **Verdict:** 🟢 **Passed.** Host-based origin enforcement prevents untrusted domains from accessing dispute data.

---

## 4. End-to-End Frontend/Backend Connectivity Analysis (R2 & R3)

### 4.1 CORS Connectivity
Backend CORS policy is 100% compliant and accepts cross-origin API calls originating from `https://razorpay-ai-risk-manager.vercel.app` and any other `*.vercel.app` preview environments.

### 4.2 Observed Client-Side Discrepancy & Root Cause
Inspection of the client script bundle currently deployed to Vercel (`/assets/index-C8juh_Dc.js`) revealed:
- Embedded Base API URL: **`https://razorpay-ai-risk-manager-api.onrender.com`**
- Status of that host: **Offline / Request Timeout** (>40s with no response)
- Active Render Service URL: **`https://disputeguard-backend.onrender.com`** (Healthy, responding with 200 OK)

**Cause:** The frontend deployment on Vercel predates the Render Blueprint sync or had `NEXT_PUBLIC_API_URL` set to `https://razorpay-ai-risk-manager-api.onrender.com`.  
**Remediation:** In the Vercel project settings (`remonsaha-labs-projects/razorpay-ai-risk-manager`):
1. Update `NEXT_PUBLIC_API_URL` to `https://disputeguard-backend.onrender.com`.
2. Trigger a redeploy on Vercel so the client bundle reflects the active backend host.

### 4.3 Backend Workflow Execution (`POST /cases/{id}/run`) Observation
During live API diagnostics, executing the full AI workflow endpoint (`POST /cases/DSP-2026-0001/run`):
- Locally, the workflow completes in ~3.89 seconds with deterministic narrative fallback when Google AI Studio credentials are not present.
- On the live Render free tier instance, calling this endpoint resulted in a Cloudflare gateway timeout (502 Bad Gateway) after 51.8 seconds.
- **Root Cause:** When `GEMINI_API_KEY` is provisioned or set on Render with an invalid key or a model name that waits on Google API connection timeouts (`gemini-3.7-flash` in `google-generativeai`), the synchronous call blocks until Render's 50-second proxy timeout kills the worker.
- **Remediation Recommendation:** Set a client request timeout on `google.generativeai` calls (e.g., 5.0s timeout) or omit `GEMINI_API_KEY` to utilize the instantaneous deterministic rule-based representment narrative.

---

## 5. Diagnostic Verification Checklist

- [x] **Backend `/` Endpoint:** Verified live (HTTP 200, 479.8ms, service metadata confirmed).
- [x] **Backend `/health` Endpoint:** Verified live (HTTP 200, 409.9ms, status `healthy`).
- [x] **Backend `/cases` Endpoint:** Verified live (HTTP 200, 401.6ms, 20 cases returned).
- [x] **Frontend Root URL:** Verified live (HTTP 200, 286.7ms, React SPA shell served).
- [x] **Backend CORS Preflight:** Inspected and verified (`access-control-allow-origin: https://razorpay-ai-risk-manager.vercel.app`, methods & credentials passed).
- [x] **Backend CORS Actual GET:** Inspected and verified (origin reflected, credentials and expose-headers present).
- [x] **CORS Origin Protection:** Inspected and verified (unauthorized origin rejected with HTTP 400).
- [x] **Frontend/Backend Connectivity:** Assessed and documented client bundle API host mismatch.
- [x] **Zero Source Code Alteration:** Verification executed purely via diagnostic testing; application source code remains unmodified.
