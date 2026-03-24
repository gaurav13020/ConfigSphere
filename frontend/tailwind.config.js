/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f7ff',
          100: '#eff2ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#312e81',
        },
        secondary: {
          500: '#8b5cf6',
          600: '#7c3aed',
        }
      },
      boxShadow: {
        'lg': '0 10px 40px rgba(0, 0, 0, 0.1)',
        'xl': '0 20px 60px rgba(0, 0, 0, 0.12)',
      }
    },
  },
  plugins: [],
}
