/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eef4ff', 100: '#d9e6ff', 500: '#3b6cf6', 600: '#2853db', 700: '#2143b0' },
      },
    },
  },
  plugins: [],
};
