import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function scoreColor(score: number) {
  if (score >= 80) return 'text-emerald-500';
  if (score >= 65) return 'text-sky-500';
  if (score >= 50) return 'text-amber-500';
  return 'text-rose-500';
}

export function scoreGrade(score: number) {
  if (score >= 85) return 'A+';
  if (score >= 75) return 'A';
  if (score >= 65) return 'B';
  if (score >= 50) return 'C';
  return 'D';
}

export function formatDate(date: Date | string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(date));
}

export function truncate(str: string, n: number) {
  return str.length > n ? str.slice(0, n) + '…' : str;
}

export function platformIcon(platform: string) {
  const map: Record<string, string> = {
    TikTok: '🎵',
    YouTube: '▶️',
    Instagram: '📸',
    Twitter: '🐦',
    LinkedIn: '💼',
    Reddit: '🔴',
    Pinterest: '📌',
  };
  return map[platform] ?? '🌐';
}
