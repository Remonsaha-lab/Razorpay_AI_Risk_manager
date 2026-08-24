"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BookOpen, MessageCircle, FileText, ExternalLink } from "lucide-react";

export default function HelpPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 pl-64">
        <Header />
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Help & Docs</h1>
            <p className="text-muted-foreground mt-1">
              Documentation, guides, and support resources.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              { icon: BookOpen,       title: "Documentation",   desc: "Full API and workflow documentation.", link: "#" },
              { icon: FileText,       title: "Implementation Guide", desc: "Step-by-step setup and integration.", link: "#" },
              { icon: MessageCircle,  title: "Support",         desc: "Contact the DisputeGuard team.",       link: "#" },
            ].map(({ icon: Icon, title, desc }, i) => (
              <Card
                key={title}
                className="animate-fade-in cursor-pointer hover:border-primary/50 transition-colors"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <CardHeader className="text-center space-y-3">
                  <div className="mx-auto rounded-xl bg-primary/10 p-4 w-fit">
                    <Icon className="h-8 w-8 text-primary" />
                  </div>
                  <CardTitle className="text-base">{title}</CardTitle>
                  <CardDescription>{desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
