/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Updated Color Palette
        primary: {
          50: '#fef7ed',
          100: '#fdedd3',
          200: '#fbd8a5',
          300: '#f9bc6d',
          400: '#f69d33',
          500: '#e69543', // Main Orange
          600: '#d17a1f',
          700: '#ae5d17',
          800: '#8c4a18',
          900: '#743e17',
        },
        charcoal: {
          50: '#f6f6f6',
          100: '#e7e7e7',
          200: '#d1d1d1',
          300: '#b0b0b0',
          400: '#888888',
          500: '#6d6d6d',
          600: '#5d5d5d',
          700: '#4f4f4f',
          800: '#454545',
          900: '#232323', // Main Charcoal
        },
        light: {
          50: '#ffffff', // Pure White
          100: '#fdfdfd',
          200: '#f8f8f8',
          300: '#f0f0f0',
          400: '#e8e8e8',
          500: '#d3d2d0', // Main Light Gray
          600: '#b8b7b5',
          700: '#9d9c9a',
          800: '#82817f',
          900: '#676664',
        },
        accent: {
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#747474', // Main Accent Gray
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.4s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
      },
      boxShadow: {
        'soft': '0 4px 20px rgba(35, 35, 35, 0.08)',
        'medium': '0 8px 30px rgba(35, 35, 35, 0.12)',
        'strong': '0 16px 50px rgba(35, 35, 35, 0.15)',
        'orange-glow': '0 4px 20px rgba(230, 149, 67, 0.3)',
        'orange-glow-strong': '0 8px 30px rgba(230, 149, 67, 0.4)',
      },
    },
  },
  plugins: [],
}