/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        lab: {
          bg: "#0b0f14",
          panel: "#121820",
          border: "#1e2a38",
          accent: "#3dd6c3",
          muted: "#8b9cb3",
          warn: "#f0a020",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
