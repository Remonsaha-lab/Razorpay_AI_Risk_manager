"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings as SettingsIcon, Key, Bell, Shield, Globe } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 pl-64">
        <Header />
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
            <p className="text-muted-foreground mt-1">
              Configure DisputeGuard preferences and integrations.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {[
              { icon: Key,    title: "API Keys",          desc: "Manage Razorpay and Gemini API credentials." },
              { icon: Bell,   title: "Notifications",     desc: "Configure alert thresholds and channels." },
              { icon: Shield, title: "Risk Policies",     desc: "Customise AI risk scoring rules." },
              { icon: Globe,  title: "Webhook Endpoints", desc: "Set up real-time event webhooks." },
            ].map(({ icon: Icon, title, desc }, i) => (
              <Card
                key={title}
                className="animate-fade-in"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                  <div className="rounded-lg bg-primary/10 p-2.5">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-base">{title}</CardTitle>
                    <CardDescription className="text-xs">{desc}</CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    Configure
                  </Button>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
