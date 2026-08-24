"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Shield, Filter, Search } from "lucide-react";

const disputes = [
  {
    id: "DSP-2026-001",
    merchant: "TechMart India",
    amount: "₹18,400",
    reason: "Merchandise not received",
    status: "pending_review",
    risk: "high",
    created: "Aug 20, 2026",
    deadline: "Sep 4, 2026",
  },
  {
    id: "DSP-2026-002",
    merchant: "StyleHub",
    amount: "₹7,250",
    reason: "Not as described",
    status: "evidence_gathered",
    risk: "medium",
    created: "Aug 21, 2026",
    deadline: "Sep 6, 2026",
  },
  {
    id: "DSP-2026-003",
    merchant: "FoodExpress",
    amount: "₹3,100",
    reason: "Duplicate charge",
    status: "representment_sent",
    risk: "low",
    created: "Aug 18, 2026",
    deadline: "Sep 8, 2026",
  },
  {
    id: "DSP-2026-004",
    merchant: "BookWorld",
    amount: "₹12,800",
    reason: "Unauthorized transaction",
    status: "won",
    risk: "low",
    created: "Aug 10, 2026",
    deadline: "Resolved",
  },
  {
    id: "DSP-2026-005",
    merchant: "GadgetZone",
    amount: "₹45,000",
    reason: "Service not provided",
    status: "pending_review",
    risk: "critical",
    created: "Aug 22, 2026",
    deadline: "Sep 2, 2026",
  },
];

const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" }> = {
  pending_review:      { label: "Pending Review",      variant: "warning" },
  evidence_gathered:   { label: "Evidence Gathered",    variant: "default" },
  representment_sent:  { label: "Representment Sent",   variant: "secondary" },
  won:                 { label: "Won",                  variant: "success" },
  lost:                { label: "Lost",                 variant: "destructive" },
};

const riskMap: Record<string, { label: string; color: string }> = {
  low:      { label: "Low",      color: "text-accent" },
  medium:   { label: "Medium",   color: "text-warning" },
  high:     { label: "High",     color: "text-orange-500" },
  critical: { label: "Critical", color: "text-danger" },
};

export default function DisputesPage() {
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
                Manage and review all chargeback disputes.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Filter className="h-3.5 w-3.5" />
                Filter
              </Button>
              <Button variant="brand" className="gap-2">
                <Shield className="h-4 w-4" />
                Run AI Analysis
              </Button>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>All Disputes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border/50">
                      {["Case ID", "Merchant", "Amount", "Reason", "Risk", "Status", "Created", "Deadline"].map(
                        (h) => (
                          <th key={h} className="pb-3 text-left font-medium text-muted-foreground">
                            {h}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {disputes.map((d, i) => {
                      const s = statusMap[d.status] ?? { label: d.status, variant: "secondary" as const };
                      const r = riskMap[d.risk] ?? { label: d.risk, color: "text-muted-foreground" };
                      return (
                        <tr
                          key={d.id}
                          className="border-b border-border/30 hover:bg-muted/50 transition-colors animate-slide-in-right"
                          style={{ animationDelay: `${i * 60}ms` }}
                        >
                          <td className="py-3 font-mono text-xs font-medium text-primary">{d.id}</td>
                          <td className="py-3">{d.merchant}</td>
                          <td className="py-3 font-semibold">{d.amount}</td>
                          <td className="py-3 text-muted-foreground">{d.reason}</td>
                          <td className="py-3">
                            <span className={`font-semibold text-xs ${r.color}`}>● {r.label}</span>
                          </td>
                          <td className="py-3">
                            <Badge variant={s.variant}>{s.label}</Badge>
                          </td>
                          <td className="py-3 text-muted-foreground text-xs">{d.created}</td>
                          <td className="py-3 text-muted-foreground text-xs">{d.deadline}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
