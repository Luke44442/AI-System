LEARNING_AGENT_SYSTEM = """You are the Learning Agent. You analyse outcomes across all agent
activities and extract reusable lessons, patterns, and improvements. You turn failures into
wisdom and successes into repeatable playbooks."""

LESSON_EXTRACTION_PROMPT = """Analyse the following agent activity logs and extract key lessons.

ACTIVITY DATA:
{activity_data}

OUTCOMES:
{outcomes}

Extract:
1. Success patterns (what worked and why)
2. Failure patterns (what failed and why)
3. Actionable lessons (specific rule changes)
4. Prompt improvements (if any agent prompts caused issues)
5. Workflow improvements (process bottlenecks identified)
6. Opportunity patterns (what types score/perform best)

Each lesson should have:
- Category (success/failure/improvement)
- Lesson title
- Description
- Recommended action
- Confidence (1-10)
- Priority (1-10)

Return as JSON with lessons array."""

PROMPT_OPTIMIZATION_PROMPT = """Optimise the following agent prompt based on performance data.

CURRENT PROMPT:
{current_prompt}

AGENT: {agent_name}
PERFORMANCE ISSUES: {issues}
SUCCESSFUL OUTPUTS SAMPLE: {good_outputs}
FAILED OUTPUTS SAMPLE: {bad_outputs}

Produce an improved prompt that:
1. Addresses the identified failure modes
2. Maintains the strengths from successful outputs
3. Adds clearer instructions for edge cases
4. Improves output consistency and quality
5. Reduces token usage while maintaining quality

Provide:
- Revised prompt (complete replacement)
- Change summary (what was modified and why)
- Expected improvement

Return as JSON."""

WORKFLOW_OPTIMIZATION_PROMPT = """Analyse the current workflow and identify optimisations.

WORKFLOW: {workflow_name}
METRICS:
- Average completion time: {avg_time}
- Success rate: {success_rate}%
- Common failure points: {failures}
- Agent utilisation: {utilisation}

Recommend:
1. Bottleneck elimination
2. Parallelisation opportunities
3. Caching/memoisation points
4. Agent task redistribution
5. New automation to add
6. Steps that can be removed entirely

Quantify expected improvement for each recommendation.

Return as JSON with recommendations array."""

KNOWLEDGE_SYNTHESIS_PROMPT = """Synthesise the accumulated knowledge base into strategic insights.

KNOWLEDGE ENTRIES: {knowledge_count}
TOP LESSONS: {top_lessons}
CURRENT OBJECTIVES: {objectives}
PERFORMANCE TRENDS: {trends}

Produce:
1. Top 5 strategic insights derived from accumulated learning
2. Recommended changes to global strategy
3. New hypotheses to test
4. Patterns that predict success
5. Anti-patterns to avoid

These insights will directly influence CEO decision-making.

Return as JSON with insights array."""
