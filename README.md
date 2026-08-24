# DisputeGuard — Razorpay AI Buildathon Plan

> Evidence-grounded AI for chargeback decisioning and representment.

**Track:** 02 — AI Risk Manager  
**Application deadline:** **5 September 2026** (official page does not state a time)  
**Personal submission target:** **4 September 2026, 20:00 IST**  
**Build scope:** A defense-only prototype for one loss class: *card-not-present “merchandise/services not received” disputes for shipped physical goods.*

---

## 1. The project in one sentence

DisputeGuard ingests a dispute and its merchant evidence, verifies the evidence deterministically, recommends whether to **contest**, **request more evidence**, or **accept the loss** based on expected value, and produces a source-cited, submission-ready representment packet for cases that pass review.

The important design rule is:

> **The LLM explains evidence; deterministic rules verify evidence; policy and economics make the decision.**

This is not a system for identifying, targeting, or exploiting customers. It is strictly a merchant-side, post-dispute defense workflow.

## 2. Why this is the right Track 02 project

The Buildathon asks for a working detector, verifier, or auto-responder for one class of loss, with measured precision and recall on a held-out test set, plus an honest false-positive cost. DisputeGuard is intentionally scoped to meet that bar:

| Buildathon requirement | DisputeGuard proof |
|---|---|
| One concrete loss class | “Merchandise/services not received” disputes for shipped goods |
| Working verifier / responder | Evidence intake → validation → decision → evidence packet |
| Meaningful AI use | Structured extraction and constrained narrative generation with source grounding |
| Measured quality | Held-out synthetic evaluation set; decision precision, recall, false-contest and false-accept rates |
| Honest cost | Expected-value model and per-error rupee cost |
| Defense-only | No fraud-generation, evasion, targeting, or offensive capability |
| Failure recovery | Deliberately show an LLM accepting an OCR-corrupted tracking ID, then show deterministic validation blocking it |

## 3. Product scope: what to build and what not to build

### Must build (MVP)

1. Upload or select a synthetic dispute case.
2. Load a configurable evidence policy for the selected scheme/reason-code demo case.
3. Extract fields from invoice, proof-of-delivery (POD), shipment record, payment record, and optional customer communication.
4. Verify identifiers, amounts, timestamps, delivery status, and cross-document consistency.
5. Calculate evidence completeness, a calibrated/explicit win-probability estimate, expected value, and one of three actions:
   - `CONTEST`
   - `REQUEST_MORE_EVIDENCE`
   - `ACCEPT_LOSS`
6. Generate a concise evidence-backed narrative only for contestable cases.
7. Show citations/provenance for every factual claim in the narrative.
8. Generate a downloadable **submission-ready** PDF packet (do not claim production scheme compliance or autonomous live submission).
9. Run a held-out evaluation and show real metrics.

### Explicitly defer

- Live network/scheme dispute submission.
- Support for every card scheme, reason code, or jurisdiction.
- A production-grade fraud model trained on real customer data.
- Autonomous decisioning without a review threshold.
- A broad “multi-agent” system. A clear state machine is more credible and easier to demo.

## 4. Primary demo story

Use one strong case and one failure case. This makes the five-minute video memorable.

### Demo case A — evidence is strong

```text
Dispute: DSP-2026-001
Amount: ₹18,400
Reason: Merchandise/services not received
Respond-by: 04 Sep 2026, 18:00 IST

Evidence:
✓ Order and payment record
✓ Invoice
✓ Shipment record
✓ Proof of delivery
✓ Exact tracking-ID verification
✓ Carrier delivery event
✓ Delivery time before respond-by deadline
```

Expected screen result:

```text
Recommendation: CONTEST
Evidence completeness: 100%
Estimated P(win): 0.84
Expected value of contest: +₹14,180
Review state: Ready for human approval
```

Then open the submission-ready packet and show that each claim links to evidence.

### Demo case B — deliberate failure and recovery

```text
Invoice tracking ID: AWB98234710
Blurry POD OCR output: AWB9823471O
```

The baseline LLM may say “match” because the strings look similar. DisputeGuard must reject that as unverified:

```text
Exact match: failed
OCR correction candidate: O → 0
Carrier database confirmation: found / not found
Final status: VERIFIED only if carrier record confirms the corrected identifier
```

Pitch line:

> “We do not let the model grade its own homework.”

## 5. System architecture

