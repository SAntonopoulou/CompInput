/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'kotoba-primary': '#16561D',
        'kotoba-secondary': '#D6A42F',
        'kotoba-secondary-dark': '#B58C27',
        'kotoba-accent': '#F89973',
        'kotoba-background': '#F4F1E9',
        'kotoba-text': '#2B463C',
      },
    },
  },
  plugins: [],
}
