export const DEAL_STAGES = [
  { value: "new", label: "New", emoji: "🆕" },
  { value: "qualified", label: "Qualified", emoji: "✅" },
  { value: "call_completed", label: "Call Completed", emoji: "📞" },
  { value: "proposal_sent", label: "Proposal Sent", emoji: "📋" },
  { value: "negotiation", label: "Negotiation", emoji: "🤝" },
  { value: "closed_won", label: "Closed Won", emoji: "💰" },
  { value: "closed_lost", label: "Closed Lost", emoji: "❌" },
] as const;

export const RULE_TYPES = [
  { value: "kill", label: "Kill", color: "red" },
  { value: "scale", label: "Scale", color: "green" },
  { value: "launch", label: "Launch", color: "blue" },
  { value: "bid", label: "Bid", color: "amber" },
] as const;

export const ACTION_TYPES = [
  { value: "pause", label: "Pause", icon: "⏸️" },
  { value: "resume", label: "Resume", icon: "▶️" },
  { value: "increase_budget", label: "Increase Budget", icon: "📈" },
  { value: "decrease_budget", label: "Decrease Budget", icon: "📉" },
  { value: "duplicate", label: "Duplicate", icon: "📋" },
  { value: "bid_adjust", label: "Bid Adjust", icon: "🎯" },
] as const;

export const AUDIENCE_TYPES = [
  { value: "lookalike", label: "Lookalike", color: "blue" },
  { value: "interest", label: "Interest", color: "violet" },
  { value: "broad", label: "Broad", color: "slate" },
  { value: "custom", label: "Custom", color: "emerald" },
  { value: "retargeting", label: "Retargeting", color: "amber" },
] as const;

export const FATIGUE_LEVELS = {
  fresh: { label: "Fresh", color: "emerald", emoji: "🟢" },
  declining: { label: "Declining", color: "amber", emoji: "🟡" },
  burned: { label: "Burned", color: "red", emoji: "🔴" },
} as const;

export const PLACEMENTS = [
  "feed", "stories", "reels", "right_column", "search", "other",
] as const;

export const METRICS = [
  "spend", "conversions", "cpl", "cpa", "ctr", "frequency",
  "roas", "cpc", "cpm", "impressions",
] as const;

export const OPERATORS = [">", "<", ">=", "<=", "=="] as const;

export const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: "chart", children: [
    { label: "Overview", href: "/dashboard" },
    { label: "Actions", href: "/dashboard/actions" },
    { label: "Anomalies", href: "/dashboard/anomalies" },
    { label: "Creatives", href: "/dashboard/creatives" },
    { label: "Audiences", href: "/dashboard/audiences" },
    { label: "Funnel", href: "/dashboard/funnel" },
  ]},
  { label: "Leads", href: "/leads", icon: "users" },
  { label: "Rules", href: "/rules", icon: "bolt" },
  { label: "Insights", href: "/insights", icon: "brain" },
  { label: "Competitors", href: "/competitors", icon: "search" },
  { label: "Reports", href: "/reports", icon: "document" },
  { label: "Settings", href: "/settings/accounts", icon: "cog", children: [
    { label: "Accounts", href: "/settings/accounts" },
    { label: "Seasonality", href: "/settings/seasonality" },
  ]},
] as const;
