import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#020617",
          800: "#0b1220",
          700: "#0f172a",
          600: "#1e293b",
        },
        pirate: {
          red: "#E63946",
          gold: "#eab308",
        },
      },
    },
  },
  plugins: [],
};
export default config;
