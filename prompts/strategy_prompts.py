STRATEGIC_PLANNING_SYSTEM = """You are the Strategic Planning Agent. You transform research findings
into concrete, executable business plans. You are pragmatic, data-driven, and focused on
generating real revenue as quickly as possible with minimal capital at risk."""

OPPORTUNITY_SCORING_PROMPT = """Score this business opportunity across multiple dimensions.

OPPORTUNITY:
Title: {title}
Description: {description}
Category: {category}
Market Data: {market_data}

Score each dimension 0-100:
- profit_potential: How much monthly revenue can this realistically generate?
- difficulty: How hard is it to execute? (0=very hard, 100=very easy)
- startup_cost: How cheap to start? (0=very expensive, 100=completely free)
- time_required: How quickly can we launch and see revenue? (0=months, 100=days)
- automation_potential: Can this run with minimal human input? (0=manual, 100=fully automated)
- scalability: Can revenue grow 10x without proportional cost growth?
- risk_level: How risky? (0=very risky, 100=very safe)

Also provide:
- estimated_monthly_revenue_usd: Realistic monthly revenue in 6 months
- estimated_startup_cost_usd: One-time startup investment needed
- time_to_first_revenue_days: Days until first dollar earned
- overall_score: Weighted composite score
- recommendation: approve|reject|needs_more_research
- reasoning: 2-3 sentence justification

Return as JSON."""

EXECUTION_PLAN_PROMPT = """Create a detailed execution plan for this approved opportunity.

OPPORTUNITY: {opportunity}
BUDGET: ${budget}
TIMELINE: {timeline_weeks} weeks

Produce a week-by-week execution plan including:
- Week 1-2: Foundation tasks (setup, research, tooling)
- Week 3-4: Build phase (create the core product/service/content)
- Week 5-6: Launch phase (go live, initial marketing)
- Week 7+: Growth phase (scale what works)

For each task specify:
- Task name
- Department responsible (research/strategy/execution/finance)
- Estimated hours
- Tools/resources needed
- Expected output
- Success metric

Return as JSON with phases array."""

BUSINESS_MODEL_PROMPT = """Design the optimal business model for this opportunity.

OPPORTUNITY: {opportunity}
TARGET MARKET: {market}

Evaluate and recommend:
1. Revenue model (subscription/one-time/freemium/ads/affiliate/services)
2. Pricing strategy with specific price points
3. Customer acquisition channels (organic, paid, partnerships)
4. Unit economics (CAC, LTV, margins)
5. Key partnerships needed
6. Technology stack required
7. Minimal viable product definition
8. Path to $1k/month, $10k/month, $100k/month

Return as JSON with all sections."""

RISK_ANALYSIS_PROMPT = """Perform a thorough risk analysis for this business opportunity.

OPPORTUNITY: {opportunity}
EXECUTION PLAN: {plan}

Identify and score all risks:
- Market risks (demand disappears, saturation)
- Technical risks (tools don't work, platform bans)
- Financial risks (costs exceed projections)
- Competitive risks (large player enters market)
- Legal/compliance risks
- Operational risks (key dependency fails)

For each risk:
- Name
- Probability (low/medium/high)
- Impact (low/medium/high)
- Risk score (1-10)
- Mitigation strategy
- Contingency plan

Overall risk rating: low/medium/high
Go/no-go recommendation with reasoning.

Return as JSON."""
