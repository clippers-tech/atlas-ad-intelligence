// Core entity types — accounts, campaigns, ads, metrics

export interface Account {
  id: string;
  name: string;
  slug: string;
  meta_ad_account_id: string;
  business_type: "web3" | "clippers" | "agency";
  target_cpl: number | null;
  target_cpa: number | null;
  target_roas: number | null;
  timezone: string;
  currency: string;
  telegram_chat_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  account_id: string;
  meta_campaign_id: string;
  name: string;
  objective: string | null;
  status: string;
  daily_budget: number | null;
  lifetime_budget: number | null;
  // Aggregated from ad_metrics
  spend?: number;
  impressions?: number;
  reach?: number;
  link_clicks?: number;
  clicks_all?: number;
  landing_page_views?: number;
  outbound_clicks?: number;
  conversions?: number;
  leads?: number;
  cpm?: number;
  cpc_link?: number;
  cpc_all?: number;
  ctr_link?: number;
  ctr_all?: number;
  cost_per_lpv?: number;
  cpl?: number;
  frequency?: number;
  roas?: number;
}

export interface Ad {
  id: string;
  account_id: string;
  ad_set_id: string;
  meta_ad_id: string;
  name: string;
  creative_url: string | null;
  thumbnail_url: string | null;
  ad_type: string;
  review_status: string;
  status: string;
  first_active_date: string | null;
  adset_name?: string;
  spend?: number;
  impressions?: number;
  reach?: number;
  link_clicks?: number;
  conversions?: number;
  leads?: number;
  cpm?: number;
  cpc_link?: number;
  ctr_link?: number;
  cpl?: number;
}

export interface AdMetric {
  id: string;
  ad_id: string;
  timestamp: string;
  spend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpc: number;
  cpm: number;
  conversions: number;
  cpl: number;
  cpa: number;
  frequency: number;
  video_view_3s_rate: number;
  video_p50: number;
  video_p75: number;
  video_p100: number;
  reach: number;
  unique_clicks: number;
}

export interface DashboardOverview {
  total_spend: number;
  total_impressions: number;
  total_reach: number;
  total_link_clicks: number;
  total_clicks_all: number;
  total_landing_page_views: number;
  total_conversions: number;
  total_leads: number;
  effective_leads: number;
  avg_cpl: number;
  avg_cpm: number;
  avg_cpc_link: number;
  ctr_link: number;
  total_bookings: number;
  total_revenue: number;
  true_roas: number;
  active_ads_count: number;
  paused_today_count: number;
  campaigns: CampaignRow[];
}

export interface CampaignRow {
  campaign_id: string;
  id?: string;
  name: string;
  status: string;
  spend: number;
  impressions: number;
  link_clicks: number;
  clicks_all: number;
  landing_page_views: number;
  leads: number;
  cpl: number;
  cpm: number;
  ctr_link: number;
  cpc_link: number;
  bookings: number;
  revenue: number;
  roas: number;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface Lead {
  id: string;
  account_id: string;
  email: string | null;
  name: string | null;
  phone: string | null;
  source_campaign_id: string | null;
  source_campaign_name?: string;
  source_ad_id: string | null;
  source_ad_name?: string;
  utm_campaign: string | null;
  stage: string;
  revenue: number | null;
  booked_at: string | null;
  created_at: string;
}

export interface LeadJourney {
  lead: Lead;
  events: JourneyEvent[];
  attribution: LeadAttribution;
}

export interface JourneyEvent {
  type: string;
  timestamp: string;
  description: string;
  details?: string;
}

export interface LeadAttribution {
  campaign_name: string | null;
  ad_set_name: string | null;
  ad_name: string | null;
  utm_campaign: string | null;
  utm_source: string | null;
  utm_medium: string | null;
  cost_to_acquire: number | null;
  revenue: number | null;
  individual_roas: number | null;
}

export interface Deal {
  id: string;
  lead_id: string;
  account_id: string;
  stage: string;
  revenue: number | null;
  proposal_sent_at: string | null;
  closed_at: string | null;
  notes: string | null;
}

export interface Rule {
  id: string;
  account_id: string;
  name: string;
  description: string | null;
  type: "kill" | "scale" | "launch" | "bid";
  condition_json: RuleCondition;
  action_json: RuleAction;
  is_enabled: boolean;
  priority: number;
  cooldown_minutes: number;
  budget_limit: number | null;
  budget_spent: number;
  trigger_count?: number;
  estimated_savings?: number;
  last_triggered?: string;
}

export interface RuleCondition {
  metric: string;
  operator: string;
  value: number;
  and?: RuleCondition[];
  or?: RuleCondition[];
}

export interface RuleAction {
  action: string;
  percent?: number;
}

// Re-export extended types
export type {
  ActionLogEntry, Anomaly, CreativePerformance, PlacementBreakdown,
  AudiencePerformance, FunnelData, FunnelStage, ConversionRate,
  Insight, Competitor, CompetitorAd,
  PaginatedResponse, HealthStatus, TaskHealth,
} from "./types-extended";
