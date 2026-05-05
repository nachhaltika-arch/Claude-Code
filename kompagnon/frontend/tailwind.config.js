/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        kompagnon: {
          50:  "#f0fafa",
          100: "#d0f0f5",
          200: "#a0e0ea",
          300: "#60c8d8",
          400: "#20aabf",
          500: "#008EAA",
          600: "#007090",
          700: "#005570",
          800: "#003d52",
          900: "#002535",
        },
        accent: {
          200: "#fde8d0",
          400: "#f8b060",
          600: "#e07020",
        },
        /* Legacy kc- aliases for backwards compatibility */
        kc: {
          anthrazit:      '#002535',
          'anthrazit-80': '#003d52',
          'anthrazit-20': '#a0e0ea',
          rot:            '#008EAA',
          'rot-hover':    '#007090',
          'rot-subtle':   '#f0fafa',
          weiss:          '#FFFFFF',
          hell:           '#f8fafc',
          mittel:         '#8A8A8A',
          rand:           '#e2e8f0',
          success:        '#16a34a',
          warning:        '#ea580c',
          info:           '#0284c7',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        'kc-sm':  '2px',
        'kc-md':  '6px',
        'kc-lg':  '12px',
      },
      spacing: {
        'kc-1':  '0.25rem',
        'kc-2':  '0.5rem',
        'kc-3':  '0.75rem',
        'kc-4':  '1rem',
        'kc-6':  '1.5rem',
        'kc-8':  '2rem',
        'kc-12': '3rem',
        'kc-16': '4rem',
        'kc-20': '5rem',
      },
      animation: {
        'blob': 'blob 7s infinite',
        'bounce-slow': 'bounce 3s infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        blob: {
          '0%':   { transform: 'translate(0,0) scale(1)' },
          '33%':  { transform: 'translate(30px,-50px) scale(1.1)' },
          '66%':  { transform: 'translate(-20px,20px) scale(0.9)' },
          '100%': { transform: 'translate(0,0) scale(1)' },
        },
        fadeIn: {
          '0%':   { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'kompagnon': '0 4px 24px rgba(0,142,170,0.2)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
