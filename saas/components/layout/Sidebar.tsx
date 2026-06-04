'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { TrendingUp, Target, FileText, CreditCard, Zap, LayoutDashboard } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV = [
  { href: '/',              label: 'Dashboard',    icon: LayoutDashboard },
  { href: '/research',      label: 'Research',     icon: TrendingUp },
  { href: '/opportunities', label: 'Opportunities',icon: Target },
  { href: '/content',       label: 'Content',      icon: FileText },
  { href: '/billing',       label: 'Billing',      icon: CreditCard },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside className="w-56 border-r border-white/[0.06] flex flex-col bg-white/[0.01]">
      {/* Logo */}
      <div className="flex items-center gap-2.5 p-5 border-b border-white/[0.06]">
        <div className="w-7 h-7 bg-violet-600 rounded-lg flex items-center justify-center shrink-0">
          <Zap size={14} className="text-white" />
        </div>
        <span className="font-bold text-white text-sm tracking-tight">GrowthIQ</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? path === '/' : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
                active
                  ? 'bg-violet-500/15 text-violet-300 font-medium'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.04]',
              )}
            >
              <Icon size={15} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-white/[0.06]">
        <div className="text-[10px] text-slate-600 px-2">
          GrowthIQ v1.0
        </div>
      </div>
    </aside>
  );
}
