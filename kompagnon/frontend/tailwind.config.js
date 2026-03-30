/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        kc: {
          anthrazit:    '#1E1E1E',
          'anthrazit-80': '#3C3C3C',
          'anthrazit-20': '#D8D8D8',
          rot:          '#C8102E',
          'rot-hover':  '#A50D25',
          'rot-subtle': '#F9E5E8',
          weiss:        '#FFFFFF',
          hell:         '#F4F4F4',
          mittel:       '#8A8A8A',
          rand:         '#E0E0E0',
          success:      '#2E7D32',
          warning:      '#E65100',
          info:         '#0277BD',
        },
      },
      fontFamily: {
        display: ['Milo', 'Neue Haas Grotesk', 'DM Sans', 'system-ui', 'sans-serif'],
        body:    ['Milo', 'Source Sans 3', 'DM Sans', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        'kc-sm':  '2px',
        'kc-md':  '4px',
        'kc-lg':  '8px',
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
    },
  },
  plugins: [],
};
