'use client';
import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity } from 'lucide-react';
import { GlassCard, PanelHeader, PulsingDot } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { deptColor, activityColor, formatTime, agentShortName } from '@/lib/utils';
import type { ActivityItem } from '@/types';

const TYPE_PREFIX: Record<string, string> = {
  info:      '→',
  success:   '✓',
  warning:   '⚠',
  error:     '✗',
  decision:  '★',
  discovery: '◈',
};

function FeedRow({ item }: { item: ActivityItem }) {
  const typeColor = activityColor(item.type);
  const dColor    = deptColor(item.department as never);
  return (
    <motion.div
      initial={{ opacity: 0, x: -8, height: 0 }}
      animate={{ opacity: 1, x: 0, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-2.5 py-1.5 border-b border-[rgba(255,255,255,0.03)] group hover:bg-[rgba(0,200,255,0.02)] transition-colors"
    >
      {/* Timestamp */}
      <span className="font-mono text-[8px] text-slate-600 pt-0.5 w-14 flex-shrink-0">
        {formatTime(item.timestamp)}
      </span>

      {/* Type indicator */}
      <span className="font-mono text-[10px] w-3 flex-shrink-0 pt-0.5" style={{ color: typeColor }}>
        {TYPE_PREFIX[item.type] ?? '·'}
      </span>

      {/* Agent name */}
      <span
        className="font-mono text-[9px] font-bold flex-shrink-0 w-24 truncate pt-0.5"
        style={{ color: dColor }}
      >
        {agentShortName(item.agent)}
      </span>

      {/* Message */}
      <span className="font-mono text-[10px] text-slate-300 leading-relaxed flex-1 min-w-0">
        {item.message}
      </span>
    </motion.div>
  );
}

export function ActivityFeed({ maxItems = 80 }: { maxItems?: number }) {
  const feed = useSystemStore(s => s.activityFeed);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  // Auto-scroll if pinned to bottom
  useEffect(() => {
    if (pinned.current && scrollRef.current) {
      scrollRef.current.scrollTop = 0; // feed is reversed (newest first)
    }
  }, [feed.length]);

  return (
    <GlassCard noPad className="flex flex-col h-full">
      <PanelHeader
        title="Agent Activity Feed"
        badge="LIVE"
        icon={<Activity size={12} />}
        right={
          <div className="flex items-center gap-1.5">
            <PulsingDot color="#00ff94" size={5} />
            <span className="font-mono text-[8px] text-neon-green">{feed.length} events</span>
          </div>
        }
      />

      {/* Legend */}
      <div className="flex items-center gap-3 px-4 py-1.5 border-b border-[rgba(255,255,255,0.04)] bg-surface-mid/20">
        {(['research','strategy','execution','finance'] as const).map(d => (
          <div key={d} className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: deptColor(d) }} />
            <span className="font-mono text-[8px] text-slate-500 capitalize">{d}</span>
          </div>
        ))}
      </div>

      {/* Feed */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-3 py-1 scrollbar-thin"
        style={{ maxHeight: '100%' }}
      >
        <AnimatePresence mode="popLayout" initial={false}>
          {feed.slice(0, maxItems).map(item => (
            <FeedRow key={item.id} item={item} />
          ))}
        </AnimatePresence>

        {feed.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <span className="font-mono text-[10px] text-slate-600">Awaiting agent activity...</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
