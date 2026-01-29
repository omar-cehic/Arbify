/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          'yellow': {
            400: '#d4af37', // Gold color from logo
            500: '#c4a030', // Darker variant for hover states
          },
          'gray': {
            700: '#1f1f1f',
            800: '#141414',
            900: '#0c0c0c',
          }
        },
        fontFamily: {
          sans: ['Inter', 'system-ui', 'sans-serif'],
        },
      },
    },
    plugins: [],
    safelist: [
      'bg-gray-900',
      'bg-gray-800',
      'text-white',
      'text-yellow-400',
      'py-3',
      'px-4',
    ],
  }