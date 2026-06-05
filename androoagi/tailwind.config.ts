import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./renderer/**/*.{ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0f',
        surface: '#111118',
        'surface-2': '#1a1a24',
        border: 'rgba(255,255,255,0.07)',
        agents: {
          orchestrator: '#7c3aed',
          scout:        '#0ea5e9',
          validation:   '#f59e0b',
          store:        '#10b981',
          listing:      '#f97316',
          product:      '#ec4899',
          growth:       '#06b6d4',
        },
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'typing': 'typing 0.05s steps(1)',
        'fade-up': 'fadeUp 0.4s ease-out',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        slideIn:   { from: { opacity: '0', transform: 'translateY(-12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        pulseGlow: { '0%,100%': { opacity: '1', boxShadow: '0 0 12px currentColor' }, '50%': { opacity: '0.7', boxShadow: '0 0 32px currentColor' } },
        fadeUp:    { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        blink:     { '0%,100%': { opacity: '1' }, '50%': { opacity: '0' } },
      },
    },
  },
  plugins: [],
};

export default config;
