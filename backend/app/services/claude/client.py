"""Claude API wrapper — async httpx client with circuit breaker protection."""

import logging
from typing import Any

import httpx

from app.config import settings
from app.utils.circuit_breaker import claude_circuit, CircuitOpenError

logger = logging.getLogger(__name__)

_ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_REQUEST_TIMEOUT = 60.0

# Cost per million tokens (USD) — claude-sonnet-4 pricing
_COST_PER_M_INPUT = 3.0
_COST_PER_M_OUTPUT = 15.0


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost from token counts."""
    return (input_tokens / 1_000_000 * _COST_PER_M_INPUT) + (
        output_tokens / 1_000_000 * _COST_PER_M_OUTPUT
    )


async def _do_call(
    prompt: str,
    system_prompt: str,
    model: str,
) -> dict[str, Any]:
    """Raw httpx call to Anthropic Messages API (no circuit breaker logic here)."""
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        response = await client.post(_ANTHROPIC_MESSAGES_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content_blocks = data.get("content", [])
    text = " ".join(
        block.get("text", "") for block in content_blocks if block.get("type") == "text"
    ).strip()

    usage = data.get("usage", {})
    input_tokens: int = usage.get("input_tokens", 0)
    output_tokens: int = usage.get("output_tokens", 0)
    total_tokens = input_tokens + output_tokens

    cost = _estimate_cost(input_tokens, output_tokens)
    model_used: str = data.get("model", model)

    logger.info(
        "claude_client: call completed — model=%s tokens=%d cost=$%.4f",
        model_used,
        total_tokens,
        cost,
    )

    return {
        "response": text,
        "tokens_used": total_tokens,
        "model": model_used,
        "cost_usd": cost,
    }


async def call_claude(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
) -> dict[str, Any]:
    """Call Anthropic's Messages API with circuit breaker protection.

    Args:
        prompt: User message content.
        system_prompt: Optional system instructions for Claude.
        model: Override the default model from settings.

    Returns:
        Dict with keys: response, tokens_used, model, cost_usd.
        On error returns: response="", tokens_used=0, model=<model>, cost_usd=0.0, error=<msg>.
    """
    resolved_model = model or settings.claude_model

    if not settings.anthropic_api_key:
        logger.error("claude_client: anthropic_api_key not configured")
        return {
            "response": "",
            "tokens_used": 0,
            "model": resolved_model,
            "cost_usd": 0.0,
            "error": "anthropic_api_key not configured",
        }

    try:
        result: dict[str, Any] = await claude_circuit.call(
            _do_call, prompt, system_prompt, resolved_model
        )
        return result
    except CircuitOpenError as exc:
        logger.error("claude_client: circuit breaker OPEN — %s", exc)
        return {
            "response": "",
            "tokens_used": 0,
            "model": resolved_model,
            "cost_usd": 0.0,
            "error": str(exc),
        }
    except httpx.HTTPStatusError as exc:
        logger.error(
            "claude_client: HTTP error %d — %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
        return {
            "response": "",
            "tokens_used": 0,
            "model": resolved_model,
            "cost_usd": 0.0,
            "error": f"HTTP {exc.response.status_code}",
        }
    except Exception as exc:
        logger.exception("claude_client: unexpected error — %s", exc)
        return {
            "response": "",
            "tokens_used": 0,
            "model": resolved_model,
            "cost_usd": 0.0,
            "error": str(exc),
        }
