/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1', // Indigo primary
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        ai: {
          primary: '#8b5cf6',   // Violet
          secondary: '#6366f1', // Indigo
          glow: '#a855f7',
        },
        eligible: {
          light: '#d1fae5',
          text: '#10b981',
          bg: '#064e3b',
          border: '#059669',
        },
        warning: {
          light: '#fef3c7',
          text: '#f59e0b',
          bg: '#78350f',
          border: '#d97706',
        },
        ineligible: {
          light: '#fee2e2',
          text: '#ef4444',
          bg: '#7f1d1d',
          border: '#dc2626',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
