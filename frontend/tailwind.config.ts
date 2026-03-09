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
          50: "#f0f7ff",
          100: "#e0efff",
          200: "#b8dbff",
          300: "#7abfff",
          400: "#339dff",
          500: "#0a7eff",
          600: "#005fd4",
          700: "#004bab",
          800: "#00408d",
          900: "#003774",
          950: "#00224d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
