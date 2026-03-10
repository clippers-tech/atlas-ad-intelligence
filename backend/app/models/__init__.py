"""Import all models so Alembic can detect them."""

from app.models.account import Account  # noqa: F401
from app.models.campaign import Campaign  # noqa: F401
from app.models.ad_set import AdSet  # noqa: F401
from app.models.ad import Ad  # noqa: F401
from app.models.ad_metric import AdMetric  # noqa: F401
from app.models.ad_placement_metric import AdPlacementMetric  # noqa: F401
from app.models.creative_metadata import CreativeMetadata  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.deal import Deal  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.rule import Rule  # noqa: F401
from app.models.action_log import ActionLog  # noqa: F401
from app.models.competitor_ad import CompetitorAd  # noqa: F401
from app.models.competitor_config import CompetitorConfig  # noqa: F401

from app.models.market_condition import MarketCondition  # noqa: F401
from app.models.seasonality_config import SeasonalityConfig  # noqa: F401
from app.models.audience_test_queue import AudienceTestQueue  # noqa: F401
from app.models.landing_page_event import LandingPageEvent  # noqa: F401
from app.models.health_check_log import HealthCheckLog  # noqa: F401
