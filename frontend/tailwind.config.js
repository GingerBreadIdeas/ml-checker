/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'roboto-medium': ['Roboto', 'sans-serif'],
        'roboto-light': ['Roboto', 'sans-serif'],
        'poppins-regular': ['Poppins', 'sans-serif'],
      },
      fontWeight: {
        'roboto-medium': '500',
        'roboto-light': '300',
        'poppins-regular': '400',
      }
    },
  },
  plugins: [],
}