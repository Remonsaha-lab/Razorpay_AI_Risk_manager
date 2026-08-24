"use client";

import { useEffect, useState } from "react";
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
} from "lucide-react";

/* ── Metric card data ── */
const metrics = [
  {
    title: "Active Disputes",
    value: "23",
    change: "+3 today",
    changeType: "warning" as const,
    icon: FileWarning,
    iconColor: "text-warning",
    iconBg: "bg-warning/10",
  },
  {
    title: "Win Rate",
    value: "78.4%",
    change: "+2.1% this month",
    changeType: "success" as const,
    icon: TrendingUp,
    iconColor: "text-accent",
    iconBg: "bg-accent/10",
  },
  {
    title: "Amount at Risk",
    value: "₹4.2L",
    change: "12 cases pending",
    changeType: "destructive" as const,
    icon: IndianRupee,
    iconColor: "text-danger",
    iconBg: "bg-danger/10",
  },
  {
    title: "Avg Response Time",
    value: "2.4 hrs",
    change: "-18% vs last week",
    changeType: "success" as const,
    icon: Clock,
    iconColor: "text-brand-400",
    iconBg: "bg-brand-400/10",
  },
];

/* ── Recent disputes mock data ── */
const recentDisputes = [
  {
    id: "DSP-2026-001",
    merchant: "TechMart India",
    amount: "₹18,400",
    reason: "Merchandise not received",
    status: "pending_review",
    risk: "high",
    deadline: "Sep 4, 2026",
  },
  {
    id: "DSP-2026-002",
    merchant: "StyleHub",
    amount: "₹7,250",
    reason: "Not as described",
    status: "evidence_gathered",
    risk: "medium",
    deadline: "Sep 6, 2026",
  },
  {
    id: "DSP-2026-003",
    merchant: "FoodExpress",
    amount: "₹3,100",
    reason: "Duplicate charge",
    status: "representment_sent",
    risk: "low",
    deadline: "Sep 8, 2026",
  },
  {
    id: "DSP-2026-004",
    merchant: "BookWorld",
    amount: "₹12,800",
    reason: "Unauthorized transaction",
    status: "won",
    risk: "low",
    deadline: "Resolved",
  },
  {
    id: "DSP-2026-005",
    merchant: "GadgetZone",
    amount: "₹45,000",
    reason: "Service not provided",
    status: "pending_review",
    risk: "critical",
    deadline: "Sep 2, 2026",
  },
];

const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }> = {
  pending_review:      { label: "Pending Review",      variant: "warning" },
  evidence_gathered:   { label: "Evidence Gathered",    variant: "default" },
  representment_sent:  { label: "Representment Sent",   variant: "secondary" },
  won:                 { label: "Won",                  variant: "success" },
  lost:                { label: "Lost",                 variant: "destructive" },
};

const riskConfig: Record<string, { label: string; color: string }> = {
  low:      { label: "Low",      color: "text-accent" },
  medium:   { label: "Medium",   color: "text-warning" },
  high:     { label: "High",     color: "text-orange-500" },
  critical: { label: "Critical", color: "text-danger" },
};

export default function DashboardPage() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "healthy" | "error">("checking");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((r) => r.json())
      .then((d) => setBackendStatus(d.status === "healthy" ? "healthy" : "error"))
      .catch(() => setBackendStatus("error"));
  }, []);

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
              <Button variant="brand" className="gap-2">
                <Shield className="h-4 w-4" />
                New Analysis
              </Button>
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
                <Button variant="outline" size="sm" className="gap-1.5">
                  View All
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="relative overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Case ID
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Merchant
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Amount
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Reason
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Risk
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Status
                      </th>
                      <th className="pb-3 text-left font-medium text-muted-foreground">
                        Deadline
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentDisputes.map((dispute, i) => {
                      const status = statusConfig[dispute.status] ?? {
                        label: dispute.status,
                        variant: "secondary" as const,
                      };
                      const risk = riskConfig[dispute.risk] ?? {
                        label: dispute.risk,
                        color: "text-muted-foreground",
                      };
                      return (
                        <tr
                          key={dispute.id}
                          className="border-b border-border/30 transition-colors hover:bg-muted/50 animate-slide-in-right"
                          style={{ animationDelay: `${400 + i * 60}ms` }}
                        >
                          <td className="py-3 font-mono text-xs font-medium text-primary">
                            {dispute.id}
                          </td>
                          <td className="py-3">{dispute.merchant}</td>
                          <td className="py-3 font-semibold">{dispute.amount}</td>
                          <td className="py-3 text-muted-foreground">
                            {dispute.reason}
                          </td>
                          <td className="py-3">
                            <span className={`font-semibold text-xs ${risk.color}`}>
                              ● {risk.label}
                            </span>
                          </td>
                          <td className="py-3">
                            <Badge variant={status.variant}>{status.label}</Badge>
                          </td>
                          <td className="py-3 text-muted-foreground text-xs">
                            {dispute.deadline}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
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
                        High-value case needs immediate attention
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        DSP-2026-005 (₹45,000) — deadline in 9 days. AI
                        confidence for successful representment: 62%. Consider
                        gathering additional delivery proof.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-accent mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">
                        Strong evidence detected
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        DSP-2026-002 has matching delivery signatures and
                        tracking data. AI recommends auto-filing representment.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-danger/30 bg-danger/5 p-4">
                  <div className="flex items-start gap-3">
                    <XCircle className="h-5 w-5 text-danger mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">
                        Pattern alert: Repeat offender
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Customer linked to DSP-2026-001 has 3 prior disputes in
                        6 months. Flag for enhanced review.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="animate-fade-in" style={{ animationDelay: "580ms" }}>
              <CardHeader>
                <CardTitle>Resolution Summary</CardTitle>
                <CardDescription>Last 30 days performance.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Win/Loss/Pending bars */}
                  {[
                    { label: "Won",     count: 18, total: 30, color: "bg-accent" },
                    { label: "Lost",    count: 5,  total: 30, color: "bg-danger" },
                    { label: "Pending", count: 7,  total: 30, color: "bg-warning" },
                  ].map((item) => (
                    <div key={item.label} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{item.label}</span>
                        <span className="text-muted-foreground">
                          {item.count}/{item.total}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full ${item.color} transition-all duration-1000`}
                          style={{ width: `${(item.count / item.total) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}

                  <div className="pt-4 border-t border-border/50">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-accent">₹3.8L</p>
                        <p className="text-xs text-muted-foreground">Amount Recovered</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-danger">₹1.1L</p>
                        <p className="text-xs text-muted-foreground">Amount Lost</p>
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
