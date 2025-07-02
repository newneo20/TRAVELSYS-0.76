module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './**/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
      colors: {
        primary: '#1e40af', // Ejemplo azul
      },
    },
  },
  plugins: [],
};