```text
Dispute event + merchant documents
             │
             ▼
      Dispute router
  scheme • reason code • respond_by
             │
             ▼
   Policy/evidence requirement map
             │
             ▼
      Evidence harvester
 invoice • POD • shipment • payment • chat
             │
             ▼
 Text extraction / OCR fallback
             │
             ▼
  Deterministic evidence validator
 exact identifiers • date/order checks • amounts • completeness
             │
             ▼
       Evidence graph / provenance
             │
             ▼
  Win estimate + expected-value gate
             │
  ┌──────────┼──────────────┐
  ▼          ▼              ▼
CONTEST  REQUEST MORE    ACCEPT LOSS
          EVIDENCE
  │
  ▼
Constrained LLM narrative
  │
  ▼
Claim audit + human approval
  │
  ▼
Submission-ready evidence PDF
```

### State machine

```text
INGEST → LOAD_POLICY → EXTRACT → VERIFY → ASSESS_COMPLETENESS
      → ESTIMATE_OUTCOME → CALCULATE_EV → DECIDE
      → (CONTEST → DRAFT_NARRATIVE → AUDIT → PACKET | REQUEST | ACCEPT)
```

Use LangGraph only if it accelerates implementation. A plain typed Python workflow is fully acceptable if it is easier to test and demonstrate.

## 6. Recommended technology stack

Keep the stack small. The selection below optimizes for a reliable hackathon demo, not for maximum framework count.

| Layer | Recommended choice | Why it is here |
|---|---|---|
| Web app | Next.js, TypeScript, Tailwind CSS, shadcn/ui | Fast, polished case dashboard and review UI |
| API | FastAPI + Pydantic v2 | Typed request/response models, rapid iteration |
| Workflow | Typed Python functions; LangGraph optional | Transparent state transitions and testability |
| Database | SQLite for MVP; PostgreSQL only if deployment needs it | Avoid infrastructure risk before submission |
| PDF parsing | PyMuPDF | Extract text from digital PDFs quickly |
| OCR | PaddleOCR **or** Surya (choose one) | Read scanned PODs; do not maintain several OCR stacks |
| Vision fallback | One multimodal LLM, only for low-confidence OCR | Bounded use with a clear reason |
| LLM | OpenAI or Gemini via one provider wrapper | Structured extraction/narrative, not policy judgment |
| Fuzzy/OCR correction | Python `re`, `RapidFuzz`, confusion map | Generate a candidate; never use similarity alone to validate an ID |
| Win model | Transparent weighted baseline first; XGBoost only if time remains | A trustworthy baseline beats a rushed ML claim |
| Calibration | Isotonic regression / Platt scaling if the data supports it | Prevent “LLM confidence” from masquerading as probability |
| PDF packet | ReportLab | Submission-ready packet artifact |
| Tests/evals | Pytest + JSONL fixtures | Reproducible held-out evaluation |
| Deployment | Docker Compose; Vercel/Render optional | Use deployment only after the local demo is dependable |
| Observability | Structured logs; Langfuse optional | Keep prompt traces and decision reasons visible |

### Do not make these critical-path dependencies

- A vector database or generic RAG pipeline.
- LiteLLM, unless you already use it comfortably.
- Async ORM complexity.
- More than one OCR engine.
- Real payment credentials or live customer data.

## 7. Data model and policy model

Use synthetic, clearly labelled data. Never manufacture a claim of real merchant performance.

### Core entities

```python
Dispute(
  id, amount_inr, scheme, reason_code, reason_description,
  created_at, respond_by, transaction_id, order_id, status
)

EvidenceDocument(
  id, dispute_id, type, source_file, page_number,
  extraction_method, extraction_confidence,
  raw_text, source_timestamp
)

EvidenceClaim(
  id, document_id, field, raw_value, normalized_value,
  verification_status, verification_reason,
  source_location, linked_entity_id
)

Decision(
  dispute_id, action, evidence_completeness, win_probability,
  expected_value_inr, review_required, rationale
)
```

### Evidence-policy configuration

Keep rules external and explicitly demo-scoped. Do **not** hard-code remembered card-scheme mappings or claim universal compliance.

```json
{
  "policy_id": "demo_shipped_goods_not_received_v1",
  "scope_note": "Synthetic demo policy; configurable by scheme, reason code and jurisdiction.",
  "required_evidence": [
    "order_record",
    "payment_record",
    "invoice",
    "proof_of_delivery",
    "carrier_delivery_event"
  ],
  "required_checks": [
    "transaction_amount_match",
    "order_id_match",
    "exact_tracking_id_verification",
    "delivery_before_respond_by"
  ]
}
```

### Evidence verification rules

