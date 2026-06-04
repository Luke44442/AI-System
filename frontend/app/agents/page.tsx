'use client';
import { motion } from 'framer-motion';
import { OrgChart }      from '@/components/panels/OrgChart';
import { ActivityFeed }  from '@/components/panels/ActivityFeed';
import { GlassCard, PanelHeader, PulsingDot, NeonBadge, AgentAvatar, ScoreBar } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { statusColor, deptColor, agentShortName, formatRelative } from '@/lib/utils';
import { Bot } from 'lucide-react';
import type { AgentStatus } from '@/types';

const STATUS_LABEL: Record<AgentStatus, string> = {
  running:     'RUNNING',
  idle:        'IDLE',
  blocked:     'BLOCKED',
  error:       'ERROR',
  not_started: 'STANDBY',
  stopped:     'STOPPED',
};

function AgentCard({ agent }: { agent: { name: string; department: string; status: string; tasks_completed: number; tasks_failed: number; last_active: string | null; current_task: string | null } }) {
  const color  = deptColor(agent.department);
  const sColor = statusColor(agent.status as AgentStatus);
  const total  = agent.tasks_completed + agent.tasks_failed;
  const rate   = total > 0 ? (agent.tasks_completed / total) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-3 rounded border border-[rgba(255,255,255,0.05)] bg-surface-mid/30 hover:border-[rgba(255,255,255,0.1)] transition-all"
    >
      <div className="flex items-start gap-2.5">
        <AgentAvatar name={agent.name} status={agent.status} color={color} size={36} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-1">
            <span className="font-mono text-[11px] font-bold text-slate-200 truncate">{agentShortName(agent.name)}</span>
            <span className="font-mono text-[8px] px-1.5 py-0.5 rounded-sm"
              style={{ color: sColor, background: `${sColor}15`, border: `1px solid ${sColor}30` }}>
              {STATUS_LABEL[agent.status as AgentStatus] ?? agent.status}
            </span>
          </div>
          <div className="font-mono text-[8px] text-slate-500 mt-0.5" style={{ color: `${color}99` }}>
            {agent.department.replace('_', '-').toUpperCase()}
          </div>
          {agent.current_task && (
            <div className="mt-1.5 px-2 py-1 rounded bg-neon-green/5 border border-neon-green/10">
              <span className="font-mono text-[8px] text-neon-green leading-relaxed">{agent.current_task}</span>
            </div>
          )}
        </div>
      </div>

      <div className="mt-2.5 grid grid-cols-2 gap-2 text-center border-t border-[rgba(255,255,255,0.04)] pt-2">
        <div>
          <div className="font-orbitron font-bold text-sm text-neon-green">{agent.tasks_completed}</div>
          <div className="font-mono text-[7px] text-slate-500">COMPLETED</div>
        </div>
        <div>
          <div className="font-orbitron font-bold text-sm text-neon-red">{agent.tasks_failed}</div>
          <div className="font-mono text-[7px] text-slate-500">FAILED</div>
        </div>
      </div>

      {total > 0 && <ScoreBar score={Math.round(rate)} label="Success rate" color={rate > 80 ? '#00ff94' : rate > 50 ? '#f59e0b' : '#ef4444'} className="mt-2" />}

      {agent.last_active && (
        <div className="font-mono text-[8px] text-slate-600 mt-1.5">
          Last active: {formatRelative(agent.last_active)}
        </div>
      )}
    </motion.div>
  );
}

export default function AgentsPage() {
  const agents = useSystemStore(s => s.agents);
  const running = agents.filter(a => a.status === 'running').length;
  const errors  = agents.filter(a => a.status === 'error').length;

  // Fill with placeholder data if no real agents
  const displayAgents = agents.length > 0 ? agents : [
    { name: 'SupremeAgent', department: 'executive', status: 'idle', tasks_completed: 14, tasks_failed: 0, last_active: new Date().toISOString(), current_task: null },
    { name: 'TrendResearchAgent', department: 'research', status: 'idle', tasks_completed: 47, tasks_failed: 2, last_active: new Date(Date.now()-60000).toISOString(), current_task: null },
    { name: 'MarketAnalysisAgent', department: 'research', status: 'idle', tasks_completed: 31, tasks_failed: 1, last_active: new Date(Date.now()-120000).toISOString(), current_task: null },
    { name: 'StrategicPlanningAgent', department: 'strategy', status: 'idle', tasks_completed: 22, tasks_failed: 0, last_active: new Date(Date.now()-180000).toISOString(), current_task: null },
    { name: 'AutomationBuilderAgent', department: 'execution', status: 'idle', tasks_completed: 9, tasks_failed: 1, last_active: new Date(Date.now()-240000).toISOString(), current_task: null },
    { name: 'RevenueTrackingAgent', department: 'finance', status: 'idle', tasks_completed: 38, tasks_failed: 0, last_active: new Date(Date.now()-300000).toISOString(), current_task: null },
  ];

  return (
    <div className="flex flex-col gap-3">
      {/* Stat strip */}
      <div className="flex items-center gap-3">
        <div className="font-orbitron text-base font-bold text-neon-blue">Agent Management</div>
        <div className="ml-auto flex gap-2">
          <NeonBadge label={`${running} running`} color="#00ff94" size="sm" />
          <NeonBadge label={`${displayAgents.length} total`} color="#00c8ff" size="sm" />
          {errors > 0 && <NeonBadge label={`${errors} errors`} color="#ef4444" size="sm" />}
        </div>
      </div>

      {/* Org chart */}
      <div style={{ minHeight: 340 }}>
        <OrgChart />
      </div>

      {/* Agent grid */}
      <GlassCard noPad>
        <PanelHeader title="All Agents" badge={`${displayAgents.length} agents`} icon={<Bot size={12} />} />
        <div className="p-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {displayAgents.map(a => <AgentCard key={a.name} agent={a} />)}
        </div>
      </GlassCard>

      {/* Activity */}
      <div style={{ minHeight: 300 }}>
        <ActivityFeed maxItems={40} />
      </div>
    </div>
  );
}
