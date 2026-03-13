"""Master router — includes all ATLAS API sub-routers."""

from fastapi import APIRouter

from app.api.health_api import router as health_router
from app.api.accounts_api import router as accounts_router
from app.api.leads_api import router as leads_router
from app.api.deals_api import router as deals_router
from app.api.rules_api import router as rules_router
from app.api.competitors_api import router as competitors_router
from app.api.competitor_fetch_api import router as competitor_fetch_router
from app.api.reports_api import router as reports_router
from app.api.tracking_api import router as tracking_router
from app.api.dashboard.overview import router as dashboard_overview_router
from app.api.dashboard.action_log_view import router as dashboard_actions_router
from app.api.dashboard.creative_leaderboard import router as dashboard_creatives_router
from app.api.dashboard.audience_heatmap import router as dashboard_audiences_router
from app.api.dashboard.funnel import router as dashboard_funnel_router
from app.api.dashboard.anomaly_timeline import router as dashboard_anomalies_router
from app.api.webhooks.landing_page_webhook import router as landing_page_router
from app.api.webhooks.meta_leadgen_webhook import router as meta_leadgen_router
from app.api.campaigns_api import router as campaigns_router
from app.api.adsets_api import router as adsets_router
from app.api.ads_api import router as ads_router
from app.api.insights_api import router as insights_router
from app.api.insights_trigger_api import router as insights_trigger_router
from app.api.creatives_api import router as creatives_router
from app.api.schedules_api import router as schedules_router
from app.api.sync_api import router as sync_router
from app.api.actions_api import router as actions_router

master_router = APIRouter()

master_router.include_router(health_router, tags=["Health"])
master_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
master_router.include_router(leads_router, prefix="/leads", tags=["Leads"])
master_router.include_router(deals_router, prefix="/deals", tags=["Deals"])
master_router.include_router(rules_router, prefix="/rules", tags=["Rules"])
master_router.include_router(competitors_router, prefix="/competitors", tags=["Competitors"])
master_router.include_router(competitor_fetch_router, prefix="/competitors", tags=["Competitors"])
master_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
master_router.include_router(tracking_router, prefix="/tracking", tags=["Tracking"])
master_router.include_router(dashboard_overview_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(dashboard_actions_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(dashboard_creatives_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(dashboard_audiences_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(dashboard_funnel_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(dashboard_anomalies_router, prefix="/dashboard", tags=["Dashboard"])
master_router.include_router(landing_page_router, prefix="/webhooks", tags=["Webhooks"])
master_router.include_router(meta_leadgen_router, prefix="/webhooks", tags=["Webhooks"])
master_router.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
master_router.include_router(adsets_router, prefix="/ad-sets", tags=["Ad Sets"])
master_router.include_router(ads_router, prefix="/ads", tags=["Ads"])
master_router.include_router(insights_router, prefix="/insights", tags=["Insights"])
master_router.include_router(insights_trigger_router, prefix="/insights", tags=["Insights"])
master_router.include_router(creatives_router, prefix="/creatives", tags=["Creatives"])
master_router.include_router(schedules_router, prefix="/schedules", tags=["Schedules"])
master_router.include_router(sync_router, tags=["Sync"])
master_router.include_router(actions_router, prefix="/actions", tags=["Actions"])
