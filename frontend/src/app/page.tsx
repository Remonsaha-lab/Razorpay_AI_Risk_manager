"use client";

import { useEffect, useState } from "react";
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
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  IndianRupee,
  FileWarning,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { fetchCases, type CaseSummary } from "@/lib/api";

const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }> = {
  pending_review:      { label: "Pending Review",      variant: "warning" },
  evidence_gathered:   { label: "Evidence Gathered",    variant: "default" },
  validation_complete: { label: "Validation Complete",  variant: "secondary" },
  representment_sent:  { label: "Representment Sent",   variant: "secondary" },
  won:                 { label: "Won",                  variant: "success" },
  lost:                { label: "Lost",                 variant: "destructive" },
  accepted_loss:       { label: "Accepted Loss",        variant: "destructive" },
};

const riskConfig: Record<string, { label: string; color: string }> = {
  low:      { label: "Low",      color: "text-accent" },
  medium:   { label: "Medium",   color: "text-warning" },
  high:     { label: "High",     color: "text-orange-500" },
  critical: { label: "Critical", color: "text-danger" },
};

function formatAmount(amount: string): string {
  const num = parseFloat(amount);
  if (isNaN(num)) return `₹${amount}`;
  return `₹${num.toLocaleString("en-IN")}`;
}

