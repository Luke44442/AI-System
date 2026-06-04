'use client';
import { AgentChat }     from '@/components/panels/AgentChat';
import { ActivityFeed }  from '@/components/panels/ActivityFeed';
import { GlassCard, PanelHeader, AgentAvatar, NeonBadge } from '@/components/ui';
import { deptColor, agentShortName } from '@/lib/utils';
import { MessageSquare, Users } from 'lucide-react';

const ALL_AGENTS = [
  { name: 'SupremeAgent',              dept: 'executive' },
  { name: 'TrendResearchAgent',        dept: 'research' },
  { name: 'MarketAnalysisAgent',       dept: 'research' },
  { name: 'BusinessOpportunityAgent',  dept: 'research' },
  { name: 'CompetitorIntelligenceAgent', dept: 'research' },
  { name: 'SocialMediaTrendAgent',     dept: 'research' },
  { name: 'StrategicPlanningAgent',    dept: 'strategy' },
  { name: 'BusinessModelAgent',        dept: 'strategy' },
  { name: 'RiskAnalysisAgent',         dept: 'strategy' },
  { name: 'ValidationAgent',           dept: 'strategy' },
  { name: 'AutomationBuilderAgent',    dept: 'execution' },
  { name: 'MarketingAgent',            dept: 'execution' },
  { name: 'ContentAgent',             dept: 'execution' },
  { name: 'SalesAgent',               dept: 'execution' },
  { name: 'OutreachAgent',            dept: 'execution' },
  { name: 'WebsiteBuilderAgent',       dept: 'execution' },
  { name: 'RevenueTrackingAgent',      dept: 'finance' },
  { name: 'CostAnalysisAgent',        dept: 'finance' },
  { name: 'ProfitOptimizationAgent',  dept: 'finance' },
  { name: 'LearningAgent',            dept: 'self_improvement' },
  { name: 'KnowledgeManagementAgent', dept: 'self_improvement' },
  { name: 'PromptOptimizationAgent',  dept: 'self_improvement' },
  { name: 'WorkflowOptimizationAgent',dept: 'self_improvement' },
];

export default function ChatPage() {
  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="font-orbitron text-base font-bold text-neon-blue">Agent Conversations</div>

      <div className="grid grid-cols-[220px_1fr_320px] gap-3 flex-1" style={{ minHeight: '70vh' }}>
        {/* Agent list */}
        <GlassCard noPad className="flex flex-col">
          <PanelHeader title="Agents" icon={<Users size={12} />} badge="22" />
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {ALL_AGENTS.map(a => {
              const color = deptColor(a.dept as never);
              return (
                <div key={a.name}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-surface-bright/40 transition-colors cursor-default">
                  <AgentAvatar name={a.name} color={color} size={24} />
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-[9px] text-slate-300 truncate">{agentShortName(a.name)}</div>
                    <div className="font-mono text-[7px]" style={{ color: `${color}80` }}>
                      {a.dept.replace('_', '-')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>

        {/* Main chat */}
        <AgentChat />

        {/* Activity feed */}
        <ActivityFeed maxItems={50} />
      </div>
    </div>
  );
}
