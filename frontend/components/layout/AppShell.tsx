'use client';
import { useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useActivityFeed } from '@/hooks/useActivityFeed';
import { useSystemStore } from '@/store/useSystemStore';
import { agentsApi, opportunitiesApi, revenueApi, memoryApi, systemApi } from '@/lib/api';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function AppShell({ children }: { children: React.ReactNode }) {
  useWebSocket();
  useActivityFeed();

  const {
    setAgents, setDeptSummary, setPipeline,
    setRevenue, setKpis, setLessons, setInsights,
    setApiOnline, applyDashboard,
  } = useSystemStore();

  // Initial data load
  useEffect(() => {
    async function bootstrap() {
      try {
        const health = await systemApi.health();
        setApiOnline(health.status === 'ok');
      } catch {
        setApiOnline(false);
        return;
      }

      // Parallel data fetch
      const [agents, depts, pipeline, revenue, kpis, dashboard, lessons] = await Promise.allSettled([
        agentsApi.list(),
        agentsApi.depts(),
        opportunitiesApi.pipeline(),
        revenueApi.summary(),
        revenueApi.kpis(),
        systemApi.dashboard(),
        memoryApi.lessons(30),
      ]);

      if (agents.status       === 'fulfilled') setAgents(agents.value);
      if (depts.status        === 'fulfilled') setDeptSummary(depts.value as never);
      if (pipeline.status     === 'fulfilled') {
        const p = pipeline.value.pipeline;
        setPipeline(p.pending.items, p.qualified.items, p.approved.items);
      }
      if (revenue.status      === 'fulfilled') setRevenue(revenue.value);
      if (kpis.status         === 'fulfilled') setKpis(kpis.value);
      if (dashboard.status    === 'fulfilled') applyDashboard(dashboard.value as never);
      if (lessons.status      === 'fulfilled') setLessons(lessons.value.lessons);
    }

    void bootstrap();
    // Refresh every 30 seconds
    const id = setInterval(() => void bootstrap(), 30_000);
    return () => clearInterval(id);
  }, [setAgents, setDeptSummary, setPipeline, setRevenue, setKpis, setLessons, setInsights, setApiOnline, applyDashboard]);

  return (
    <div className="flex min-h-screen bg-surface-deep text-slate-200">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-grid bg-[length:40px_40px] opacity-100" />
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-glow-blue opacity-30 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-glow-purple opacity-20 blur-3xl" />
      </div>

      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="relative flex flex-col flex-1 min-w-0 z-10">
        <Header />
        <main className="flex-1 overflow-auto p-4">
          {children}
        </main>

        {/* Status bar */}
        <footer className="px-5 py-1.5 border-t border-[rgba(0,200,255,0.06)] bg-surface-deep/95 flex items-center justify-between">
          <span className="font-mono text-[8px] text-slate-600 tracking-wider">
            AI WEALTH SYSTEM v1.0 · AUTONOMOUS OPERATION MODE
          </span>
          <span className="font-mono text-[8px] text-slate-600 tracking-wider">
            LEGAL & ETHICAL INCOME GENERATION ONLY
          </span>
        </footer>
      </div>
    </div>
  );
}
