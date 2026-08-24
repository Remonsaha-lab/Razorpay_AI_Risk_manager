"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  FileWarning,
  BarChart3,
  Settings,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/",           label: "Dashboard",     icon: LayoutDashboard },
  { href: "/disputes",   label: "Disputes",      icon: FileWarning },
  { href: "/analytics",  label: "Analytics",     icon: BarChart3 },
  { href: "/settings",   label: "Settings",      icon: Settings },
  { href: "/help",       label: "Help & Docs",   icon: HelpCircle },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border/50 bg-card/80 backdrop-blur-xl">
      {/* ── Logo ── */}
      <div className="flex h-16 items-center gap-2.5 border-b border-border/50 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-brand shadow-lg shadow-brand-500/20">
          <Shield className="h-5 w-5 text-white" />
        </div>
        <div>
          <span className="text-lg font-bold tracking-tight">
            Dispute<span className="text-gradient">Guard</span>
          </span>
          <p className="text-[10px] leading-none text-muted-foreground">
            AI Risk Manager
          </p>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon
                className={cn(
                  "h-4.5 w-4.5 transition-colors",
                  active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              {label}
              {active && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Footer ── */}
      <div className="border-t border-border/50 p-4">
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-xs font-medium text-muted-foreground">
            DisputeGuard v0.1.0
          </p>
          <p className="text-[10px] text-muted-foreground/60">
            © 2026 Razorpay
          </p>
        </div>
      </div>
    </aside>
  );
}
