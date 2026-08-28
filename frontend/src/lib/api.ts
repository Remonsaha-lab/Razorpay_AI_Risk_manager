const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/* ── TypeScript Interfaces ── */

export interface CaseSummary {
  id: string;
  merchant_name: string;
  amount: string;
  currency: string;
  reason: string;
  status: string;
  respond_by: string;
  risk_level: string;
}

export interface EvidenceDocument {
  id: string;
  dispute_id: string;
  type: string;
  filename: string;
  source: string;
  extraction_method: string;
  extraction_confidence: number;
  raw_text: string;
}

export interface EvidenceClaim {
  id: string;
  dispute_id: string;
  document_id: string;
  field_name: string;
  raw_value: string;
  normalized_value: string;
  source_page: number;
  source_location: string;
  verification_status: "verified" | "failed" | "pending" | "needs_review";
  verification_reason: string;
  extraction_method: string;
  extraction_confidence: number;
}

export interface StrengthFactor {
  description: string;
  impact: number;
  source_claim_id: string | null;
}

export interface Decision {
  id: string;
  dispute_id: string;
  action: "contest" | "request_more_evidence" | "accept_loss";
  review_required: boolean;
  completeness_score: number;
  evidence_strength: number;
  contest_expected_value: string;
  accept_expected_value: string;
  positive_factors: StrengthFactor[];
  negative_factors: StrengthFactor[];
  reasons: string[];
  assumptions: string[];
  decided_at: string;
}

export interface ValidationIssue {
  rule_id: string;
  severity: string;
  message: string;
  document_id?: string;
  expected?: string;
  actual?: string;
}

export interface CaseDetail {
  case: CaseSummary & {
    merchant_id: string;
    transaction_id: string;
    order_id: string;
    transaction_date: string;
    reason_description: string;
    filed_date: string;
    customer_name: string;
    customer_email: string;
    shipping_address: string;
    billing_address: string;
    evidence_document_ids: string[];
  };
  evidence_documents: EvidenceDocument[];
  metadata: Record<string, unknown>;
}

export interface WorkflowResult {
  decision: Decision;
  claims: EvidenceClaim[];
  issues: ValidationIssue[];
  missing_evidence: string[];
  policy_id: string;
}

/* ── API Functions ── */

export async function fetchCases(): Promise<CaseSummary[]> {
  const data = await apiFetch<{ cases: CaseSummary[] }>("/cases");
  return data.cases;
}

export async function fetchCase(caseId: string): Promise<CaseDetail> {
  return apiFetch<CaseDetail>(`/cases/${caseId}`);
}

export async function runAnalysis(caseId: string): Promise<WorkflowResult> {
  return apiFetch<WorkflowResult>(`/cases/${caseId}/run`, { method: "POST" });
}

export async function fetchDecision(caseId: string): Promise<{
  decision: Decision;
  issues: ValidationIssue[];
  missing_evidence: string[];
}> {
  return apiFetch(`/cases/${caseId}/decision`);
}

export async function fetchEvidence(caseId: string): Promise<{
  claims: EvidenceClaim[];
  documents: EvidenceDocument[];
}> {
  return apiFetch(`/cases/${caseId}/evidence`);
}

export async function approveCase(caseId: string, narrative?: string): Promise<{ status: string; approval: Record<string, unknown> }> {
  return apiFetch(`/cases/${caseId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved_by: "Merchant Reviewer", narrative }),
  });
}

export async function fetchApproval(caseId: string): Promise<{ is_approved: boolean; approval: Record<string, unknown> | null }> {
  return apiFetch(`/cases/${caseId}/approval`);
}

export function getPacketDownloadUrl(caseId: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base}/cases/${caseId}/packet`;
}

