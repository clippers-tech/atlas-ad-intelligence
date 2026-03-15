"""Claude AI Analyzer — generates insights using Anthropic API.

Uses Claude Sonnet 4.6 to analyze ad performance data and produce
structured insights with titles, summaries, recommendations,
and priority levels.
"""

import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.insight import Insight
from app.services.insights.data_collector import (
    collect_account_data,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are ATLAS, an expert AI ad intelligence analyst for digital marketing agencies.
You analyze Meta (Facebook/Instagram) ad performance data and provide actionable insights.

Your analysis covers:
- Campaign performance trends and anomalies
- Budget optimization opportunities
- Creative fatigue detection
- Audience saturation signals
- Competitor activity patterns
- Lead pipeline health

IMPORTANT: Respond ONLY with a valid JSON array of insight objects. Each object must have:
{
  "type": "performance" | "creative" | "budget" | "audience" | "competitor" | "anomaly",
  "title": "Short descriptive title (max 100 chars)",
  "summary": "Detailed analysis paragraph (2-4 sentences)",
  "recommendation": "Specific actionable recommendation",
  "priority": "critical" | "high" | "medium" | "low"
}

Generate 3-8 insights per analysis. Focus on the most impactful findings.
Be specific with numbers and percentages. Reference actual campaign names.
If data is limited, note that and provide what insights you can."""


def _build_analysis_prompt(data: dict) -> str:
    """Build the analysis prompt from collected data."""
    account = data.get("account", {})
    metrics = data.get("metrics_summary", {})
    campaigns = data.get("campaigns", [])
    leads = data.get("lead_pipeline", {})
    actions = data.get("rule_actions", {})
    competitors = data.get("competitors", [])
    period = data.get("data_period", {})

    prompt_parts = [
        f"## Account: {account.get('name', 'Unknown')}",
        f"Business Type: {account.get('business_type', 'N/A')}",
        f"Currency: {account.get('currency', 'GBP')}",
        f"Target CPL: {account.get('target_cpl', 'N/A')}",
        f"Target ROAS: {account.get('target_roas', 'N/A')}",
        "",
        "## Performance Summary (Last 7 Days)",
        f"- Total Spend: {metrics.get('total_spend', 0)}",
        f"- Total Conversions: {metrics.get('total_conversions', 0)}",
        f"- Total Clicks: {metrics.get('total_clicks', 0)}",
        f"- Avg CPL: {metrics.get('avg_cpl', 0)}",
        f"- Avg CTR: {metrics.get('avg_ctr', 0)}%",
        "",
        "## Campaign Breakdown",
    ]

    for camp in campaigns[:15]:
        prompt_parts.append(
            f"- {camp['name']} ({camp['status']}): "
            f"Spend={camp['spend']}, "
            f"Conversions={camp['conversions']}, "
            f"CTR={camp['ctr']}%, "
            f"CPL={camp['cpl']}"
        )

    if leads:
        prompt_parts.extend(["", "## Lead Pipeline"])
        for stage, count in leads.items():
            prompt_parts.append(f"- {stage}: {count}")

    if actions:
        prompt_parts.extend(["", "## Rule Actions (Last 7 Days)"])
        for action_type, count in actions.items():
            prompt_parts.append(f"- {action_type}: {count}")

    if competitors:
        prompt_parts.extend(["", "## Competitor Activity"])
        for comp in competitors:
            prompt_parts.append(
                f"- {comp['name']}: "
                f"{comp['active_ads']} active ads"
            )

    prompt_parts.extend([
        "",
        f"Analysis period: {period.get('from', '')} to "
        f"{period.get('to', '')}",
        "",
        "Analyze this data and provide insights as a JSON array.",
    ])

    return "\n".join(prompt_parts)


async def _call_claude(prompt: str) -> list[dict]:
    """Call the Anthropic API and parse response."""
    api_key = settings.anthropic_api_key
    if not api_key:
        logger.warning(
            "claude: ANTHROPIC_API_KEY not set — skipping"
        )
        return []

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text content from response
        response_text = ""
        for block in message.content:
            if hasattr(block, "text"):
                response_text += block.text

        # Parse JSON from response
        # Handle potential markdown code blocks
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        insights = json.loads(text)
        if not isinstance(insights, list):
            insights = [insights]

        logger.info(
            "claude: received %d insights from API",
            len(insights),
        )
        return insights

    except json.JSONDecodeError as exc:
        logger.error(
            "claude: failed to parse response JSON — %s", exc
        )
        return []
    except Exception as exc:
        logger.error("claude: API call failed — %s", exc)
        raise


async def generate_insights_for_account(
    db: AsyncSession, account_id: UUID
) -> dict:
    """Generate Claude-powered insights for a single account.

    1. Collect account data
    2. Build prompt
    3. Call Claude API
    4. Store insights in DB

    Returns:
        Dict with insights_created count
    """
    logger.info(
        "claude: generating insights for account %s",
        account_id,
    )

    # Collect data
    data = await collect_account_data(db, account_id)
    if "error" in data:
        logger.error(
            "claude: data collection failed — %s",
            data["error"],
        )
        return {"insights_created": 0, "error": data["error"]}

    # Build prompt and call Claude
    prompt = _build_analysis_prompt(data)
    raw_insights = await _call_claude(prompt)

    if not raw_insights:
        logger.info(
            "claude: no insights returned for account %s",
            account_id,
        )
        return {"insights_created": 0}

    # Store insights in DB
    created = 0
    for item in raw_insights:
        try:
            insight = Insight(
                account_id=account_id,
                type=item.get("type", "general"),
                title=item.get("title", "Untitled Insight"),
                summary=item.get("summary", ""),
                recommendation=item.get("recommendation"),
                priority=item.get("priority", "medium"),
                source="claude",
            )
            db.add(insight)
            created += 1
        except Exception as exc:
            logger.error(
                "claude: failed to store insight — %s", exc
            )

    if created > 0:
        await db.flush()

    logger.info(
        "claude: created %d insights for account %s",
        created,
        account_id,
    )
    return {"insights_created": created}