function formatDeadline(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function DashboardPage() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "healthy" | "error">("checking");
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((r) => r.json())
      .then((d) => setBackendStatus(d.status === "healthy" ? "healthy" : "error"))
      .catch(() => setBackendStatus("error"));

    fetchCases()
      .then((data) => {
        setCases(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  /* ── Compute live metrics ── */
  const totalCases = cases.length;
  const totalAmountAtRisk = cases.reduce((sum, c) => sum + parseFloat(c.amount || "0"), 0);
  const pendingCount = cases.filter((c) => c.status === "pending_review").length;

  const metrics = [
    {
      title: "Active Disputes",
      value: loading ? "…" : String(totalCases),
      change: `${pendingCount} pending review`,
      changeType: "warning" as const,
      icon: FileWarning,
      iconColor: "text-warning",
      iconBg: "bg-warning/10",
    },
    {
      title: "Win Rate",
      value: "—",
      change: "Run analysis to compute",
      changeType: "success" as const,
      icon: TrendingUp,
      iconColor: "text-accent",
      iconBg: "bg-accent/10",
    },
    {
      title: "Amount at Risk",
      value: loading ? "…" : `₹${(totalAmountAtRisk / 100000).toFixed(1)}L`,
      change: `${totalCases} cases loaded`,
      changeType: "destructive" as const,
      icon: IndianRupee,
      iconColor: "text-danger",
      iconBg: "bg-danger/10",
    },
    {
      title: "Avg Response Time",
      value: "—",
      change: "Requires evaluation data",
      changeType: "success" as const,
      icon: Clock,
      iconColor: "text-brand-400",
      iconBg: "bg-brand-400/10",
    },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <main className="flex-1 pl-64">
        <Header />

        <div className="p-6 space-y-6">
          {/* ── Page title ── */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                Dashboard
              </h1>
              <p className="text-muted-foreground mt-1">
                Real-time chargeback monitoring and AI-powered risk analysis.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-card px-3 py-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    backendStatus === "healthy"
                      ? "bg-accent animate-pulse"
                      : backendStatus === "error"
                      ? "bg-danger"
                      : "bg-warning animate-pulse"
                  }`}
                />
                <span className="text-xs font-medium text-muted-foreground">
                  API:{" "}
                  {backendStatus === "healthy"
                    ? "Connected"
                    : backendStatus === "error"
                    ? "Offline"
                    : "Checking…"}
                </span>
              </div>
              <Link href="/disputes">
                <Button variant="brand" className="gap-2">
                  <Shield className="h-4 w-4" />
                  View Disputes
                </Button>
              </Link>
            </div>
          </div>

          {/* ── Metric cards ── */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric, i) => (
              <Card
                key={metric.title}
                className="animate-fade-in"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.title}
                  </CardTitle>
                  <div className={`rounded-lg p-2 ${metric.iconBg}`}>
                    <metric.icon className={`h-4 w-4 ${metric.iconColor}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metric.value}</div>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                    {metric.changeType === "success" && (
                      <ArrowUpRight className="h-3 w-3 text-accent" />
                    )}
                    {metric.changeType === "warning" && (
                      <AlertTriangle className="h-3 w-3 text-warning" />
                    )}
                    {metric.change}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* ── Recent disputes table ── */}
          <Card className="animate-fade-in" style={{ animationDelay: "320ms" }}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Disputes</CardTitle>
                  <CardDescription>
                    Latest chargeback cases requiring attention.
                  </CardDescription>
                </div>
                <Link href="/disputes">
                  <Button variant="outline" size="sm" className="gap-1.5">
                    View All
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Loading cases from API…
                </div>
              ) : cases.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No cases loaded. Check that the backend is running.
                </div>
              ) : (
                <div className="relative overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border/50">
                        <th className="pb-3 text-left font-medium text-muted-foreground">Case ID</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Merchant</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Amount</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Reason</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Risk</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Status</th>
                        <th className="pb-3 text-left font-medium text-muted-foreground">Deadline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cases.slice(0, 8).map((dispute, i) => {
                        const status = statusConfig[dispute.status] ?? {
                          label: dispute.status,
                          variant: "secondary" as const,
                        };
                        const risk = riskConfig[dispute.risk_level] ?? {
                          label: dispute.risk_level,
                          color: "text-muted-foreground",
                        };
                        return (
                          <tr
                            key={dispute.id}
                            className="border-b border-border/30 transition-colors hover:bg-muted/50 animate-slide-in-right cursor-pointer"
                            style={{ animationDelay: `${400 + i * 60}ms` }}
                          >
                            <td className="py-3">
                              <Link
                                href={`/disputes/${dispute.id}`}
                                className="font-mono text-xs font-medium text-primary hover:underline"
                              >
                                {dispute.id}
                              </Link>
                            </td>
                            <td className="py-3">{dispute.merchant_name}</td>
                            <td className="py-3 font-semibold">{formatAmount(dispute.amount)}</td>
                            <td className="py-3 text-muted-foreground">{dispute.reason.replace(/_/g, " ")}</td>
                            <td className="py-3">
                              <span className={`font-semibold text-xs ${risk.color}`}>
                                ● {risk.label}
                              </span>
                            </td>
                            <td className="py-3">
                              <Badge variant={status.variant}>{status.label}</Badge>
                            </td>
                            <td className="py-3 text-muted-foreground text-xs">
                              {formatDeadline(dispute.respond_by)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── AI Insights panel ── */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="animate-fade-in" style={{ animationDelay: "500ms" }}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  AI Risk Insights
                </CardTitle>
                <CardDescription>
                  Automated analysis from DisputeGuard AI engine.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">
                        Select a case to run analysis
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Navigate to any dispute and click &quot;Run AI Analysis&quot;
                        to see the deterministic evidence assessment, completeness
                        score, and economic recommendation.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-accent mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">
                        {cases.length} cases loaded from fixtures
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        All synthetic test data is ready for extraction and validation.
                        Includes strong, weak, corrupted-OCR, and mismatch scenarios.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-danger/30 bg-danger/5 p-4">
                  <div className="flex items-start gap-3">
                    <XCircle className="h-5 w-5 text-danger mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">
                        Safety: Review required for all contest decisions
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        AI extraction and scoring are advisory only. A human must
                        approve every contest before packet generation is enabled.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="animate-fade-in" style={{ animationDelay: "580ms" }}>
              <CardHeader>
                <CardTitle>Case Types Overview</CardTitle>
                <CardDescription>Distribution of loaded synthetic scenarios.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {[
                    { label: "Strong Evidence", count: cases.filter(c => c.risk_level === "low" || c.risk_level === "medium").length, total: totalCases || 1, color: "bg-accent" },
                    { label: "Missing Evidence", count: cases.filter(c => c.status === "pending_review" && c.risk_level === "medium").length, total: totalCases || 1, color: "bg-warning" },
                    { label: "High Risk / Critical", count: cases.filter(c => c.risk_level === "high" || c.risk_level === "critical").length, total: totalCases || 1, color: "bg-danger" },
                  ].map((item) => (
                    <div key={item.label} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{item.label}</span>
                        <span className="text-muted-foreground">
                          {item.count}/{totalCases}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full ${item.color} transition-all duration-1000`}
                          style={{ width: `${(item.count / (totalCases || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}

                  <div className="pt-4 border-t border-border/50">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-accent">
                          {formatAmount(String(totalAmountAtRisk))}
                        </p>
                        <p className="text-xs text-muted-foreground">Total Amount at Risk</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-brand-400">{totalCases}</p>
                        <p className="text-xs text-muted-foreground">Total Cases Loaded</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
