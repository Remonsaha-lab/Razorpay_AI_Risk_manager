# DisputeGuard — Implementation Guide

This second README is the build guide for [README.md](README.md). It deliberately contains no application source code. It describes what to build, where it belongs, and the commands to run.

## Goal and safety boundaries

Build a local-first prototype for one loss class: **card-not-present “merchandise/services not received” disputes for shipped physical goods**.

```text
Select synthetic case → extract document facts → deterministically verify facts
→ calculate completeness and economics → recommend action
→ draft only evidence-cited claims → human approval → PDF packet
```

- Use clearly labelled synthetic data only.
- AI may extract information and draft wording; it must never make the final verification or policy decision.
- A human approves any contest packet.
- Do not use real payment credentials, customer data, or live dispute submission.
- Do not claim official Razorpay/card-scheme compliance.

## Target repository layout

Create folders only when their milestone needs them.

```text
Razorpay_project/
├── README.md                     # Existing product brief
├── IMPLEMENTATION_GUIDE.md       # This guide
├── .gitignore
├── .env.example                  # Variable names only; no real values
├── frontend/                     # Next.js + TypeScript dashboard
├── backend/
│   ├── api/                      # FastAPI routes and response wiring
│   ├── domain/                   # Pydantic entities, enums, decision types
│   ├── workflow/                 # Ordered workflow/state transitions
│   ├── services/                 # Parsing, OCR, LLM wrapper, PDF service
│   ├── validators/               # IDs, amounts, dates, consistency
│   └── policies/                 # Versioned demo-scoped JSON rules
├── data/
│   ├── fixtures/                 # Development synthetic cases/documents
│   └── held_out/                 # Untouched synthetic test cases
├── evals/                        # Evaluation runner and metrics
├── tests/                        # Unit and end-to-end tests
├── docs/                         # Architecture, evaluation, decisions, demo script
└── docker-compose.yml            # Add only after local stability
```

| Area | Owns |
|---|---|
| `backend/api/` | HTTP input/output, never core decisions |
| `backend/domain/` | Dispute, evidence, claim, and decision shapes |
| `backend/validators/` | Exact matches and contradiction checks |
| `backend/workflow/` | The ordered end-to-end run |
| `backend/services/` | Parsing, OCR, provider wrapper, packet generation |
| `backend/policies/` | Evidence requirements, thresholds, assumptions |
| `data/` | Synthetic documents/cases only |
| `evals/` | Held-out evaluation and reported metrics |

## Prerequisites and setup

Install Git, Node.js 20 LTS or newer, Python 3.11 or newer, and a browser. Verify them:

```powershell
git --version
node --version
npm --version
python --version
```

Initialize Git when needed:

```powershell
git init
git status
```

### Frontend

On the scaffold day, create the UI. Choose TypeScript, ESLint, Tailwind, and the App Router in the prompts.

```powershell
npx create-next-app@latest frontend
cd frontend
npm run dev
```

Confirm the starter screen at `http://localhost:3000`, then stop it with `Ctrl+C`. Add UI dependencies only while building the dashboard:

```powershell
npx shadcn@latest init
npm install lucide-react
```

Do not add authentication, a state-management library, charts, or extra component libraries unless a concrete requirement needs one.

### Backend

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic pytest httpx
pip freeze > backend\requirements.txt
```

After creating the backend application entry point, run it:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Inspect endpoints at `http://127.0.0.1:8000/docs`. If activation is blocked, use this current-shell-only setting:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Install only when the milestone needs it

| Purpose | Command | Add when |
|---|---|---|
| Digital PDF parsing | `pip install pymupdf` | Invoice/POD parsing |
| OCR candidate matching | `pip install rapidfuzz` | Noisy-ID demo; never final validation |
| PDF packet | `pip install reportlab` | Packet milestone |
| Environment variables | `pip install python-dotenv` | First AI-provider configuration |
| Evaluation | `pip install pandas scikit-learn` | Evaluation milestone |
| OCR engine | Follow one engine’s official install instructions | Only if saved synthetic OCR text is inadequate |

Pick **one** OCR engine. Avoid adding agent frameworks, an ORM, Docker, cloud deployment, and multiple OCR engines to the critical path.

## Implementation sequence

### 1. Data and policy model

In `backend/domain/`, define a Dispute (ID, amount, reason, transaction/order IDs, dates/status); EvidenceDocument (type, source, page, extraction method/confidence, raw text); EvidenceClaim (field, raw/normalized values, source, verification status/reason); and Decision (action, completeness, evidence-strength estimate, expected value, review flag, reasons).

Use exactly these initial actions: `CONTEST`, `REQUEST_MORE_EVIDENCE`, and `ACCEPT_LOSS`. A contradiction should set `review_required`, not create an unmeasured action. Create a versioned JSON policy in `backend/policies/` that lists required evidence, required checks, thresholds, and an explicit synthetic-demo scope note.

### 2. Extraction is separate from verification

Extraction reads fixture text, PDFs, OCR, or a bounded model and returns fields with provenance. It does not decide whether a field is correct. The deterministic validator must:

1. Normalize identifiers conservatively and compare order IDs exactly.
2. Compare money with exact decimal/currency-aware values, never float equality.
3. Confirm delivery has an independent carrier event before the response deadline.
4. Surface address, time, or amount differences as contradictions.
5. Use fuzzy/OCR similarity only to propose a correction candidate.
6. Verify a corrected tracking ID only after independent carrier confirmation.

Retain raw value, normalized value, document/page/source, verification status, and reason. This enables source-cited UI and PDF content.

### 3. Deterministic decision engine

Implement small typed steps:

```text
load policy → extract claims → validate claims → assess completeness
→ assess contradictions → estimate evidence strength → calculate EV → decide
```

