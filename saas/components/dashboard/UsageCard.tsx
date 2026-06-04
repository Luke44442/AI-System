import { cn } from '@/lib/utils';

interface Props {
  label: string;
  value: number;
  limit: number | null;
  icon: React.ReactNode;
  color: 'violet' | 'sky' | 'emerald' | 'amber';
}

const COLOR_MAP = {
  violet: { text: 'text-violet-400', bg: 'bg-violet-500', bar: 'bg-violet-500', ring: 'border-violet-500/20 bg-violet-500/5' },
  sky:    { text: 'text-sky-400',    bg: 'bg-sky-500',    bar: 'bg-sky-500',    ring: 'border-sky-500/20 bg-sky-500/5'       },
  emerald:{ text: 'text-emerald-400',bg: 'bg-emerald-500',bar: 'bg-emerald-500',ring: 'border-emerald-500/20 bg-emerald-500/5'},
  amber:  { text: 'text-amber-400',  bg: 'bg-amber-500',  bar: 'bg-amber-500',  ring: 'border-amber-500/20 bg-amber-500/5'   },
};

export function UsageCard({ label, value, limit, icon, color }: Props) {
  const c = COLOR_MAP[color];
  const pct = limit && limit > 0 ? Math.min((value / limit) * 100, 100) : null;
  const unlimited = limit === -1;

  return (
    <div className={cn('glass p-4 rounded-xl border', c.ring)}>
      <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center mb-3', c.ring)}>
        <span className={c.text}>{icon}</span>
      </div>
      <div className={cn('text-2xl font-bold tabular-nums mb-0.5', c.text)}>
        {value.toLocaleString()}
      </div>
      <div className="text-xs text-slate-500 mb-2">{label}</div>
      {pct !== null ? (
        <>
          <div className="h-1 bg-white/5 rounded-full overflow-hidden">
            <div
              className={cn('h-full rounded-full transition-all', c.bar, pct >= 90 ? '!bg-red-500' : '')}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-600 mt-1">
            {value}/{limit} this month
          </div>
        </>
      ) : (
        <div className="text-[10px] text-slate-600">
          {unlimited ? '∞ unlimited' : 'All time'}
        </div>
      )}
    </div>
  );
}
