CONTENT_AGENT_SYSTEM = """You are the Content Agent. You create high-quality, SEO-optimised content
that drives organic traffic and builds authority. You understand content marketing, copywriting,
and how to produce content that converts readers into customers."""

CONTENT_CREATION_PROMPT = """Create content for the following business opportunity.

OPPORTUNITY: {opportunity}
CONTENT TYPE: {content_type}
TARGET AUDIENCE: {audience}
PLATFORM: {platform}
GOAL: {goal}

Content types available:
- blog_post: Long-form SEO article (1500+ words)
- landing_page: Conversion-focused sales page
- email_sequence: 5-email welcome/nurture sequence
- social_post: Platform-specific social content (3 variations)
- video_script: YouTube/TikTok video script
- newsletter: Weekly newsletter edition
- product_description: E-commerce product listing

Produce complete, ready-to-publish content. Include:
- Headline variations (A/B test ready)
- Body content
- Call to action
- SEO keywords (if applicable)
- Estimated reading time

Return as JSON with content and metadata."""

MARKETING_STRATEGY_PROMPT = """Design a growth marketing strategy for this business.

OPPORTUNITY: {opportunity}
BUDGET: ${monthly_budget}/month
TARGET REVENUE: ${target_revenue}/month

Create a multi-channel marketing strategy:

1. SEO Strategy
   - Target keywords (head + long-tail)
   - Content calendar (12 weeks)
   - Link-building approach

2. Social Media Strategy
   - Platform selection rationale
   - Content types and posting frequency
   - Growth tactics

3. Paid Acquisition (if budget allows)
   - Platform(s) to test
   - Ad formats and creative direction
   - Expected CAC and ROAS

4. Partnership/Referral Strategy
   - Potential partners to approach
   - Affiliate program structure

5. Email Marketing
   - Lead magnet ideas
   - Automation sequence

Month 1 action items with specific tasks and owners.

Return as JSON."""

AUTOMATION_BLUEPRINT_PROMPT = """Design an automation system for this business process.

PROCESS: {process}
TOOLS AVAILABLE: {tools}
GOAL: {goal}

Create a detailed automation blueprint:
1. Process mapping (current vs. automated)
2. Tool/API integrations required
3. Data flows and transformations
4. Error handling and fallbacks
5. Monitoring and alerting
6. Time savings estimate
7. Implementation steps

Prefer: Python, Zapier/Make, n8n, or custom scripts.
Always include error handling and logging.

Return as JSON with automation_steps array."""

OUTREACH_PROMPT = """Create an outreach strategy and templates for this opportunity.

OPPORTUNITY: {opportunity}
TARGET: {target_audience}
GOAL: {goal}

Produce:
1. Outreach channel recommendations (email, LinkedIn, Twitter, cold call)
2. Ideal Customer Profile (ICP) definition
3. Personalised outreach templates (3 variations per channel)
4. Follow-up sequence (4 touch points)
5. Objection handling scripts
6. Tracking metrics to measure success

All outreach must be:
- Personalised and value-first
- Compliant with CAN-SPAM / GDPR
- NOT spam — genuine value exchange
- Professional and credible

Return as JSON with templates array."""
