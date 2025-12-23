/** @type {import('tailwindcss').Config} */
export default {
  // где используем классы
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6', // Основной синий
          600: '#2563eb', // Ховер
          700: '#1d4ed8',
        },
        dark: {
          bg: '#0f172a',      // Slate 900 (Фон страницы)
          surface: '#1e293b', // Slate 800 (Фон карточек/сайдбара)
          border: '#334155',  // Slate 700
        }
      }
    },
  },
  plugins: [],
}