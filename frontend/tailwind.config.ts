import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        atlas: {
          bg: "#0C0C0E",
          surface: "#131316",
          "surface-2": "#1A1A1F",
          "surface-3": "#222228",
          border: "#2A2A32",
          "border-light": "#35353F",
          muted: "#6B6B7B",
          text: "#E8E8ED",
          "text-secondary": "#9D9DAD",
        },
        amber: {
          50: "#FFFBEB",
          100: "#FEF3C7",
          200: "#FDE68A",
          300: "#FCD34D",
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
          700: "#B45309",
          800: "#92400E",
          900: "#78350F",
          950: "#451A03",
        },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
