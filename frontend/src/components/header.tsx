"use client";

import { Bell, Search, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function Header() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border/50 bg-background/80 backdrop-blur-xl px-6">
      {/* ── Search ── */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search disputes, transactions…"
          className="h-10 w-full rounded-lg border border-border/50 bg-muted/50 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
        />
      </div>

      {/* ── Actions ── */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={toggleTheme} className="relative">
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger animate-pulse" />
        </Button>

        <div className="ml-2 flex h-9 w-9 items-center justify-center rounded-full gradient-brand text-xs font-bold text-white shadow-lg shadow-brand-500/20">
          RM
        </div>
      </div>
    </header>
  );
}