Completeness is verified required evidence divided by required evidence. Keep thresholds in policy configuration. Start with an explainable evidence-strength score; do not call it a calibrated probability without training and validation. Record positive and negative factors.

Recommend contest only when required evidence is verified, no contradictions remain, the policy threshold is met, and contest EV exceeds accept EV. Request evidence only when it can arrive before the deadline; otherwise accept loss. Display all economic assumptions.

### 4. Add bounded AI late

Use one provider wrapper only after the deterministic route works. Its narrow jobs are structured extraction for low-confidence text and a concise narrative assembled only from approved claim IDs. Require structured outputs and audit each factual sentence afterward. Every sentence must point to an approved claim/source. The model cannot set verification status, override rules, calculate the decision, or invent carrier confirmation.

### 5. Reviewer-first UI

Build one dashboard before multiple pages. Show case ID, amount, reason and deadline; recommendation/review state/completeness/estimate/EV; evidence checklist; factors/assumptions; source-cited narrative/audit; and packet generation only for eligible human-approved contests. Start with the strong and corrupted-tracking-ID fixtures.

### 6. Packet, then evaluation

The PDF packet contains case summary, approved narrative, decision, evidence index, and document/page citations. Label it **submission-ready prototype packet**; do not add live submission.

Create 80–100 synthetic cases. Separate development and held-out sets before tuning prompts/thresholds. On held-out data report extraction accuracy, identifier-verification accuracy, contest precision/recall, false-contest/false-accept rates, claim-grounding rate, review rate, and synthetic net value.

## Day-by-day plan: 23 August–4 September 2026

Today is **23 August 2026**. End each day with a runnable path, a small commit, and a short decision note in `docs/decisions.md`.

| Date | Finish with | Work to do |
|---|---|---|
| **23 Aug** | Local scaffold | Initialize Git; scaffold frontend/backend; add `.gitignore` and `.env.example`; prove both servers launch. |
| **24 Aug** | Concrete scope | Create policy and 20 seed synthetic cases, including strong and corrupted-ID cases; define domain/provenance shapes. |
| **25 Aug** | Reliable validation | Load fixtures; validate IDs, amounts, dates, required evidence, and links; test success/failure paths. |
| **26 Aug** | Explainable evidence | Create claims with raw/normalized values, status/reason, and source location; calculate policy completeness. |
| **27 Aug** | Defensible decision | Implement strength factors, expected value, action selection, deadlines, review flag, and rationale. |
| **28 Aug** | End-to-end local demo | Build API routes and basic dashboard; select, run, and inspect both demo cases. |
| **29 Aug** | Auditable AI | Add one structured extraction/narrative wrapper only if necessary; enforce claim audit. |
| **30 Aug** | Packet + review | Generate cited PDF for eligible cases; add human approval; confirm no live submission path. |
| **31 Aug** | Frozen test data | Expand to 80–100 cases; isolate 20–25% held out; add evaluation runner/definitions. |
| **1 Sep** | Recorded measurements | Tune only on development cases; run held-out evaluation after freezing prompts/thresholds; document actual results. |
| **2 Sep** | Failure recovery story | Show the `O`/`0` near-match and deterministic block without carrier confirmation; capture screenshots. |
| **3 Sep** | Submission materials | Fresh-setup check; complete architecture/evaluation/demo docs; record the five-minute video. |
| **4 Sep** | Submission ready | Final smoke test, public-repo hygiene, verify links, submit before the 20:00 IST personal target; begin no new features. |

## Daily commands

Use the repository root for source control:

```powershell
git status
git add -A
git commit -m "Describe the completed milestone"
```

Run services in separate terminals:

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

```powershell
cd frontend
npm run dev
```

Run these once they exist, before committing:

```powershell
pytest
python -m evals.run_eval
npm run lint
npm run build
```

## Completion gates

1. **Scaffold:** both servers launch and the API returns a fixture.
2. **Verification:** correct IDs pass; wrong IDs/amounts, missing/late delivery, and unconfirmed OCR corrections fail with reasons.
3. **Decision:** all three actions follow visible policy/economic rules.
4. **Provenance:** every displayed fact has a document/source location.
5. **Narrative:** every factual sentence links to an approved claim.
6. **Evaluation:** held-out measurements run reproducibly and include false-positive cost.
7. **Demo:** strong and failure cases work end-to-end in under five minutes.
8. **Submission:** no secrets/real data, setup is documented, and limitations are explicit.

## Scope cuts if you fall behind

Preserve deterministic validation, failure recovery, and held-out metrics. Cut in this order:

1. Authentication, database infrastructure, and deployment; use local JSON/SQLite.
2. Dashboard polish, charts, filters, and extra screens.
3. Trained/calibrated model; use a labelled evidence-strength baseline.
4. Live OCR; use prepared synthetic OCR text with the noisy-ID case.
5. Docker; record a stable local demo.

## Final safety checklist

- [ ] All data is synthetic and visibly labelled.
- [ ] `.env.example` has names only; no secret is committed.
- [ ] Policies, thresholds, and assumptions are configuration, not UI constants.
- [ ] A near-match is never verified without independent confirmation.
- [ ] Amounts use exact decimal comparisons.
- [ ] AI cannot override verification, policy, economics, or human approval.
- [ ] Every packet/narrative fact has provenance.
- [ ] Held-out metrics are actual measurements, not targets.
- [ ] Docs describe a synthetic prototype, not legal advice or a live integration.
- [ ] The demo includes a happy path and safe failure path.

When you are ready, ask for a specific milestone, such as “guide me through the 23 August scaffold.” I will then guide the next small coding step and its commands without writing application code until you explicitly change that instruction.
