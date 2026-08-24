/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        /* ── Razorpay-inspired palette ── */
        brand: {
          50:  "#eef5ff",
          100: "#d9e8ff",
          200: "#bcd7ff",
          300: "#8ebfff",
          400: "#599cff",
          500: "#3478ff",
          600: "#1b56f5",
          700: "#1542e1",
          800: "#1836b6",
          900: "#1a338f",
          950: "#142157",
        },
        navy: {
          50:  "#f0f4ff",
          100: "#dde5ff",
          200: "#c2cfff",
          300: "#96adff",
          400: "#647fff",
          500: "#3e4fff",
          600: "#2a2af5",
          700: "#2220d8",
          800: "#1e1dae",
          900: "#1e1f89",
          950: "#070825",
        },
        accent: {
          DEFAULT: "#00d09c",
          foreground: "#ffffff",
        },
        success: { DEFAULT: "#00d09c", foreground: "#fff" },
        warning: { DEFAULT: "#f5a623", foreground: "#fff" },
        danger:  { DEFAULT: "#ff4d4d", foreground: "#fff" },

        /* ── shadcn design tokens ── */
        border:      "hsl(var(--border))",
        input:       "hsl(var(--input))",
        ring:        "hsl(var(--ring))",
        background:  "hsl(var(--background))",
        foreground:  "hsl(var(--foreground))",
        primary:     { DEFAULT: "hsl(var(--primary))",   foreground: "hsl(var(--primary-foreground))" },
        secondary:   { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted:       { DEFAULT: "hsl(var(--muted))",     foreground: "hsl(var(--muted-foreground))" },
        popover:     { DEFAULT: "hsl(var(--popover))",   foreground: "hsl(var(--popover-foreground))" },
        card:        { DEFAULT: "hsl(var(--card))",      foreground: "hsl(var(--card-foreground))" },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(16px)" },
          to:   { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.5" },
        },
      },
      animation: {
        "fade-in":        "fade-in 0.4s ease-out forwards",
        "slide-in-right": "slide-in-right 0.3s ease-out forwards",
        shimmer:          "shimmer 2s infinite",
        pulse:            "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
