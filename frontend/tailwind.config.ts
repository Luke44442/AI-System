import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: 'rgba(13,27,46,0.85)',
          deep:    '#070d1a',
          mid:     '#0d1b2e',
          bright:  '#122036',
        },
        neon: {
          blue:    '#00c8ff',
          purple:  '#9333ea',
          green:   '#00ff94',
          amber:   '#f59e0b',
          red:     '#ef4444',
          pink:    '#ec4899',
        },
        border: {
          DEFAULT: 'rgba(0,200,255,0.12)',
          bright:  'rgba(0,200,255,0.35)',
          purple:  'rgba(147,51,234,0.3)',
        },
      },
      fontFamily: {
        mono:     ['var(--font-jetbrains)', 'JetBrains Mono', 'Fira Code', 'monospace'],
        orbitron: ['var(--font-orbitron)', 'Orbitron', 'sans-serif'],
        sans:     ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'grid':           'linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px)',
        'glow-blue':      'radial-gradient(ellipse at center, rgba(0,200,255,0.15) 0%, transparent 70%)',
        'glow-purple':    'radial-gradient(ellipse at center, rgba(147,51,234,0.15) 0%, transparent 70%)',
        'panel-gradient': 'linear-gradient(135deg, rgba(13,27,46,0.9) 0%, rgba(7,13,26,0.95) 100%)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      boxShadow: {
        'neon-blue':   '0 0 20px rgba(0,200,255,0.3), 0 0 40px rgba(0,200,255,0.1)',
        'neon-purple': '0 0 20px rgba(147,51,234,0.3), 0 0 40px rgba(147,51,234,0.1)',
        'neon-green':  '0 0 20px rgba(0,255,148,0.3), 0 0 40px rgba(0,255,148,0.1)',
        'panel':       '0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
        'card':        '0 2px 16px rgba(0,0,0,0.4)',
      },
      animation: {
        'pulse-slow':    'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'glow-pulse':    'glowPulse 2s ease-in-out infinite',
        'scan-line':     'scanLine 4s linear infinite',
        'float':         'float 4s ease-in-out infinite',
        'slide-up':      'slideUp 0.4s ease-out',
        'fade-in':       'fadeIn 0.3s ease-out',
        'type':          'typewriter 3s steps(40) forwards',
        'count-up':      'countUp 0.6s ease-out',
        'border-flow':   'borderFlow 3s linear infinite',
        'warp':          'warp 8s linear infinite',
      },
      keyframes: {
        glowPulse: {
          '0%,100%': { opacity: '1', filter: 'brightness(1)' },
          '50%':     { opacity: '0.6', filter: 'brightness(1.4)' },
        },
        scanLine: {
          '0%':   { transform: 'translateY(-100vh)', opacity: '0.3' },
          '100%': { transform: 'translateY(100vh)', opacity: '0' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%':     { transform: 'translateY(-6px)' },
        },
        slideUp: {
          from: { transform: 'translateY(12px)', opacity: '0' },
          to:   { transform: 'translateY(0)',     opacity: '1' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        countUp: {
          from: { opacity: '0', transform: 'scale(0.85)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
        borderFlow: {
          '0%':   { backgroundPosition: '0% 50%' },
          '50%':  { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        warp: {
          '0%':   { transform: 'rotate(0deg) scale(1)' },
          '50%':  { transform: 'rotate(180deg) scale(1.05)' },
          '100%': { transform: 'rotate(360deg) scale(1)' },
        },
      },
    },
  },
  plugins: [],
};
export default config;