| Field | Rule | Invalid example |
|---|---|---|
| Order ID | Normalize then exact match across invoice/order record | `ORD-1208` vs `ORD-1280` |
| Tracking ID | Exact match; OCR correction permitted only with carrier confirmation | `AWB...10` vs `AWB...11` |
| Amount | Use currency-normalized exact decimal comparison | ₹18,400 vs ₹18,040 |
| Delivery time | Verified carrier time must exist and be before `respond_by` | Timestamp missing or after deadline |
| Address | Compare normalized required fields; surface discrepancy | Different pincode or city |
| Narrative claim | Must be generated from an approved claim ID | A fact without a source |

## 8. Decision and economics

### Evidence completeness

```text
completeness = verified_required_evidence / total_required_evidence
```

Examples:

- `< 0.60`: normally `REQUEST_MORE_EVIDENCE` if deadline permits; otherwise `ACCEPT_LOSS`.
- `0.60–0.84`: human review.
- `≥ 0.85` with no contradictions: eligible for expected-value evaluation.

Keep thresholds configurable and state that they are prototype parameters.

### Win probability

For the MVP, use an explainable score, then normalize it to a probability. Example features:

```text
+ verified proof of delivery
+ exact shipment/tracking match
+ verified delivery event
+ complete order/payment linkage
+ deadline margin
- missing required evidence
- contradictory identifiers
- contradictory amounts
- unresolved OCR uncertainty
```

If there is enough synthetic labelled data, train a small XGBoost model and calibrate its held-out outputs. Otherwise, call it an **evidence-strength estimate**, not a learned win probability.

### Expected-value decision

Use a transparent model:

\[
EV_{contest} = P(win) \times R - (1-P(win)) \times C_{loss} - C_{human} - C_{submission}
\]

Where:

- `R`: recoverable disputed amount.
- `C_loss`: cost if the contest fails (prototype assumption; document it).
- `C_human`: analyst/review cost.
- `C_submission`: processing cost.

Compare it with:

\[
EV_{accept} = -R
\]

Decision rule:

```text
if required evidence is missing and it can be obtained before respond_by:
    REQUEST_MORE_EVIDENCE
elif evidence has unresolved contradiction:
    HUMAN_REVIEW or ACCEPT_LOSS
elif EV_contest > EV_accept and P(win) >= contest_threshold:
    CONTEST
else:
    ACCEPT_LOSS
```

Do not present assumptions as Razorpay fees or official scheme rules. Label them as synthetic evaluation parameters.

## 9. Evaluation plan — non-negotiable

Track 02 will be much stronger if the evaluation is reproducible and held out.

### Dataset design

Create **80–100 fully synthetic cases**. Reserve 20–25% before tuning any thresholds or prompts.

| Segment | Suggested cases | Expected correct action |
|---|---:|---|
| Complete, consistent evidence | 20 | Contest |
| Missing POD or carrier event | 15 | Request evidence / accept |
| Wrong identifier | 15 | Reject evidence; request/accept |
| OCR corruption | 10 | Validate only when independently confirmed |
| Contradictory dates/amounts | 10 | Human review / accept |
| Low-value, weak-economics cases | 10 | Accept |
| Deadline-critical cases | 10 | Decision reflects `respond_by` |
| Edge/borderline cases | 10 | Human review |

### Metrics to report

Report results only on the held-out test set after thresholds and prompts are frozen.

| Metric | Meaning |
|---|---|
| Evidence extraction accuracy | Extracted fields correct / checked fields |
| Identifier verification accuracy | Correctly verified or rejected IDs |
| Contest precision | Of cases recommended to contest, how many should be contested? |
| Contest recall | Of cases that should be contested, how many did the system select? |
| False-contest rate | Weak cases incorrectly sent to contest |
| False-accept rate | Strong cases incorrectly accepted as loss |
| Packet claim-grounding rate | Narrative claims that have valid provenance |
| Net economic value | Synthetic batch outcome under stated assumptions |
| Human-review rate | Share of cases safely escalated rather than over-automated |

### False-positive cost

For this product, a false positive is primarily a **false contest**: the system recommends fighting a case that lacks valid evidence or has poor economics. Its cost is:

```text
failed-contest cost + review time + processing/submission cost + opportunity cost
```

Also show the countervailing false negative: a **false accept**, where a winnable case is abandoned and the merchant loses recoverable revenue.

### Results template (fill only with real measurements)

```text
Held-out cases: __
Contest precision: __
Contest recall: __
Identifier verification accuracy: __
False-contest rate: __
False-accept rate: __
Claim-grounding rate: __
Net simulated improvement vs “contest every case”: ₹__
```

