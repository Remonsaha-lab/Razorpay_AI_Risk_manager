"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BarChart3, TrendingUp, TrendingDown, PieChart } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 pl-64">
        <Header />
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
            <p className="text-muted-foreground mt-1">
              Chargeback trends, win-rate analytics, and risk forecasting.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card className="animate-fade-in">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Monthly Dispute Volume
                </CardTitle>
                <BarChart3 className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">142</div>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                  <TrendingDown className="h-3 w-3 text-accent" />
                  -8% vs last month
                </p>
              </CardContent>
            </Card>

            <Card className="animate-fade-in" style={{ animationDelay: "80ms" }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Average Dispute Value
                </CardTitle>
                <PieChart className="h-4 w-4 text-warning" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₹14,200</div>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-warning" />
                  +5% vs last month
                </p>
              </CardContent>
            </Card>

            <Card className="animate-fade-in" style={{ animationDelay: "160ms" }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Recovered
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-accent" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₹18.6L</div>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-accent" />
                  +12% vs last month
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="animate-fade-in" style={{ animationDelay: "240ms" }}>
            <CardHeader>
              <CardTitle>Dispute Volume Trend</CardTitle>
              <CardDescription>
                Monthly dispute counts over the last 6 months.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-3 h-48">
                {[
                  { month: "Mar", value: 165 },
                  { month: "Apr", value: 180 },
                  { month: "May", value: 155 },
                  { month: "Jun", value: 170 },
                  { month: "Jul", value: 154 },
                  { month: "Aug", value: 142 },
                ].map((bar) => (
                  <div key={bar.month} className="flex-1 flex flex-col items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      {bar.value}
                    </span>
                    <div
                      className="w-full rounded-t-md bg-gradient-to-t from-brand-600 to-brand-400 transition-all duration-700"
                      style={{ height: `${(bar.value / 200) * 100}%` }}
                    />
                    <span className="text-xs text-muted-foreground">{bar.month}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
