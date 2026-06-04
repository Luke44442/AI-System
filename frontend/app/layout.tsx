import type { Metadata } from 'next';
import './globals.css';
import { AppShell } from '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: 'AI Wealth System — Autonomous Command Center',
  description: 'Multi-agent AI ecosystem for autonomous wealth research and execution',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {/* Scanline overlay for authentic CRT feel */}
        <div className="scan-overlay" />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
