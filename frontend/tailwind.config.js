/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#16561D',
        secondary: '#D6A42F',
        accent: '#F89973',
        background: '#F4F1E9',
        'text-color': '#2B463C',
      },
    },
  },
  plugins: [],
}
