'use client';
import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send } from 'lucide-react';
import { GlassCard, PanelHeader, AgentAvatar, PulsingDot } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { deptColor, formatTime, generateId } from '@/lib/utils';
import type { AgentMessage } from '@/types';

// Synthetic conversation to demo agent interactions
const DEMO_CONVERSATION: AgentMessage[] = [
  { id: '1', from: 'TrendResearchAgent',    to: 'StrategicPlanningAgent', type: 'research_finding', subject: '', content: 'Found high-demand niche: AI-powered newsletter automation. Market signal strength: 94/100. Growing 340% YoY on social media.',                                   timestamp: new Date(Date.now() - 120000).toISOString() },
  { id: '2', from: 'MarketAnalysisAgent',   to: 'StrategicPlanningAgent', type: 'market_result',    subject: '', content: 'Market analysis complete. TAM: $8.2B. Top competitor has $2M ARR with 4.2★ rating. Gap identified: no tool handles end-to-end automation.',           timestamp: new Date(Date.now() - 90000).toISOString() },
  { id: '3', from: 'StrategicPlanningAgent',to: 'SupremeAgent',           type: 'opportunity_for_approval', subject: '', content: 'Opportunity scored 78/100. Estimated $3,200 MRR by Month 4. Startup cost: $200. Risk: LOW. Requesting CEO approval for execution.', timestamp: new Date(Date.now() - 60000).toISOString() },
  { id: '4', from: 'SupremeAgent',          to: 'AutomationBuilderAgent', type: 'directive',        subject: '', content: 'APPROVED. Score 78 exceeds threshold 65. Begin execution immediately. Budget: $200 max. Priority: HIGH. Report progress every 24h.',                   timestamp: new Date(Date.now() - 45000).toISOString() },
  { id: '5', from: 'AutomationBuilderAgent',to: 'MarketingAgent',         type: 'execute',          subject: '', content: 'Automation blueprint complete. 82% of operations automated. Tech stack: Python + FastAPI + OpenAI. Handoff to Marketing for launch.',                  timestamp: new Date(Date.now() - 30000).toISOString() },
  { id: '6', from: 'MarketingAgent',        to: 'ContentAgent',           type: 'create_content',   subject: '', content: 'Marketing strategy ready. SEO primary channel. Target keywords identified. Need landing page + 4 blog posts. Requesting content creation.',            timestamp: new Date(Date.now() - 15000).toISOString() },
  { id: '7', from: 'ContentAgent',          to: 'MarketingAgent',         type: 'content_ready',    subject: '', content: 'Content delivered: landing page (2,100 words), 4 SEO articles, 5-email welcome sequence, 10 social posts. All optimised for conversion.',             timestamp: new Date(Date.now() - 5000).toISOString() },
  { id: '8', from: 'RevenueTrackingAgent',  to: 'SupremeAgent',           type: 'report',           subject: '', content: 'Week 1 metrics: 847 organic visitors, 12 signups, 3 conversions @ $49. MRR: $147. Projected Month 1: $890. System operating within budget.',           timestamp: new Date(Date.now() - 1000).toISOString() },
];

const DEPT_MAP: Record<string, string> = {
  TrendResearchAgent:'research', MarketAnalysisAgent:'research', BusinessOpportunityAgent:'research',
  StrategicPlanningAgent:'strategy', RiskAnalysisAgent:'strategy', ValidationAgent:'strategy',
  SupremeAgent:'executive', AutomationBuilderAgent:'execution', MarketingAgent:'execution',
  ContentAgent:'execution', SalesAgent:'execution', RevenueTrackingAgent:'finance',
};

function ChatBubble({ msg, isOwn }: { msg: AgentMessage; isOwn: boolean }) {
  const dept  = DEPT_MAP[msg.from] ?? 'research';
  const color = deptColor(dept as never);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-2.5 ${isOwn ? 'flex-row-reverse' : ''}`}
    >
      <AgentAvatar name={msg.from} color={color} size={28} />
      <div className={`flex flex-col gap-1 max-w-[75%] ${isOwn ? 'items-end' : ''}`}>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[8px] font-bold" style={{ color }}>{msg.from.replace('Agent', '')}</span>
          <span className="font-mono text-[8px] text-slate-600">{formatTime(msg.timestamp)}</span>
          {msg.to !== 'all' && (
            <span className="font-mono text-[8px] text-slate-600">→ {msg.to.replace('Agent', '')}</span>
          )}
        </div>
        <div
          className={`px-3 py-2 rounded-lg text-[10px] font-mono leading-relaxed ${
            isOwn
              ? 'rounded-tr-sm text-slate-100'
              : 'rounded-tl-sm text-slate-200'
          }`}
          style={{
            background: isOwn ? `${color}20` : 'rgba(255,255,255,0.04)',
            border: `1px solid ${isOwn ? `${color}30` : 'rgba(255,255,255,0.06)'}`,
          }}
        >
          {msg.content}
        </div>
        <span
          className="font-mono text-[7px] px-1.5 py-0.5 rounded-sm"
          style={{ color, background: `${color}10`, border: `1px solid ${color}20` }}
        >
          {msg.type.replace(/_/g, ' ').toUpperCase()}
        </span>
      </div>
    </motion.div>
  );
}

export function AgentChat() {
  const storeMessages = useSystemStore(s => s.agentMessages);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<string>('all');

  // Combine demo + real messages
  const allMessages = [...DEMO_CONVERSATION, ...storeMessages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  const filtered = filter === 'all'
    ? allMessages
    : allMessages.filter(m => m.from.toLowerCase().includes(filter) || m.type.includes(filter));

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filtered.length]);

  const agents = ['all', 'CEO', 'Research', 'Strategy', 'Execution', 'Finance'];

  return (
    <GlassCard noPad className="flex flex-col h-full">
      <PanelHeader
        title="Agent Conversations"
        badge="LIVE"
        icon={<MessageSquare size={12} />}
        right={
          <div className="flex items-center gap-1.5">
            <PulsingDot color="#ec4899" size={5} />
            <span className="font-mono text-[8px] text-pink-400">{allMessages.length} msgs</span>
          </div>
        }
      />

      {/* Filter tabs */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-b border-[rgba(255,255,255,0.04)] overflow-x-auto">
        {agents.map(a => (
          <button
            key={a}
            onClick={() => setFilter(a === 'all' ? 'all' : a.toLowerCase())}
            className={`font-mono text-[8px] px-2 py-1 rounded-sm transition-all whitespace-nowrap ${
              (a === 'all' ? filter === 'all' : filter === a.toLowerCase())
                ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/30'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {a.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((msg, i) => (
            <ChatBubble
              key={msg.id}
              msg={msg}
              isOwn={msg.from === 'SupremeAgent'}
            />
          ))}
        </AnimatePresence>
      </div>
    </GlassCard>
  );
}
