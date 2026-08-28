"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Shield, Filter, Loader2 } from "lucide-react";
import { fetchCases, type CaseSummary } from "@/lib/api";

const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }> = {
  pending_review:      { label: "Pending Review",      variant: "warning" },
  evidence_gathered:   { label: "Evidence Gathered",    variant: "default" },
  validation_complete: { label: "Validation Complete",  variant: "secondary" },
  representment_sent:  { label: "Representment Sent",   variant: "secondary" },
  won:                 { label: "Won",                  variant: "success" },
  lost:                { label: "Lost",                 variant: "destructive" },
  accepted_loss:       { label: "Accepted Loss",        variant: "destructive" },
};

const riskMap: Record<string, { label: string; color: string }> = {
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

function formatDate(dateStr: string): string {
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

export default function DisputesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchCases()
      .then((data) => {
        setCases(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filtered = filter ? cases.filter((c) => c.risk_level === filter) : cases;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 pl-64">
        <Header />
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Disputes</h1>
              <p className="text-muted-foreground mt-1">
                Manage and review all chargeback disputes.{" "}
                {!loading && <span className="text-primary font-medium">{cases.length} cases loaded.</span>}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex gap-1.5">
                {[null, "high", "medium", "low"].map((level) => (
                  <Button
                    key={level ?? "all"}
                    variant={filter === level ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFilter(level)}
                    className="text-xs"
                  >
                    {level ? level.charAt(0).toUpperCase() + level.slice(1) : "All"}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>All Disputes</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Loading disputes from API…
                </div>
              ) : filtered.length === 0 ? (
                <div className="text-center py-16 text-muted-foreground">
                  {filter ? `No ${filter}-risk disputes found.` : "No disputes loaded."}
                </div>
              ) : (
                <div className="relative overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border/50">
                        {["Case ID", "Merchant", "Amount", "Reason", "Risk", "Status", "Deadline", ""].map(
                          (h) => (
                            <th key={h} className="pb-3 text-left font-medium text-muted-foreground">
                              {h}
                            </th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((d, i) => {
                        const s = statusMap[d.status] ?? { label: d.status, variant: "secondary" as const };
                        const r = riskMap[d.risk_level] ?? { label: d.risk_level, color: "text-muted-foreground" };
                        return (
                          <tr
                            key={d.id}
                            className="border-b border-border/30 hover:bg-muted/50 transition-colors animate-slide-in-right"
                            style={{ animationDelay: `${i * 60}ms` }}
                          >
                            <td className="py-3">
                              <Link
                                href={`/disputes/${d.id}`}
                                className="font-mono text-xs font-medium text-primary hover:underline"
                              >
                                {d.id}
                              </Link>
                            </td>
                            <td className="py-3">{d.merchant_name}</td>
                            <td className="py-3 font-semibold">{formatAmount(d.amount)}</td>
                            <td className="py-3 text-muted-foreground">{d.reason.replace(/_/g, " ")}</td>
                            <td className="py-3">
                              <span className={`font-semibold text-xs ${r.color}`}>● {r.label}</span>
                            </td>
                            <td className="py-3">
                              <Badge variant={s.variant}>{s.label}</Badge>
                            </td>
                            <td className="py-3 text-muted-foreground text-xs">{formatDate(d.respond_by)}</td>
                            <td className="py-3">
                              <Link href={`/disputes/${d.id}`}>
                                <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                                  <Shield className="h-3 w-3" />
                                  Analyze
                                </Button>
                              </Link>
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
        </div>
      </main>
    </div>
  );
}
