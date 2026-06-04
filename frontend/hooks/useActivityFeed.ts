'use client';
import { useEffect, useRef } from 'react';
import { useSystemStore } from '@/store/useSystemStore';
import { generateId } from '@/lib/utils';
import type { ActivityItem, ActivityType, Department } from '@/types';

interface MockEntry {
  agent: string;
  dept: Department;
  message: string;
  type: ActivityType;
}

const MOCK_STREAM: MockEntry[] = [
  { agent: 'TrendResearchAgent',         dept: 'research',        type: 'info',      message: 'Scanning 1,247 SaaS databases for emerging niches...' },
  { agent: 'SocialMediaTrendAgent',      dept: 'research',        type: 'discovery', message: 'Detected viral AI productivity niche on TikTok (+340% MoM)' },
  { agent: 'MarketAnalysisAgent',        dept: 'research',        type: 'discovery', message: 'Identified $2.3B market gap in AI-powered content automation' },
  { agent: 'CompetitorIntelligenceAgent',dept: 'research',        type: 'info',      message: 'Mapped 14 competitors in newsletter automation space' },
  { agent: 'BusinessOpportunityAgent',   dept: 'research',        type: 'success',   message: 'Qualified: "AI Newsletter Platform" — confidence: 91%' },
  { agent: 'StrategicPlanningAgent',     dept: 'strategy',        type: 'info',      message: 'Scoring opportunity "AI Newsletter Platform" → 78/100' },
  { agent: 'ValidationAgent',           dept: 'strategy',        type: 'success',   message: 'Demand validated: 2,400 Reddit posts confirm pain point exists' },
  { agent: 'RiskAnalysisAgent',         dept: 'strategy',        type: 'warning',   message: 'Medium risk identified: platform dependency on OpenAI API' },
  { agent: 'BusinessModelAgent',        dept: 'strategy',        type: 'success',   message: 'Business model designed: SaaS $49-$299/mo, LTV:CAC = 4.2:1' },
  { agent: 'SupremeAgent',              dept: 'executive',        type: 'decision',  message: 'APPROVED: "AI Newsletter Platform" (score 78 > threshold 65)' },
  { agent: 'AutomationBuilderAgent',    dept: 'execution',        type: 'info',      message: 'Building automation blueprint: 80% hands-free target achieved' },
  { agent: 'WebsiteBuilderAgent',       dept: 'execution',        type: 'info',      message: 'Scaffolding Next.js landing page with conversion-optimised layout' },
  { agent: 'ContentAgent',             dept: 'execution',        type: 'success',   message: 'Generated 5,200-word SEO article targeting "AI newsletter tools"' },
  { agent: 'MarketingAgent',            dept: 'execution',        type: 'success',   message: 'Content strategy live: 12-week calendar, est. 8,400 organic visits/mo' },
  { agent: 'SalesAgent',               dept: 'execution',        type: 'info',      message: 'Optimising sales funnel: 3 CTA variants queued for A/B test' },
  { agent: 'OutreachAgent',            dept: 'execution',        type: 'info',      message: 'Personalised outreach sequences crafted for 150 ICP targets' },
  { agent: 'RevenueTrackingAgent',      dept: 'finance',          type: 'success',   message: 'Projected monthly revenue updated: $3,200 (Month 1 estimate)' },
  { agent: 'CostAnalysisAgent',        dept: 'finance',          type: 'info',      message: 'Infrastructure costs optimised — 23% reduction achieved' },
  { agent: 'ProfitOptimizationAgent',  dept: 'finance',          type: 'success',   message: 'Upsell strategy identified: annual plan conversion +18% margin' },
  { agent: 'LearningAgent',            dept: 'self_improvement', type: 'info',      message: 'Extracting lessons from cycle #7 — 4 high-confidence patterns found' },
  { agent: 'KnowledgeManagementAgent', dept: 'self_improvement', type: 'success',   message: 'Knowledge base updated: 847 entries, 94% retrieval accuracy' },
  { agent: 'PromptOptimizationAgent',  dept: 'self_improvement', type: 'success',   message: 'ResearchAgent prompt improved — output quality up 12%' },
  { agent: 'WorkflowOptimizationAgent',dept: 'self_improvement', type: 'info',      message: 'Bottleneck identified in validation phase — parallelising 3 tasks' },
  { agent: 'TrendResearchAgent',         dept: 'research',        type: 'discovery', message: 'New opportunity detected: "AI Voice Agent for SMB Customer Support"' },
  { agent: 'StrategicPlanningAgent',     dept: 'strategy',        type: 'info',      message: 'Scoring "AI Voice Agent for SMB" → calculating weighted score...' },
  { agent: 'MarketAnalysisAgent',        dept: 'research',        type: 'success',   message: 'Market sizing complete: TAM $18B, SAM $2.1B, SOM $140M' },
  { agent: 'SupremeAgent',              dept: 'executive',        type: 'decision',  message: 'Allocating resources to top 3 approved opportunities this cycle' },
  { agent: 'RevenueTrackingAgent',      dept: 'finance',          type: 'success',   message: 'ROI positive milestone hit — cumulative profit: $847' },
];

export function useActivityFeed(intervalMs = 2500) {
  const addActivity = useSystemStore(s => s.addActivity);
  const idx = useRef(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Seed with initial entries
    const now = Date.now();
    for (let i = Math.min(8, MOCK_STREAM.length - 1); i >= 0; i--) {
      const entry = MOCK_STREAM[i];
      addActivity({
        id: generateId(),
        agent: entry.agent,
        department: entry.dept,
        message: entry.message,
        type: entry.type,
        timestamp: new Date(now - i * 3000).toISOString(),
      } satisfies ActivityItem);
    }
    idx.current = 8;

    // Stream new entries
    timer.current = setInterval(() => {
      const entry = MOCK_STREAM[idx.current % MOCK_STREAM.length];
      addActivity({
        id: generateId(),
        agent: entry.agent,
        department: entry.dept,
        message: entry.message,
        type: entry.type,
        timestamp: new Date().toISOString(),
      });
      idx.current++;
    }, intervalMs + Math.random() * 1500);

    return () => { if (timer.current) clearInterval(timer.current); };
  }, [addActivity, intervalMs]);
}