## 10. Build plan to submission

Today is **22 August 2026**. Treat 5 September as a contingency day, not a development day.

| Date | Milestone | Deliverable / definition of done |
|---|---|---|
| **22 Aug** | Lock scope | Project name, one loss class, one policy config, repository created, README committed |
| **23 Aug** | Scaffold | FastAPI and Next.js run locally; typed sample dispute endpoint; clean folder structure |
| **24 Aug** | Synthetic fixtures | 20 seed cases with documents/JSON; one strong and one corrupted-ID demo case |
| **25 Aug** | Parsing and validation | Invoice/POD parsing; exact IDs, date, amount and linkage checks; Pytest tests |
| **26 Aug** | Evidence model | Provenance/claim data structures; completeness calculation; policy loader |
| **27 Aug** | Decision engine | Explainable score, EV formulas, `CONTEST`/`REQUEST`/`ACCEPT`; assumptions visible |
| **28 Aug** | Workflow and UI | End-to-end run from case selection to decision; dashboard displays reasons, deadline, evidence table |
| **29 Aug** | Constrained AI | Structured extraction fallback and sourced narrative generation; claim audit blocks unsourced text |
| **30 Aug** | Packet and review | Submission-ready PDF; human approval screen; no real submission endpoint |
| **31 Aug** | Dataset and evals | Expand to 80–100 cases; freeze 20–25% held-out; write metrics script |
| **1 Sep** | Measure and tune | Run held-out evaluation once; tune only on development cases; record final results honestly |
| **2 Sep** | Failure recovery | Script baseline LLM/OCR mismatch demonstration; capture before/after metrics and screenshots |
| **3 Sep** | Polish + pitch | Deploy or make Docker demo reliable; record 5-minute video; verify README instructions from a fresh clone |
| **4 Sep** | Submit buffer | Public repo, video unlisted link, application answers, final smoke test; submit by 20:00 IST |
| **5 Sep** | Contingency only | Fix a submission issue or re-submit if needed; do not start new features |

### Daily operating rule

Each day ends with:

1. A working demo path, even if incomplete.
2. One small commit with a clear message.
3. A screenshot/GIF or terminal output showing what now works.
4. A short note in `docs/decisions.md`: what was chosen, what was rejected, and why.

### Scope-cut order if behind schedule

Cut in this order; never cut metrics, deterministic checks, or the failure story.

1. Database and authentication → use local JSON/SQLite.
2. Fancy dashboard filters/charts.
3. XGBoost/calibration → use documented evidence-strength baseline.
4. OCR fallback → use pre-extracted synthetic text plus one saved noisy example.
5. Deployment → use Docker/local recording, while keeping the public repo runnable.

## 11. Repository layout

```text
disputeguard/
├── frontend/                    # Next.js UI
├── backend/
│   ├── api/                     # FastAPI routes
│   ├── domain/                  # Pydantic models and decision types
│   ├── workflow/                # Typed workflow/state machine
│   ├── services/                # parsing, OCR, LLM, packet service
│   ├── validators/              # identifiers, amounts, time, consistency
│   └── policies/                # demo scoped evidence-requirement JSON
├── data/
│   ├── fixtures/                # synthetic development cases
│   └── held_out/                # never tune prompts/thresholds against this
├── evals/
│   ├── run_eval.py
│   └── metrics.py
├── tests/
├── docs/
│   ├── architecture.md
│   ├── evaluation.md
│   ├── decisions.md
│   └── demo-script.md
├── docker-compose.yml
├── .env.example                 # names only; no keys
└── README.md
```

## 12. API and UI checklist

### Backend endpoints

```text
GET  /cases
GET  /cases/{case_id}
POST /cases/{case_id}/run
GET  /cases/{case_id}/decision
GET  /cases/{case_id}/evidence
POST /cases/{case_id}/packet
GET  /evals/latest
```

