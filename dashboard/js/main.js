/* ══════════════════════════════════════════════════════════════════
   AI WEALTH SYSTEM — Dashboard Controller
══════════════════════════════════════════════════════════════════ */

const API_BASE = window.location.origin;
const WS_URL   = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/dashboard`;

let ws = null;
let revenueChart = null;
const revHistory = { labels: [], revenue: [], costs: [] };

// ─── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  updateClock();
  setInterval(updateClock, 1000);
  initChart();
  fetchDashboard();
  fetchAgents();
  fetchOpportunities();
  connectWebSocket();
  setInterval(fetchDashboard, 30_000);
  setInterval(fetchAgents, 15_000);
  setInterval(fetchOpportunities, 60_000);
  addLog('sys', 'AI Wealth System dashboard initialised');
});

// ─── Clock ─────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('datetime').textContent =
    now.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
}

// ─── WebSocket ─────────────────────────────────────────────────────
function connectWebSocket() {
  if (ws) ws.close();
  ws = new WebSocket(WS_URL);
  const indicator = document.getElementById('ws-status');

  ws.onopen = () => {
    indicator.textContent = 'WS: CONNECTED';
    indicator.className = 'ws-indicator connected';
    addLog('sys', 'WebSocket connection established');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'ping') return;
      if (msg.type === 'init' && msg.data) applyInit(msg.data);
      if (msg.type === 'update') handleUpdate(msg);
    } catch (e) { /* ignore */ }
  };

  ws.onclose = () => {
    indicator.textContent = 'WS: RECONNECTING';
    indicator.className = 'ws-indicator';
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => {
    indicator.textContent = 'WS: ERROR';
    indicator.className = 'ws-indicator';
  };
}

function applyInit(data) {
  if (data.ceo_kpis) updateKPIs(data.ceo_kpis);
  if (data.finance) updateFinance(data.finance);
  document.getElementById('stage-approved').textContent = data.approved_count || 0;
  document.getElementById('stage-pending').textContent  = data.pending_count  || 0;
}

function handleUpdate(msg) {
  if (msg.channel && msg.channel.includes('finance')) updateFinance(msg.data);
  if (msg.channel && msg.channel.includes('ceo_status')) {
    updateKPIs(msg.data.kpis || {});
    updateObjectives(msg.data.objectives || []);
    addLog('ceo', `CEO cycle complete — KPIs updated`);
  }
}

// ─── API calls ─────────────────────────────────────────────────────
async function fetchDashboard() {
  try {
    const res  = await fetch(`${API_BASE}/api/system/dashboard`);
    if (!res.ok) return;
    const data = await res.json();
    updateKPIs(data.ceo || {});
    updateFinance(data.finance || {});
    if (data.ceo_review && data.ceo_review.review)
      document.getElementById('ceo-review').textContent = data.ceo_review.review.slice(0, 400);
    updateObjectives((data.ceo.objectives) || []);
    // Pipeline counts
    document.getElementById('stage-approved').textContent = data.approved_opportunities || 0;
    document.getElementById('stage-pending').textContent  = data.pending_research || 0;
    // KB
    const lessons = data.knowledge_insights?.insights?.length || 0;
    document.getElementById('kb-insights').textContent = lessons;
  } catch (e) { /* offline */ }
}

async function fetchAgents() {
  try {
    const res  = await fetch(`${API_BASE}/api/agents/`);
    if (!res.ok) return;
    const data = await res.json();
    renderAgentTree(data);
    // Department summary
    const deptRes  = await fetch(`${API_BASE}/api/agents/departments/summary`);
    if (deptRes.ok) {
      const depts = await deptRes.json();
      renderDepts(depts);
    }
    const active = data.filter(a => a.status === 'running').length;
    document.getElementById('val-agents').textContent = `${active} / 22`;
  } catch (e) { /* offline */ }
}

async function fetchOpportunities() {
  try {
    const res  = await fetch(`${API_BASE}/api/opportunities/pipeline`);
    if (!res.ok) return;
    const data = await res.json();
    const p = data.pipeline;
    const total = data.total;
    document.getElementById('stage-pending').textContent   = p.pending.count;
    document.getElementById('stage-qualified').textContent = p.qualified.count;
    document.getElementById('stage-approved').textContent  = p.approved.count;
    document.getElementById('pipeline-count').textContent  = total;
    renderOpportunities(p.approved.items);
    updatePipelineBars(p.pending.count, p.qualified.count, p.approved.count);
    document.getElementById('val-opps').textContent = total;
    // Research discoveries
    renderResearchFeed(p.pending.items.slice(0, 5));
  } catch (e) { /* offline */ }
}

async function startCycle() {
  addLog('sys', 'Initiating research cycle...');
  document.getElementById('val-cycle').textContent = 'RUNNING';
  try {
    const res = await fetch(`${API_BASE}/api/system/cycle/start`, { method: 'POST' });
    if (res.ok) {
      addLog('sys', 'Cycle started — agents deploying');
      document.getElementById('val-cycle').textContent = 'ACTIVE';
    } else {
      addLog('error', 'Failed to start cycle');
      document.getElementById('val-cycle').textContent = 'ERROR';
    }
  } catch (e) {
    addLog('error', `Cycle start error: ${e.message}`);
    document.getElementById('val-cycle').textContent = 'OFFLINE';
  }
}

// ─── Render functions ──────────────────────────────────────────────
const DEPT_MAP = {
  executive: { label: 'EXECUTIVE', agents: ['SupremeAgent'] },
  research:  { label: 'RESEARCH',  agents: ['TrendResearchAgent','BusinessOpportunityAgent','MarketAnalysisAgent','CompetitorIntelligenceAgent','SocialMediaTrendAgent'] },
  strategy:  { label: 'STRATEGY',  agents: ['StrategicPlanningAgent','BusinessModelAgent','RiskAnalysisAgent','ValidationAgent'] },
  execution: { label: 'EXECUTION', agents: ['AutomationBuilderAgent','WebsiteBuilderAgent','MarketingAgent','SalesAgent','ContentAgent','OutreachAgent'] },
  finance:   { label: 'FINANCE',   agents: ['RevenueTrackingAgent','CostAnalysisAgent','ProfitOptimizationAgent'] },
  self_improvement: { label: 'SELF-IMPROVE', agents: ['KnowledgeManagementAgent','LearningAgent','PromptOptimizationAgent','WorkflowOptimizationAgent'] },
};

function renderAgentTree(agents) {
  const container = document.getElementById('agent-tree');
  const statusMap = {};
  agents.forEach(a => statusMap[a.name] = a.status || 'not_started');
  let html = '';
  for (const [dept, info] of Object.entries(DEPT_MAP)) {
    html += `<div class="agent-dept">
      <div class="agent-dept-label">${info.label}</div>`;
    for (const name of info.agents) {
      const status = statusMap[name] || 'not_started';
      const shortName = name.replace(/Agent$/, '').replace(/([A-Z])/g, ' $1').trim();
      html += `<div class="agent-item">
        <span class="agent-dot ${status}"></span>
        <span class="agent-name">${shortName}</span>
        <span class="agent-status-text">${status.toUpperCase()}</span>
      </div>`;
    }
    html += `</div>`;
  }
  container.innerHTML = html;
}

function renderDepts(depts) {
  const deptNames = { research:'research', strategy:'strategy', execution:'execution', finance:'finance', self_improvement:'improvement' };
  for (const [dept, info] of Object.entries(depts)) {
    const key = deptNames[dept];
    if (!key) continue;
    const bar    = document.getElementById(`fill-${key}`);
    const status = document.getElementById(`status-${key}`);
    const pct    = info.total ? Math.round((info.running / info.total) * 100) : 0;
    if (bar)    bar.style.width = `${pct}%`;
    if (status) {
      status.textContent = info.running > 0 ? `${info.running} ACTIVE` : 'STANDBY';
      status.className = `dept-status ${info.running > 0 ? 'active' : ''}`;
    }
  }
}

function renderOpportunities(opps) {
  const container = document.getElementById('top-opportunities');
  if (!opps || !opps.length) {
    container.innerHTML = '<div style="color:var(--text-dim);font-size:10px;padding:4px 0">No approved opportunities yet</div>';
    return;
  }
  container.innerHTML = opps.slice(0, 5).map(o => {
    const score = (o.overall_score || 0).toFixed(0);
    const gradeClass = score >= 80 ? 'grade-a' : score >= 65 ? 'grade-b' : score >= 50 ? 'grade-c' : 'grade-f';
    return `<div class="opp-item fade-in">
      <span class="opp-title" title="${o.title || o.name || '?'}">${o.title || o.name || 'Unknown'}</span>
      <span class="opp-score ${gradeClass}">${score}</span>
    </div>`;
  }).join('');
}

function renderResearchFeed(items) {
  const container = document.getElementById('research-feed');
  if (!items || !items.length) {
    container.innerHTML = '<div style="color:var(--text-dim);font-size:10px">No research data yet</div>';
    return;
  }
  container.innerHTML = items.map(i => `
    <div class="research-item fade-in">
      <div>
        <div class="research-name">${i.name || i.title || 'Unknown'}</div>
        <div class="research-meta">${i.income_potential || i.description?.slice(0,60) || ''}</div>
      </div>
      <span class="research-tag">${i.category || 'RESEARCH'}</span>
    </div>
  `).join('');
}

function updateObjectives(objectives) {
  const ul = document.getElementById('ceo-objectives');
  if (!objectives.length) return;
  ul.innerHTML = objectives.map(o => `<li>${o}</li>`).join('');
}

function updateKPIs(kpis) {
  if (kpis.total_revenue_usd !== undefined)
    animateValue('val-revenue', `$${(+kpis.total_revenue_usd || 0).toFixed(2)}`);
  if (kpis.agents_active !== undefined)
    animateValue('val-agents', `${kpis.agents_active} / 22`);
  if (kpis.opportunities_discovered !== undefined)
    animateValue('val-opps', kpis.opportunities_discovered);
}

function updateFinance(fin) {
  if (!fin) return;
  const rev  = (+fin.total_revenue_usd  || 0).toFixed(2);
  const cost = (+fin.total_costs_usd    || 0).toFixed(2);
  const prof = (+fin.net_profit_usd     || 0).toFixed(2);
  const roi  = (+fin.roi_pct            || 0).toFixed(1);

  animateValue('val-revenue', `$${rev}`);
  animateValue('val-profit',  `$${prof}`);

  // Finance stats panel
  const stats = document.getElementById('finance-stats');
  if (stats) {
    stats.innerHTML = `
      <div class="stat"><span class="stat-label">REVENUE</span><span class="stat-val">$${rev}</span></div>
      <div class="stat"><span class="stat-label">COSTS</span><span class="stat-val">$${cost}</span></div>
      <div class="stat"><span class="stat-label">PROFIT</span><span class="stat-val" style="color:${+prof>=0?'var(--green)':'var(--red)'}">$${prof}</span></div>
      <div class="stat"><span class="stat-label">ROI</span><span class="stat-val">${roi}%</span></div>
    `;
  }

  // Update chart
  const now = new Date().toLocaleTimeString();
  revHistory.labels.push(now);
  revHistory.revenue.push(+rev);
  revHistory.costs.push(+cost);
  if (revHistory.labels.length > 12) {
    revHistory.labels.shift(); revHistory.revenue.shift(); revHistory.costs.shift();
  }
  if (revenueChart) {
    revenueChart.data.labels = [...revHistory.labels];
    revenueChart.data.datasets[0].data = [...revHistory.revenue];
    revenueChart.data.datasets[1].data = [...revHistory.costs];
    revenueChart.update('none');
  }
}

function updatePipelineBars(pending, qualified, approved) {
  const total = Math.max(pending + qualified + approved, 1);
  const setBar = (id, count) => {
    const el = document.getElementById(id);
    if (el) el.style.width = `${Math.round((count / total) * 100)}%`;
  };
  setBar('bar-pending', pending);
  setBar('bar-qualified', qualified);
  setBar('bar-approved', approved);
}

// ─── Chart init ────────────────────────────────────────────────────
function initChart() {
  const ctx = document.getElementById('revenue-chart');
  if (!ctx) return;
  revenueChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Revenue',
          data: [],
          borderColor: '#00ff88',
          backgroundColor: 'rgba(0,255,136,0.08)',
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#00ff88',
        },
        {
          label: 'Costs',
          data: [],
          borderColor: '#ff3344',
          backgroundColor: 'rgba(255,51,68,0.05)',
          borderWidth: 1.5,
          tension: 0.4,
          pointRadius: 2,
          pointBackgroundColor: '#ff3344',
          borderDash: [4,4],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      plugins: {
        legend: {
          labels: { color: '#4a7090', font: { family: 'Share Tech Mono', size: 9 } },
        },
        tooltip: {
          backgroundColor: '#050f1a',
          borderColor: '#0a3a5a',
          borderWidth: 1,
          titleColor: '#00d4ff',
          bodyColor: '#c8e8ff',
          titleFont: { family: 'Share Tech Mono' },
          bodyFont:  { family: 'Share Tech Mono', size: 11 },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(10,58,90,0.3)' },
          ticks: { color: '#4a7090', font: { family: 'Share Tech Mono', size: 9 } },
        },
        y: {
          grid: { color: 'rgba(10,58,90,0.3)' },
          ticks: { color: '#4a7090', font: { family: 'Share Tech Mono', size: 9 }, callback: v => `$${v}` },
        },
      },
    },
  });
}

// ─── Log feed ──────────────────────────────────────────────────────
const LOG_CLASSES = {
  sys: 'sys', ceo: 'ceo', research: 'research',
  strategy: 'strategy', execution: 'execution',
  finance: 'finance', error: 'error',
};

function addLog(type, message) {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  const ts = new Date().toLocaleTimeString();
  const cls = LOG_CLASSES[type] || 'sys';
  const entry = document.createElement('div');
  entry.className = `log-entry ${cls} fade-in`;
  entry.innerHTML = `<span class="log-timestamp">[${ts}]</span>${message}`;
  feed.insertBefore(entry, feed.firstChild);
  // Keep max 100 entries
  while (feed.children.length > 100) feed.removeChild(feed.lastChild);
}

// ─── Helpers ───────────────────────────────────────────────────────
function animateValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('count-up');
  el.textContent = value;
  void el.offsetWidth;
  el.classList.add('count-up');
}
