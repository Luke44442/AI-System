'use client';
import { motion } from 'framer-motion';
import { useSystemStore } from '@/store/useSystemStore';
import { GlassCard, PanelHeader } from '@/components/ui';
import { deptColor, statusColor, agentShortName } from '@/lib/utils';
import { Network } from 'lucide-react';

interface DeptNode {
  id: string;
  label: string;
  color: string;
  agents: string[];
}

const DEPARTMENTS: DeptNode[] = [
  { id: 'research',         label: 'Research',      color: '#00c8ff', agents: ['TrendResearchAgent','BusinessOpportunityAgent','MarketAnalysisAgent','CompetitorIntelligenceAgent','SocialMediaTrendAgent'] },
  { id: 'strategy',         label: 'Strategy',      color: '#9333ea', agents: ['StrategicPlanningAgent','BusinessModelAgent','RiskAnalysisAgent','ValidationAgent'] },
  { id: 'execution',        label: 'Execution',     color: '#00ff94', agents: ['AutomationBuilderAgent','WebsiteBuilderAgent','MarketingAgent','SalesAgent','ContentAgent','OutreachAgent'] },
  { id: 'finance',          label: 'Finance',       color: '#f59e0b', agents: ['RevenueTrackingAgent','CostAnalysisAgent','ProfitOptimizationAgent'] },
  { id: 'self_improvement', label: 'Self-Improve',  color: '#ec4899', agents: ['KnowledgeManagementAgent','LearningAgent','PromptOptimizationAgent','WorkflowOptimizationAgent'] },
];

export function OrgChart() {
  const agents = useSystemStore(s => s.agents);
  const statusMap = Object.fromEntries(agents.map(a => [a.name, a.status]));

  return (
    <GlassCard noPad className="h-full">
      <PanelHeader
        title="Agent Organization"
        badge="22 AGENTS"
        badgeColor="#9333ea"
        icon={<Network size={12} />}
      />

      <div className="p-4 flex flex-col items-center gap-6 overflow-auto">
        {/* CEO Node */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative"
        >
          <div className="relative px-6 py-3 rounded-lg border-2 border-amber-500/40 bg-amber-500/10 flex flex-col items-center gap-1"
            style={{ boxShadow: '0 0 20px rgba(245,158,11,0.2)' }}>
            <div className="font-orbitron text-xs font-bold text-amber-400 tracking-wider">SUPREME AGENT</div>
            <div className="font-mono text-[9px] text-amber-300/70">Chief Executive Officer</div>
            <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse-slow" style={{ boxShadow: '0 0 6px #f59e0b' }} />
              <span className="font-mono text-[8px] text-amber-400">ACTIVE</span>
            </div>
          </div>
        </motion.div>

        {/* Connector to departments */}
        <svg width="600" height="28" className="overflow-visible -my-3">
          <motion.line x1="300" y1="0" x2="300" y2="14" stroke="#f59e0b" strokeWidth="1" strokeOpacity="0.4"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.5 }} />
          {/* Horizontal bar */}
          <motion.line x1="60" y1="14" x2="540" y2="14" stroke="rgba(0,200,255,0.2)" strokeWidth="1"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8, delay: 0.3 }} />
          {/* Verticals to depts */}
          {[60, 180, 300, 420, 540].map((x, i) => (
            <motion.line key={i} x1={x} y1="14" x2={x} y2="28"
              stroke={DEPARTMENTS[i].color} strokeWidth="1" strokeOpacity="0.5"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
              transition={{ duration: 0.4, delay: 0.5 + i * 0.08 }} />
          ))}
        </svg>

        {/* Department nodes */}
        <div className="grid grid-cols-5 gap-3 w-full">
          {DEPARTMENTS.map((dept, di) => {
            const runningCount = dept.agents.filter(a => (statusMap[a] ?? 'not_started') === 'running').length;
            return (
              <motion.div
                key={dept.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + di * 0.08 }}
                className="flex flex-col gap-2"
              >
                {/* Dept header */}
                <div
                  className="p-2 rounded border flex flex-col gap-1"
                  style={{ borderColor: `${dept.color}30`, background: `${dept.color}08` }}
                >
                  <div className="font-orbitron text-[9px] font-bold tracking-wider" style={{ color: dept.color }}>
                    {dept.label}
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-[8px] text-slate-500">{runningCount}/{dept.agents.length}</span>
                    {runningCount > 0 && (
                      <span className="w-1.5 h-1.5 rounded-full animate-pulse-slow"
                        style={{ background: dept.color, boxShadow: `0 0 4px ${dept.color}` }} />
                    )}
                  </div>
                </div>

                {/* Agent list */}
                <div className="space-y-1">
                  {dept.agents.map((agentName, ai) => {
                    const status = statusMap[agentName] ?? 'not_started';
                    const sColor = statusColor(status as never);
                    const short  = agentShortName(agentName);
                    return (
                      <motion.div
                        key={agentName}
                        initial={{ opacity: 0, x: -4 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 + di * 0.05 + ai * 0.03 }}
                        className="flex items-center gap-1.5 px-2 py-1 rounded border border-[rgba(255,255,255,0.04)] bg-surface-mid/30 group hover:border-[rgba(255,255,255,0.08)] transition-all"
                        title={agentName}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{
                            background: sColor,
                            boxShadow: status === 'running' ? `0 0 4px ${sColor}` : undefined,
                          }}
                        />
                        <span className="font-mono text-[8px] text-slate-400 truncate group-hover:text-slate-200 transition-colors">
                          {short}
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </GlassCard>
  );
}