### Single-page dashboard layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Dispute DSP-2026-001  •  ₹18,400  •  respond by 18:00 IST  │
├─────────────────────────────┬───────────────────────────────┤
│ Recommendation              │ Evidence checklist            │
│ CONTEST                     │ ✓ invoice                     │
│ P(win): 0.84                │ ✓ POD                         │
│ EV: +₹14,180                │ ✓ carrier event               │
│ Human approval required     │ ✓ exact tracking match        │
├─────────────────────────────┴───────────────────────────────┤
│ Why this decision: evidence/EV factors and assumptions       │
├─────────────────────────────────────────────────────────────┤
│ Source-cited narrative / claim audit / Generate packet       │
└─────────────────────────────────────────────────────────────┘
```

## 13. Five-minute pitch structure

Target 4:30–4:45, leaving space for natural pauses.

| Time | What to say and show |
|---:|---|
| 0:00–0:30 | Problem: chargebacks consume margin and manual review. Merchants need to decide whether fighting is rational, not simply generate a letter. |
| 0:30–1:00 | Product and scope: DisputeGuard, a defense-only decisioning and representment workflow for one clearly defined dispute class. |
| 1:00–2:15 | Happy-path demo: ingest case → verify evidence → show deadline, completeness, P(win), EV, recommendation. |
| 2:15–3:00 | Show the source-cited packet and state that it is submission-ready, not an unapproved production auto-submit integration. |
| 3:00–3:45 | Failure: LLM/OCR treats `O` as `0`; deterministic validator and carrier confirmation block the bad evidence. |
| 3:45–4:30 | Evaluation: held-out data, metrics, false-contest cost, assumptions, and exceptions escalated to humans. |
| 4:30–5:00 | Architecture choices and close: “AI proposes; rules verify; economics decides.” |

## 14. “What broke, and how you got out” — draft answer

> In an early version, we let a multimodal model extract a tracking number, decide whether it matched the invoice, and report its own confidence in one step. On a deliberately noisy POD, it treated `AWB9823471O` as a match for `AWB98234710` and expressed high confidence. That failure was unsafe because a near-match can refer to a different shipment. We separated extraction from verification: the system now normalizes identifiers, requires exact matching, uses fuzzy/OCR correction only to propose a candidate, and requires an independent carrier-record confirmation before accepting it. We measure identifier-verification accuracy and false-contest rate on a held-out synthetic test set. The resulting system escalates uncertainty rather than inventing certainty.

Replace any generic results statement with actual measured results before submitting.

## 15. Application checklist

The official form asks for these items. Prepare them before the final evening.

- [ ] Full name
- [ ] College
- [ ] Graduation year
- [ ] Confirmation of in-person availability in Bangalore from September
- [ ] Choice of 6- or 12-month internship
- [ ] Resume PDF
- [ ] Track: `02 — AI Risk Manager`
- [ ] Project name: `DisputeGuard`
- [ ] Problem statement (50–100 words, derived from section 1)
- [ ] Public GitHub repository URL
- [ ] Unlisted five-minute pitch video URL
- [ ] “What broke, and how you got out” answer (section 14, updated with real metrics)

### Final GitHub repository quality gate

- [ ] README has one-command/local setup instructions and a short demo GIF/screenshots.
- [ ] `.env.example` contains no secrets.
- [ ] Synthetic data is labelled and safe to publish.
- [ ] Tests run successfully.
- [ ] Evaluation command and held-out split are documented.
- [ ] Architecture diagram and decision logic are explained.
- [ ] Limitations and assumptions are explicit.
- [ ] No claims of official scheme compliance, legal advice, production authorization, or real merchant results.
- [ ] No offensive fraud or customer-targeting capability.

## 16. Honest limitations to state prominently

1. This is a synthetic, prototype workflow and is not a legal or compliance product.
2. The demo policy is configurable but does not claim to encode every current scheme or jurisdictional rule.
3. “Win probability” is an evidence-based prototype estimate unless trained and calibrated against a suitable labelled dataset.
4. The product produces a submission-ready packet; it does not submit real disputes without authorized integration and human approval.
5. Human review is required for uncertainty, contradictions, high-value cases, and deadline-sensitive decisions.

## 17. Success definition

The submission is ready when a reviewer can clone the public repository, run a reliable demo, and see:

1. One concrete merchant-loss problem solved end to end.
2. AI used in bounded places where it adds value.
3. Deterministic verification stopping a realistic AI/OCR mistake.
4. A measurable held-out evaluation, including false-positive cost.
5. A clear, source-cited output and a safe human-review boundary.

That is the version of DisputeGuard worth submitting.

---

## Official Buildathon details used for this plan

- Application closes **5 September 2026**.
- Track 02 is **AI Risk Manager**: build a working detector, verifier, or auto-responder for one class of merchant loss; show measured precision and recall on held-out data and the false-positive cost; strictly defense-only.
- The application asks for a public GitHub repository, a five-minute pitch video, architecture/work explanation, and an account of what broke and how it was resolved.

Source: [Razorpay AI Buildathon](https://razorpay.com/buildathon/)
#   R a z o r p a y _ A I _ R i s k _ m a n a g e r  
 