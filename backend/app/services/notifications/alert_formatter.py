"""Alert formatting functions — returns HTML strings for Telegram messages."""

from typing import Any


def _html_escape(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_details(details: Any) -> str:
    """Render a details value as indented HTML lines."""
    if isinstance(details, dict):
        lines = []
        for key, val in details.items():
            lines.append(f"  <b>{_html_escape(key)}:</b> {_html_escape(val)}")
        return "\n".join(lines)
    if isinstance(details, list):
        return "\n".join(f"  • {_html_escape(str(item))}" for item in details)
    return _html_escape(str(details))


def format_urgent_alert(title: str, details: Any = "") -> str:
    """🚨 Urgent alert — used for critical failures requiring immediate action."""
    return (
        f"🚨 <b>URGENT: {_html_escape(title)}</b>\n"
        f"{_format_details(details)}"
    )


def format_warning_alert(title: str, details: Any = "") -> str:
    """⚠️ Warning alert — something needs attention soon."""
    return (
        f"⚠️ <b>WARNING: {_html_escape(title)}</b>\n"
        f"{_format_details(details)}"
    )


def format_win_alert(title: str, details: Any = "") -> str:
    """✅ Win alert — positive outcome, conversion, or goal achieved."""
    return (
        f"✅ <b>{_html_escape(title)}</b>\n"
        f"{_format_details(details)}"
    )


def format_daily_digest(data: dict) -> str:
    """📊 Daily digest — structured summary of key metrics."""
    account = _html_escape(data.get("account_name", "All Accounts"))
    date = _html_escape(data.get("date", "Today"))

    spend = data.get("spend", 0)
    impressions = data.get("impressions", 0)
    clicks = data.get("clicks", 0)
    ctr = data.get("ctr", 0)
    leads = data.get("leads", 0)
    cpl = data.get("cpl", 0)

    lines = [
        f"📊 <b>Daily Digest — {account} ({date})</b>",
        "",
        f"  💰 Spend: <b>£{spend:,.2f}</b>",
        f"  👁 Impressions: <b>{impressions:,}</b>",
        f"  🖱 Clicks: <b>{clicks:,}</b>  (CTR: {ctr:.2f}%)",
        f"  🎯 Leads: <b>{leads}</b>  (CPL: £{cpl:,.2f})",
    ]

    if "top_ads" in data:
        lines.append("\n  <b>Top Ads:</b>")
        for ad in data["top_ads"][:3]:
            lines.append(f"    • {_html_escape(ad.get('name', 'Unknown'))} — CPL £{ad.get('cpl', 0):.2f}")

    if "alerts" in data and data["alerts"]:
        lines.append("\n  <b>Alerts:</b>")
        for alert in data["alerts"]:
            lines.append(f"    ⚠️ {_html_escape(str(alert))}")

    return "\n".join(lines)


def format_system_alert(title: str, details: Any = "") -> str:
    """🔧 System alert — infrastructure, task failures, service issues."""
    return (
        f"🔧 <b>SYSTEM: {_html_escape(title)}</b>\n"
        f"{_format_details(details)}"
    )
