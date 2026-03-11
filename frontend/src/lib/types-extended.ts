// Extended types — actions, anomalies, creatives, audiences, funnel, insights, competitors

export interface ActionLogEntry {
  id: string;
  account_id: string;
  ad_id: string | null;
  ad_name?: string;
  rule_id: string | null;
  rule_name?: string;
  action_type: string;
  details_json: Record<string, unknown> | null;
  is_reversible: boolean;
  reversed_at: string | null;
  triggered_by: string;
  created_at: string;
}

export interface Anomaly {
  id: string;
  metric: string;
  current_value: number;
  avg_value: number;
  deviation_percent: number;
  severity: "low" | "medium" | "high";
  timestamp: string;
  ad_name?: string;
  campaign_name?: string;
}

export interface CreativePerformance {
  id: string;
  ad_id: string;
  ad_name: string;
  ad_type?: string;
  thumbnail_url: string | null;
  status: string;
  spend: number;
  impressions: number;
  ctr: number;
  cpl: number;
  conversions: number;
  video_view_3s_rate: number;
  video_p50: number;
  video_p75: number;
  fatigue_level: string;
  age_days: number;
  hook_type: string | null;
  cta_type: string | null;
  placements: PlacementBreakdown[];
}

export interface PlacementBreakdown {
  placement: string;
  spend: number;
  ctr: number;
  cpl: number;
  conversions: number;
}

export interface AudiencePerformance {
  id: string;
  name: string;
  audience_type: string;
  spend: number;
  leads: number;
  cpl: number;
  frequency: number;
  close_rate: number;
  quality_score: "high" | "medium" | "low";
}

export interface FunnelData {
  stages: FunnelStage[];
  conversion_rates: ConversionRate[];
  total_revenue: number;
  total_spend: number;
  true_roas: number;
}

export interface FunnelStage {
  name: string;
  count: number;
  percent_of_top: number;
}

export interface ConversionRate {
  from_stage: string;
  to_stage: string;
  rate: number;
}

export interface Insight {
  id: string;
  account_id: string | null;
  type: string;
  title?: string;
  summary?: string;
  recommendation?: string;
  priority?: string;
  response_text: string | null;
  recommendations_json: string | null;
  source: string | null; // "computer_schedule" | "manual"
  created_at: string;
}

export interface Competitor {
  id: string;
  account_id: string;
  competitor_name: string;
  meta_page_id: string | null;
  website_url: string | null;
  // Apify scraper config
  facebook_url: string | null;
  scraper_country: string;
  scraper_media_type: string;
  scraper_platforms: string;
  scraper_language: string;

  is_active: boolean;
  total_ads: number;
  ads: CompetitorAd[];
  created_at: string;
  updated_at: string;
}

export interface CompetitorAd {
  id: string;
  competitor_config_id: string;
  creative_url: string | null;
  ad_text: string | null;
  hook_text: string | null;
  estimated_spend_range: string | null;
  impression_range: string | null;
  hook_type: string | null;
  cta_type: string | null;
  offer_text: string | null;
  first_seen: string | null;
  last_seen: string | null;
  is_active: boolean;
  ai_analysis_json: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: { total: number; page: number; per_page: number };
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "critical";
  db_connected: boolean;
  last_meta_pull: string | null;
  last_rule_run: string | null;
  tasks: TaskHealth[];
}

export interface TaskHealth {
  name: string;
  last_run: string | null;
  status: string;
}
