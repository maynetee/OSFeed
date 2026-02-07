/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        'background-subtle': 'hsl(var(--background-subtle))',
        'background-muted': 'hsl(var(--background-muted))',
        foreground: 'hsl(var(--foreground))',
        'foreground-muted': 'hsl(var(--foreground-muted))',
        card: 'hsl(var(--card))',
        'card-foreground': 'hsl(var(--card-foreground))',
        muted: 'hsl(var(--muted))',
        border: 'hsl(var(--border))',
        primary: 'hsl(var(--primary))',
        'primary-foreground': 'hsl(var(--primary-foreground))',
        success: 'hsl(var(--success))',
        warning: 'hsl(var(--warning))',
        danger: 'hsl(var(--danger))',
        info: 'hsl(var(--info))',
        duplicate: 'hsl(var(--duplicate))',
        translated: 'hsl(var(--translated))',
        accent: 'hsl(var(--accent))',
        'accent-foreground': 'hsl(var(--accent-foreground))',
        'sidebar-bg': 'hsl(var(--sidebar-bg))',
        'sidebar-border': 'hsl(var(--sidebar-border))',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      animation: {
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
      boxShadow: {
        glow: '0 0 30px rgba(59, 130, 246, 0.25)',
      },
    },
  },
  plugins: [],
}
