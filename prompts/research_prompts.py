TREND_RESEARCH_SYSTEM = """You are the Trend Research Agent. Your job is to discover emerging trends
that represent genuine income opportunities. Focus on: AI tools, SaaS, digital products,
content niches, automation services, lead generation, e-commerce, and market gaps.

Always return structured, actionable findings backed by observable market data."""

TREND_RESEARCH_PROMPT = """Analyse current internet and business trends to identify emerging income opportunities.

Search focus areas:
- AI and automation tools demand
- Growing content niches (YouTube, TikTok, newsletters)
- Underserved B2B software needs
- Digital product opportunities
- Freelance/agency service gaps

For each trend found, provide:
- Trend name and description
- Evidence/signals observed
- Estimated market size
- Income potential
- Time window (how long this opportunity will remain relevant)
- Recommended entry strategy

Return as JSON with a "trends" array."""

MARKET_ANALYSIS_PROMPT = """Conduct a market analysis for the following niche/opportunity:

OPPORTUNITY: {opportunity}

Analyse:
1. Total Addressable Market (TAM) size
2. Current competitors and their weaknesses
3. Customer pain points and willingness to pay
4. Best monetisation models (subscription, one-time, freemium, etc.)
5. Distribution channels that work in this market
6. Barriers to entry (good or bad)
7. Growth trajectory (is this market growing?)

Return structured JSON with all fields."""

COMPETITOR_INTELLIGENCE_PROMPT = """Research competitors for this business opportunity:

OPPORTUNITY: {opportunity}
CATEGORY: {category}

For each competitor found:
- Company name and URL
- Revenue estimate / size
- Key strengths
- Clear weaknesses / gaps
- Customer complaints (from reviews)
- Pricing strategy
- What they're missing that we could provide

Identify the biggest gap in the market we can exploit legally and ethically.

Return as JSON with a "competitors" array and "market_gap" field."""

SOCIAL_MEDIA_TREND_PROMPT = """Analyse social media platforms for trending income opportunities.

Platforms to monitor: YouTube, TikTok, Twitter/X, Reddit, LinkedIn, Instagram

Look for:
- Viral content categories with monetisation potential
- Emerging creator niches with growing audiences
- Products/services that are selling on social commerce
- Pain points people are complaining about (potential SaaS/service opportunities)
- Affiliate marketing opportunities gaining traction
- Newsletter/community niches with engaged audiences

Return JSON with trending_opportunities array, each including platform, trend, opportunity, and score."""
