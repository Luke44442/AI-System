import Link from 'next/link';
import { TrendingUp, ChevronRight } from 'lucide-react';
import { formatDate } from '@/lib/utils';

interface Run {
  id: string;
  topic: string;
  createdAt: Date;
}

export function RecentRuns({ runs }: { runs: Run[] }) {
  return (
    <div className="glass p-5 rounded-2xl">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <TrendingUp size={14} className="text-sky-400" />
          Recent Research
        </h2>
        <Link href="/research" className="text-[10px] text-violet-400 hover:text-violet-300 transition">
          New run →
        </Link>
      </div>
      {runs.length === 0 ? (
        <p className="text-xs text-slate-600 text-center py-6">No research runs yet.</p>
      ) : (
        <div className="space-y-1">
          {runs.map(run => (
            <div key={run.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/[0.03] transition group">
              <div className="w-1.5 h-1.5 rounded-full bg-violet-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-300 truncate group-hover:text-white transition">{run.topic}</p>
                <p className="text-[9px] text-slate-600">{formatDate(run.createdAt)}</p>
              </div>
              <ChevronRight size={11} className="text-slate-700 group-hover:text-slate-400 transition" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
