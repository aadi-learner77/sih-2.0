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
        sans: ['Inter', '"Noto Sans Devanagari"', 'system-ui', 'sans-serif'],
        serif: ['Fraunces', 'Playfair Display', 'Georgia', 'serif'],
        devanagari: ['"Noto Sans Devanagari"', '"Noto Serif Devanagari"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius-md)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-lg)',
        '2xl': 'var(--radius-lg)',
        '3xl': '24px',
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
        navy: '#0A1F3D',
        brandBlue: '#14396B',
        midnight: {
          DEFAULT: '#02030A',
          2: '#060914',
          3: '#0B1020',
        },
        'midnight-2': '#060914',
        'midnight-3': '#0B1020',
        cobalt: {
          DEFAULT: '#1F4BFF',
          light: '#4D74FF',
          dark: '#0A2FD6',
          glow: 'rgba(31,75,255,0.45)',
        },
        soft: '#C7D2FE',
        muted: '#8A97C2',
        'text-soft': '#C7D2FE',
        'text-white': '#FFFFFF',
        saffron: '#FF9933',
        brandGreen: '#138808',
        cyan: {
          DEFAULT: '#22D3EE',
          400: '#22D3EE',
          500: '#06B6D4',
        },
        violet: {
          DEFAULT: '#8B5CF6',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
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
        },
        pramaan: {
          midnight: '#0B1437',
          deepNavy: '#0A1F3D',
          royalBlue: '#14396B',
          electricCyan: '#22D3EE',
          saffron: '#FF9933',
          saffronLight: '#FEF3C7',
          indiaGreen: '#138808',
          indiaGreenLight: '#DCFCE7',
          violet: '#8B5CF6',
          ivory: '#FAFAF7',
          slateText: '#0F172A',
          mutedText: '#475569'
        }
      }
    },
  },
  plugins: [],
}
