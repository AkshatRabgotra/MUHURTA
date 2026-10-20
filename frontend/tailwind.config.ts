import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        vedic: {
          dark: '#0D0805',
          darker: '#080503',
          card: '#150E0A',
          border: 'rgba(245, 158, 11, 0.3)',
          gold: '#F59E0B',
          amber: '#D97706',
          saffron: '#EA580C',
          vermilion: '#DC2626',
          cream: '#FFFBEB',
        },
      },
      fontFamily: {
        serif: ['var(--font-cinzel)', 'Georgia', 'serif'],
        sans: ['var(--font-sans)', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
