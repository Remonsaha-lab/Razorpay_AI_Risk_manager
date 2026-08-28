"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Shield,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  FileText,
  TrendingUp,
  TrendingDown,
  Scale,
  Eye,
  Lock,
} from "lucide-react";
import {
  fetchCase,
  runAnalysis,
  approveCase,
  fetchApproval,
  getPacketDownloadUrl,
  type CaseDetail,
  type WorkflowResult,
  type EvidenceClaim,
} from "@/lib/api";

/* ── Helpers ── */

function formatAmount(amount: string): string {
  const num = parseFloat(amount);
  if (isNaN(num)) return `₹${amount}`;
  return `₹${num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

const actionConfig: Record<string, { label: string; color: string; bg: string; icon: typeof CheckCircle2 }> = {
  contest:                { label: "CONTEST",               color: "text-accent",  bg: "bg-accent/10 border-accent/30",        icon: CheckCircle2 },
  request_more_evidence:  { label: "REQUEST MORE EVIDENCE", color: "text-warning", bg: "bg-warning/10 border-warning/30",      icon: AlertTriangle },
  accept_loss:            { label: "ACCEPT LOSS",           color: "text-danger",  bg: "bg-danger/10 border-danger/30",        icon: XCircle },
};

const verificationColors: Record<string, string> = {
  verified:     "text-accent",
  failed:       "text-danger",
  pending:      "text-warning",
  needs_review: "text-orange-500",
};

const verificationIcons: Record<string, typeof CheckCircle2> = {
  verified:     CheckCircle2,
  failed:       XCircle,
  pending:      Clock,
  needs_review: AlertTriangle,
};

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [humanApproved, setHumanApproved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCase(caseId)
      .then((data) => {
        setCaseDetail(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    fetchApproval(caseId)
      .then((res) => {
        if (res.is_approved) {
          setHumanApproved(true);
        }
      })
      .catch(() => {});
  }, [caseId]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      const data = await runAnalysis(caseId);
      setResult(data);
      // Refresh approval state if needed
      const appRes = await fetchApproval(caseId).catch(() => ({ is_approved: false }));
      setHumanApproved(appRes.is_approved);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    }
    setAnalyzing(false);
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      await approveCase(caseId);
      setHumanApproved(true);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  };

  const handleDownloadPacket = () => {
    window.open(getPacketDownloadUrl(caseId), "_blank");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 pl-64">
          <Header />
          <div className="flex items-center justify-center h-[calc(100vh-4rem)] text-muted-foreground gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            Loading case {caseId}…
          </div>
        </main>
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 pl-64">
          <Header />
          <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4">
            <XCircle className="h-12 w-12 text-danger" />
            <p className="text-lg font-medium">Case not found</p>
            <p className="text-muted-foreground">{error || `Case ${caseId} does not exist.`}</p>
            <Link href="/disputes">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Disputes
              </Button>
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const dispute = caseDetail.case;
  const decision = result?.decision;
  const claims = result?.claims || [];
  const issues = result?.issues || [];
  const missingEvidence = result?.missing_evidence || [];
  const ac = decision ? (actionConfig[decision.action] ?? actionConfig.accept_loss) : null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 pl-64">
        <Header />
        <div className="p-6 space-y-6">

          {/* ── Breadcrumb & Actions ── */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/disputes">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
                  {caseId}
                  <Badge variant="warning">{dispute.status.replace(/_/g, " ")}</Badge>
                </h1>
                <p className="text-muted-foreground text-sm mt-0.5">
                  {dispute.merchant_name} — {dispute.reason.replace(/_/g, " ")}
                </p>
              </div>
            </div>
            <Button
              variant="brand"
              className="gap-2"
              onClick={handleRunAnalysis}
              disabled={analyzing}
            >
              {analyzing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Shield className="h-4 w-4" />
              )}
              {analyzing ? "Running Analysis…" : "Run AI Analysis"}
            </Button>
          </div>

          {/* ── Case Summary Cards ── */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground font-medium">Dispute Amount</p>
                <p className="text-2xl font-bold mt-1">{formatAmount(dispute.amount)}</p>
                <p className="text-xs text-muted-foreground mt-1">{dispute.currency}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground font-medium">Response Deadline</p>
                <p className="text-lg font-bold mt-1">{formatDate(dispute.respond_by)}</p>
                <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {Math.max(0, Math.ceil((new Date(dispute.respond_by).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))} days remaining
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground font-medium">Evidence Documents</p>
                <p className="text-2xl font-bold mt-1">{caseDetail.evidence_documents.length}</p>
                <p className="text-xs text-muted-foreground mt-1">attached to this case</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground font-medium">Risk Level</p>
                <p className={`text-lg font-bold mt-1 ${
                  dispute.risk_level === "high" || dispute.risk_level === "critical" ? "text-danger" :
                  dispute.risk_level === "medium" ? "text-warning" : "text-accent"
                }`}>
                  {dispute.risk_level.toUpperCase()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Filed {formatDate(dispute.filed_date || "")}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* ── Decision Banner ── */}
          {decision && ac && (
            <Card className={`border ${ac.bg} animate-fade-in`}>
              <CardContent className="pt-6 pb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`rounded-full p-3 ${ac.bg}`}>
                      <ac.icon className={`h-8 w-8 ${ac.color}`} />
                    </div>
                    <div>
                      <p className={`text-2xl font-bold ${ac.color}`}>{ac.label}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {decision.review_required && (
                          <span className="text-warning font-medium mr-2">⚠ Human review required</span>
                        )}
                        Evidence Strength: {(decision.evidence_strength * 100).toFixed(0)}%
                        {" · "}Completeness: {(decision.completeness_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Contest EV</p>
                    <p className={`text-lg font-bold ${parseFloat(decision.contest_expected_value) > 0 ? "text-accent" : "text-danger"}`}>
                      {formatAmount(decision.contest_expected_value)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Accept EV: {formatAmount(decision.accept_expected_value)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {decision && (
            <div className="grid gap-4 md:grid-cols-2">

              {/* ── Evidence Checklist ── */}
              <Card className="animate-fade-in">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Evidence Checklist
                  </CardTitle>
                  <CardDescription>
                    Completeness: {(decision.completeness_score * 100).toFixed(0)}%
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {["invoice", "tracking_record", "proof_of_delivery"].map((type) => {
                    const doc = caseDetail.evidence_documents.find((d) => d.type === type);
                    const isMissing = missingEvidence.some((m) => m.toLowerCase().includes(type.replace(/_/g, " ").toLowerCase()) || m.toLowerCase().includes(type.toLowerCase()));
                    return (
                      <div key={type} className="flex items-center gap-3 rounded-lg border border-border/50 p-3">
                        {doc && !isMissing ? (
                          <CheckCircle2 className="h-5 w-5 text-accent flex-shrink-0" />
                        ) : (
                          <XCircle className="h-5 w-5 text-danger flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <p className="text-sm font-medium capitalize">{type.replace(/_/g, " ")}</p>
                          {doc ? (
                            <p className="text-xs text-muted-foreground">{doc.filename} · {doc.source}</p>
                          ) : (
                            <p className="text-xs text-danger">Missing — not attached to this case</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {missingEvidence.length > 0 && (
                    <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 mt-2">
                      <p className="text-xs text-warning font-medium">Missing Evidence:</p>
                      {missingEvidence.map((m, i) => (
                        <p key={i} className="text-xs text-muted-foreground ml-2">• {m}</p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* ── Strength Factors ── */}
              <Card className="animate-fade-in" style={{ animationDelay: "100ms" }}>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Scale className="h-4 w-4" />
                    Evidence Strength Factors
                  </CardTitle>
                  <CardDescription>
                    Score: {(decision.evidence_strength * 100).toFixed(0)}% (explainable estimate, not calibrated)
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {decision.positive_factors.map((f, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border border-accent/20 bg-accent/5 p-3">
                      <TrendingUp className="h-4 w-4 text-accent mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm">{f.description}</p>
                        <p className="text-xs text-accent font-medium mt-0.5">+{(f.impact * 100).toFixed(0)}% impact</p>
                      </div>
                    </div>
                  ))}
                  {decision.negative_factors.map((f, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border border-danger/20 bg-danger/5 p-3">
                      <TrendingDown className="h-4 w-4 text-danger mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm">{f.description}</p>
                        <p className="text-xs text-danger font-medium mt-0.5">{(f.impact * 100).toFixed(0)}% impact</p>
                      </div>
                    </div>
                  ))}
                  {decision.positive_factors.length === 0 && decision.negative_factors.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">No factors recorded.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* ── Reasons & Assumptions ── */}
          {decision && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="animate-fade-in" style={{ animationDelay: "200ms" }}>
                <CardHeader>
                  <CardTitle className="text-base">Decision Reasoning</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {decision.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-primary mt-0.5">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                  {issues.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-border/50">
                      <p className="text-xs font-medium text-muted-foreground mb-2">Validation Issues:</p>
                      {issues.map((issue, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-muted-foreground mb-1">
                          <AlertTriangle className="h-3 w-3 text-warning mt-0.5 flex-shrink-0" />
                          <span>{issue.message}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="animate-fade-in" style={{ animationDelay: "300ms" }}>
                <CardHeader>
                  <CardTitle className="text-base">Assumptions</CardTitle>
                  <CardDescription>
                    Economic and model assumptions underlying this recommendation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {decision.assumptions.map((a, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="text-warning mt-0.5">⚙</span>
                      <span>{a}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}

          {/* ── Claims Table ── */}
          {claims.length > 0 && (
            <Card className="animate-fade-in" style={{ animationDelay: "400ms" }}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Extracted &amp; Verified Claims
                </CardTitle>
                <CardDescription>
                  {claims.length} claims extracted across {caseDetail.evidence_documents.length} documents.
                  Each claim shows what was extracted, how it was verified, and where it came from.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border/50">
                        {["Field", "Raw Value", "Normalized", "Status", "Reason", "Source"].map(
                          (h) => (
                            <th key={h} className="pb-3 text-left font-medium text-muted-foreground text-xs">{h}</th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {claims.map((claim, i) => {
                        const StatusIcon = verificationIcons[claim.verification_status] || Clock;
                        const statusColor = verificationColors[claim.verification_status] || "text-muted-foreground";
                        return (
                          <tr
                            key={claim.id}
                            className="border-b border-border/30 hover:bg-muted/50 transition-colors"
                          >
                            <td className="py-2.5">
                              <Badge variant="secondary" className="text-[10px] font-mono">
                                {claim.field_name}
                              </Badge>
                            </td>
                            <td className="py-2.5 font-mono text-xs max-w-[180px] truncate" title={claim.raw_value}>
                              {claim.raw_value}
                            </td>
                            <td className="py-2.5 font-mono text-xs max-w-[180px] truncate text-muted-foreground" title={claim.normalized_value}>
                              {claim.normalized_value}
                            </td>
                            <td className="py-2.5">
                              <span className={`flex items-center gap-1.5 text-xs font-medium ${statusColor}`}>
                                <StatusIcon className="h-3.5 w-3.5" />
                                {claim.verification_status}
                              </span>
                            </td>
                            <td className="py-2.5 text-xs text-muted-foreground max-w-[240px]">
                              {claim.verification_reason}
                            </td>
                            <td className="py-2.5 text-xs text-muted-foreground whitespace-nowrap">
                              <span className="font-mono">{claim.document_id}</span>
                              <br />
                              <span className="text-[10px]">{claim.source_location}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Human Approval & Packet ── */}
          {decision && (
            <Card className="animate-fade-in" style={{ animationDelay: "500ms" }}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Human Review & Packet Generation</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {decision.action === "contest"
                        ? humanApproved
                          ? "✅ Contest approved by reviewer. Packet generation enabled."
                          : "A human must approve this contest recommendation before generating an evidence packet."
                        : "Packet generation is only available for approved contest decisions."
                      }
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {decision.action === "contest" && !humanApproved && (
                      <Button
                        variant="default"
                        className="gap-2"
                        disabled={approving}
                        onClick={handleApprove}
                      >
                        {approving ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4" />
                        )}
                        {approving ? "Approving…" : "Approve Contest"}
                      </Button>
                    )}
                    <Button
                      variant="brand"
                      className="gap-2"
                      disabled={!(decision.action === "contest" && humanApproved)}
                      onClick={handleDownloadPacket}
                    >
                      {decision.action === "contest" && humanApproved ? (
                        <FileText className="h-4 w-4" />
                      ) : (
                        <Lock className="h-4 w-4" />
                      )}
                      Generate Evidence Packet (PDF)
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Pre-analysis state ── */}
          {!result && !analyzing && (
            <Card className="animate-fade-in">
              <CardContent className="py-16">
                <div className="text-center space-y-4">
                  <Shield className="h-16 w-16 text-muted-foreground/30 mx-auto" />
                  <div>
                    <p className="text-lg font-medium">Ready for Analysis</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Click &quot;Run AI Analysis&quot; to extract evidence claims, run deterministic validation,
                      and compute an economic recommendation for this dispute.
                    </p>
                  </div>
                  <Button variant="brand" className="gap-2" onClick={handleRunAnalysis}>
                    <Shield className="h-4 w-4" />
                    Run AI Analysis
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

        </div>
      </main>
    </div>
  );
}
