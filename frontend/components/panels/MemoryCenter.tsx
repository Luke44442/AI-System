'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Search, BookOpen, TrendingUp, AlertTriangle, Lightbulb } from 'lucide-react';
import { GlassCard, PanelHeader, NeonBadge, ScoreBar } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import type { Lesson, KnowledgeInsight } from '@/types';

// Demo knowledge for when no API data is available
const DEMO_LESSONS: Lesson[] = [
  { category: 'success', title: 'AI automation niches score highest', description: 'Opportunities combining AI + automation consistently score 75+. Prioritise these categories.', recommended_action: 'Weight automation_potential by 1.5x in scoring formula', confidence: 9, priority: 9 },
  { category: 'success', title: 'Free search providers reduce cost by 94%', description: 'DuckDuckGo fallback eliminated $340/mo in Serper API costs with negligible quality loss.', recommended_action: 'Keep DuckDuckGo as primary with Serper as premium fallback only', confidence: 10, priority: 8 },
  { category: 'failure', title: 'Generic content performs poorly', description: 'Content generated without specific audience persona data converts at 0.8% vs 3.2% with ICP data.', recommended_action: 'Always pass target audience persona to ContentAgent before generation', confidence: 8, priority: 9 },
  { category: 'improvement', title: 'Parallel validation cuts cycle time 60%', description: 'Running Market + Competitor analysis in parallel reduced cycle time from 18 to 7 minutes.', recommended_action: 'Implement parallel execution for all independent analysis tasks', confidence: 9, priority: 7 },
  { category: 'success', title: 'SaaS with monthly billing has highest LTV', description: 'Monthly SaaS models show 4.2x higher LTV:CAC ratio versus one-time products in our data.', recommended_action: 'Prefer recurring revenue models when scoring opportunities', confidence: 8, priority: 8 },
];

const DEMO_INSIGHTS: KnowledgeInsight[] = [
  { insight: 'Automation potential is the strongest predictor of long-term success', implication: 'Weight automation 25% higher in opportunity scoring', priority: 10 },
  { insight: 'Markets under $500M TAM with clear pain points outperform large generic markets', implication: 'Niche-down strategy should be the default approach', priority: 9 },
  { insight: 'Winning opportunities share: low barrier, high automation, clear buyer persona', implication: 'Add this triple-filter as pre-screening before full scoring', priority: 9 },
];

const CATEGORY_CONFIG = {
  success:     { label: 'Success',     color: '#00ff94', icon: TrendingUp },
  failure:     { label: 'Failure',     color: '#ef4444', icon: AlertTriangle },
  improvement: { label: 'Improvement', color: '#00c8ff', icon: TrendingUp },
};

function LessonCard({ lesson }: { lesson: Lesson }) {
  const cfg = CATEGORY_CONFIG[lesson.category as keyof typeof CATEGORY_CONFIG] ?? CATEGORY_CONFIG.improvement;
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-3 rounded border border-[rgba(255,255,255,0.05)] bg-surface-mid/20 hover:border-[rgba(255,255,255,0.09)] transition-all"
    >
      <div className="flex items-start gap-2 mb-1.5">
        <cfg.icon size={10} style={{ color: cfg.color, marginTop: 2, flexShrink: 0 }} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <span className="font-mono text-[10px] font-bold text-slate-200 leading-snug">{lesson.title}</span>
            <NeonBadge label={cfg.label} color={cfg.color} />
          </div>
          <p className="font-mono text-[9px] text-slate-400 mt-1 leading-relaxed">{lesson.description}</p>
          <div className="mt-2 p-1.5 rounded bg-surface-bright/30 border border-[rgba(255,255,255,0.05)]">
            <span className="font-mono text-[8px] text-slate-500">ACTION: </span>
            <span className="font-mono text-[9px] text-slate-300">{lesson.recommended_action}</span>
          </div>
        </div>
      </div>
      <div className="flex gap-4 mt-2">
        <ScoreBar score={lesson.confidence * 10} label="Confidence" color={cfg.color} className="flex-1" />
        <ScoreBar score={lesson.priority * 10}   label="Priority"   color="#9333ea"   className="flex-1" />
      </div>
    </motion.div>
  );
}

export function MemoryCenter() {
  const { lessons: storeLessons, insights: storeInsights } = useSystemStore();
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState<'lessons' | 'insights'>('lessons');

  const lessons  = storeLessons.length  > 0 ? storeLessons  : DEMO_LESSONS;
  const insights = storeInsights.length > 0 ? storeInsights : DEMO_INSIGHTS;

  const filteredLessons = search
    ? lessons.filter(l => l.title.toLowerCase().includes(search.toLowerCase()) || l.description.toLowerCase().includes(search.toLowerCase()))
    : lessons;

  return (
    <GlassCard noPad className="flex flex-col h-full">
      <PanelHeader
        title="Memory Center"
        badge={`${lessons.length} lessons`}
        badgeColor="#ec4899"
        icon={<Brain size={12} />}
      />

      {/* Search + tabs */}
      <div className="px-3 pt-2 pb-0 space-y-2">
        <div className="relative">
          <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search knowledge base..."
            className="w-full pl-8 pr-3 py-2 bg-surface-mid/50 border border-[rgba(255,255,255,0.06)] rounded text-[10px] font-mono text-slate-300 placeholder-slate-600 focus:outline-none focus:border-neon-blue/30"
          />
        </div>
        <div className="flex gap-1">
          {(['lessons', 'insights'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`font-mono text-[9px] px-3 py-1 rounded-sm transition-all capitalize ${
                tab === t
                  ? 'bg-neon-blue/15 text-neon-blue border border-neon-blue/25'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        <AnimatePresence mode="popLayout">
          {tab === 'lessons' && filteredLessons.map((l, i) => (
            <LessonCard key={l.title + i} lesson={l} />
          ))}

          {tab === 'insights' && insights.map((ins, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="p-3 rounded border border-[rgba(147,51,234,0.2)] bg-[rgba(147,51,234,0.05)]"
            >
              <div className="flex items-start gap-2">
                <Lightbulb size={10} className="text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-mono text-[10px] font-bold text-slate-200 leading-snug">{ins.insight}</p>
                  <p className="font-mono text-[9px] text-purple-300/70 mt-1">{ins.implication}</p>
                  <div className="mt-1.5 font-mono text-[8px] text-slate-500">
                    Priority: <span className="text-purple-400 font-bold">{ins.priority}/10</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {tab === 'lessons' && filteredLessons.length === 0 && (
          <div className="flex items-center justify-center h-16">
            <span className="font-mono text-[9px] text-slate-600">No lessons match your search</span>
          </div>
        )}
      </div>

      {/* Stats footer */}
      <div className="px-3 py-2 border-t border-[rgba(255,255,255,0.04)] flex items-center gap-4">
        <span className="font-mono text-[8px] text-slate-600">
          <span className="text-neon-green">{lessons.filter(l => l.category === 'success').length}</span> successes
        </span>
        <span className="font-mono text-[8px] text-slate-600">
          <span className="text-neon-red">{lessons.filter(l => l.category === 'failure').length}</span> failures
        </span>
        <span className="font-mono text-[8px] text-slate-600">
          <span className="text-neon-blue">{lessons.filter(l => l.category === 'improvement').length}</span> improvements
        </span>
      </div>
    </GlassCard>
  );
}
