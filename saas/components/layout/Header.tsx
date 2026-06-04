'use client';
import { signOut } from 'next-auth/react';
import type { Session } from 'next-auth';
import { LogOut, User } from 'lucide-react';
import { useState } from 'react';

interface Props {
  user: Session['user'];
}

export function Header({ user }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="h-14 border-b border-white/[0.06] flex items-center justify-between px-6 shrink-0">
      <div /> {/* Left slot — can add breadcrumbs here */}

      <div className="relative">
        <button
          onClick={() => setMenuOpen(o => !o)}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition px-2 py-1.5 rounded-lg hover:bg-white/[0.04]"
        >
          {user?.image ? (
            <img src={user.image} alt="" className="w-6 h-6 rounded-full" />
          ) : (
            <div className="w-6 h-6 bg-violet-600/60 rounded-full flex items-center justify-center">
              <User size={12} className="text-white" />
            </div>
          )}
          <span className="hidden sm:block">{user?.name ?? user?.email}</span>
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-48 glass rounded-xl p-1 shadow-xl z-50">
            <div className="px-3 py-2 border-b border-white/[0.06] mb-1">
              <p className="text-xs font-medium text-white truncate">{user?.name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
            </div>
            <button
              onClick={() => void signOut({ callbackUrl: '/login' })}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.04] rounded-lg transition"
            >
              <LogOut size={13} />
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
