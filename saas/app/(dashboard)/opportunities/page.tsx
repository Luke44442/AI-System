import { getAuthSession } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { Target, Trash2 } from 'lucide-react';
import { cn, scoreColor, scoreGrade, platformIcon, formatDate } from '@/lib/utils';

export default async function OpportunitiesPage() {
  const session = await getAuthSession();
  const userId = session!.user.id;

  const opps = await prisma.savedOpportunity.findMany({
    where: { project: { workspace: { userId } } },
    orderBy: { overallScore: 'desc' },
    take: 100,
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target size={22} className="text-emerald-400" />
            Saved Opportunities
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {opps.length} opportunities saved across all projects
          </p>
        </div>
      </div>

      {opps.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center">
          <Target size={32} className="text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">No opportunities saved yet.</p>
          <p className="text-slate-600 text-xs mt-1">
            Run a research session and click the bookmark icon to save opportunities here.
          </p>
          <a
            href="/research"
            className="inline-block mt-4 bg-violet-600 hover:bg-violet-500 text-white text-sm px-4 py-2 rounded-lg transition"
          >
            Start researching →
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {opps.map(opp => (
            <div key={opp.id} className="glass p-4 rounded-xl hover:border-violet-500/20 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={cn('text-xl font-bold', scoreColor(opp.overallScore))}>
                      {Math.round(opp.overallScore)}
                    </span>
                    <span className="text-[10px] text-slate-500">{scoreGrade(opp.overallScore)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white leading-snug">{opp.title}</h3>
                  <p className="text-[10px] text-slate-500 mt-0.5">{opp.niche}</p>
                </div>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed mb-3 line-clamp-2">{opp.description}</p>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mb-3">
                {[
                  { label: 'Virality', v: opp.viralityScore },
                  { label: 'Monetization', v: opp.monetizationScore },
                  { label: 'Low Competition', v: 100 - opp.competitionScore },
                  { label: 'Ease', v: opp.easeScore },
                ].map(({ label, v }) => (
                  <div key={label}>
                    <div className="flex justify-between text-[9px] text-slate-600 mb-0.5">
                      <span>{label}</span>
                      <span className={scoreColor(v)}>{Math.round(v)}</span>
                    </div>
                    <div className="h-0.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={cn('h-full rounded-full', v >= 70 ? 'bg-emerald-500' : v >= 50 ? 'bg-sky-500' : 'bg-amber-500')}
                        style={{ width: `${v}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-1 flex-wrap mb-2">
                {opp.platforms.map(p => (
                  <span key={p} className="text-[9px] bg-white/[0.04] border border-white/[0.05] px-1.5 py-0.5 rounded text-slate-400">
                    {platformIcon(p)} {p}
                  </span>
                ))}
              </div>

              {opp.contentAngle && (
                <p className="text-[9px] text-slate-600 border-t border-white/[0.04] pt-2 mt-2">
                  <span className="text-violet-400">Angle:</span> {opp.contentAngle}
                </p>
              )}

              <p className="text-[9px] text-slate-700 mt-2">{formatDate(opp.createdAt)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
