/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: '#F6F3EB',
          surface: '#FDFBF7',
          border: '#E8E4DC',
        },
        stage: {
          DEFAULT: '#121110',
          surface: '#1A1816',
          border: '#2A2724',
          subtle: '#3A3632',
        },
        ink: {
          DEFAULT: '#1A1714',
          secondary: '#5C5752',
          muted: '#7A746A',
          border: '#D8D4CC',
        },
        signal: {
          red: '#C0392B',
          amber: '#B77F0A',
          green: '#1A7A40',
        },
        brass: {
          light: '#B08D4F',
          dark: '#7A5F2B',
        },
      },
      fontFamily: {
        display: ['Newsreader', 'serif'],
        sans: ['IBM Plex Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      borderRadius: {
        'sm': '1px',
        DEFAULT: '2px',
        'md': '2px',
        'lg': '3px',
      },
      transitionTimingFunction: {
        'precise': 'cubic-bezier(0.2, 0.0, 0.0, 1.0)',
        'exit': 'cubic-bezier(0.4, 0.0, 1.0, 1.0)',
      },
    },
  },
  plugins: [],
}
