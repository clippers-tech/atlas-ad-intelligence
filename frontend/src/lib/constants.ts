export const NAV_ITEMS = [
  { label: "Overview", href: "/dashboard", icon: "overview" },
  { label: "Campaigns", href: "/campaigns", icon: "campaigns" },
  { label: "Ad Sets", href: "/adsets", icon: "adsets" },
  { label: "Ads", href: "/ads", icon: "ads" },
  { label: "Rules", href: "/rules", icon: "rules" },
  { label: "Competitor Intel", href: "/competitors", icon: "competitors" },
  { label: "Insights", href: "/insights", icon: "insights" },
  { label: "Computer", href: "/schedules", icon: "computer" },
  { label: "Settings", href: "/settings", icon: "settings" },
] as const;

export const RULE_TYPES = [
  { value: "kill", label: "Kill", color: "red" },
  { value: "scale", label: "Scale", color: "green" },
  { value: "alert", label: "Alert", color: "amber" },
] as const;

export const ACTION_TYPES = [
  { value: "pause", label: "Pause", icon: "⏸" },
  { value: "resume", label: "Resume", icon: "▶" },
  { value: "increase_budget", label: "Increase Budget", icon: "📈" },
  { value: "decrease_budget", label: "Decrease Budget", icon: "📉" },
  { value: "notify", label: "Notify / Alert", icon: "🔔" },
] as const;

export const METRICS = [
  "spend", "conversions", "cpl", "cpa", "ctr_link", "ctr_all",
  "frequency", "roas", "cpc_link", "cpc_all", "cpm",
  "impressions", "reach", "link_clicks", "clicks_all",
  "landing_page_views", "video_view_3s_rate",
] as const;

export const OPERATORS = [">", "<", ">=", "<=", "=="] as const;

export const DATE_RANGES = [
  { label: "Today", value: "1d" },
  { label: "7d", value: "7d" },
  { label: "14d", value: "14d" },
  { label: "30d", value: "30d" },
  { label: "All", value: "all" },
] as const;

export const CAMPAIGN_STATUSES = [
  { value: "ACTIVE", label: "Active", color: "success" },
  { value: "PAUSED", label: "Paused", color: "warning" },
  { value: "DELETED", label: "Deleted", color: "danger" },
  { value: "ARCHIVED", label: "Archived", color: "muted" },
] as const;
