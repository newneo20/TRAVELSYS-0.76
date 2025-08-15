// tailwind.config.js
module.exports = {
  // 🔥 Activa el modo oscuro por clase (lo controlamos con <html class="dark">)
  darkMode: 'class',

  // Qué archivos escanea Tailwind para generar utilidades
  content: [
    './templates/**/*.html',           // templates raíz
    './**/templates/**/*.html',        // templates en apps Django
    './**/*.js',                       // scripts front
    './**/*.ts',                       // (opcional) si usas TS
    './**/*.py',                       // (opcional) clases en strings desde Python
  ],

  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
      colors: {
        primary: '#1e40af', // tu azul
      },
      // (opcional) sombras/superficies dark suaves
      boxShadow: {
        'elev-1': '0 1px 2px rgba(0,0,0,.06)',
      },
    },
  },

  plugins: [
    // Si más adelante usas forms: require('@tailwindcss/forms')
  ],

  // (opcional) si tienes clases generadas dinámicamente, agrégalas aquí
  // safelist: ['dark:bg-gray-900','dark:text-gray-100', 'bg-white', 'text-gray-900'],
};
