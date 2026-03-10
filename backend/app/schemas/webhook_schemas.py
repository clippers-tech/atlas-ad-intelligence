from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LandingPageEventPayload(BaseModel):
    account_slug: str
    page_url: str
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    scroll_depth_percent: Optional[float] = None
    time_on_page_seconds: Optional[int] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
