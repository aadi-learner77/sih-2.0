/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Arial', 'Helvetica', 'sans-serif'],
        mono: ['ui-monospace', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius-md)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-lg)',
        '2xl': 'var(--radius-lg)',
        '3xl': 'var(--radius-lg)',
        pill: 'var(--radius-pill)',
        full: 'var(--radius-pill)',
      },
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-muted': 'var(--surface-muted)',
        border: 'var(--border)',
        text: 'var(--text)',
        'text-muted': 'var(--text-muted)',
        primary: {
          DEFAULT: 'var(--primary)',
          hover: 'var(--primary-hover)',
        },
        focus: 'var(--focus)',
        success: {
          bg: 'var(--success-bg)',
          text: 'var(--success-text)',
        },
        warning: {
          bg: 'var(--warning-bg)',
          text: 'var(--warning-text)',
        },
        danger: {
          bg: 'var(--danger-bg)',
          text: 'var(--danger-text)',
        },
        info: {
          bg: 'var(--info-bg)',
          text: 'var(--info-text)',
        },
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
