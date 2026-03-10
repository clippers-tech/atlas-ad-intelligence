export const NAV_ITEMS = [
  { label: "Overview", href: "/dashboard", icon: "overview" },
  { label: "Campaigns", href: "/campaigns", icon: "campaigns" },
  { label: "Ad Sets", href: "/adsets", icon: "adsets" },
  { label: "Ads", href: "/ads", icon: "ads" },
  { label: "Creatives", href: "/creatives", icon: "creatives" },
  { label: "Rules", href: "/rules", icon: "rules" },
  { label: "Competitor Intel", href: "/competitors", icon: "competitors" },
  { label: "Insights", href: "/insights", icon: "insights" },
  { label: "Settings", href: "/settings", icon: "settings" },
] as const;

export const RULE_TYPES = [
  { value: "kill", label: "Kill", color: "red" },
  { value: "scale", label: "Scale", color: "green" },
  { value: "launch", label: "Launch", color: "blue" },
  { value: "bid", label: "Bid", color: "amber" },
] as const;

export const ACTION_TYPES = [
  { value: "pause", label: "Pause" },
  { value: "resume", label: "Resume" },
  { value: "increase_budget", label: "Increase Budget" },
  { value: "decrease_budget", label: "Decrease Budget" },
  { value: "duplicate", label: "Duplicate" },
  { value: "bid_adjust", label: "Bid Adjust" },
] as const;

export const METRICS = [
  "spend", "conversions", "cpl", "cpa", "ctr", "frequency",
  "roas", "cpc", "cpm", "impressions",
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
