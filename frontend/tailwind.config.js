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
        aicte: {
          saffron: '#FF671F',
          white: '#FFFFFF',
          green: '#046A38',
          navy: '#06038D',
          slate: '#0F172A',
          dark: '#0B0F19',
          card: '#161F30',
          border: '#2A364F',
          accent: '#38BDF8'
        }
      }
    },
  },
  plugins: [],
}
