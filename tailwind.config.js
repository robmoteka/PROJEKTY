/** @type {import('tailwindcss').Config} */
// Konfiguracja Tailwind CSS — przygotowana na kompilację w v1.0
// Na MVP używamy CDN; ten plik będzie aktywowany po wdrożeniu standalone CLI
module.exports = {
  // Ścieżki skanowane przez Tailwind w celu eliminacji nieużywanych klas
  content: [
    "./shell/templates/**/*.html",
    "./module-issues/templates/**/*.html",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    // Dostępne motywy DaisyUI
    themes: ["dark", "light"],
  },
}
