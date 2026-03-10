"use client";

const iconProps = { width: 20, height: 20, fill: "none", stroke: "currentColor", strokeWidth: 1.5 };

export function OverviewIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

export function CampaignsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <path d="M3 7h4v14H3zM10 4h4v17h-4zM17 10h4v11h-4z" />
    </svg>
  );
}

export function AdSetsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <path d="M2 6h6v6H2zM9 6h6v6H9zM16 6h6v6h-6z" />
      <path d="M5 16v3M12 16v3M19 16v3" strokeLinecap="round" />
    </svg>
  );
}

export function AdsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 15l3-6 3 6M10 13h4" />
    </svg>
  );
}

export function CreativesIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <path d="M21 15l-5-5L5 21" />
    </svg>
  );
}

export function RulesIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );
}

export function CompetitorsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
    </svg>
  );
}

export function InsightsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <path d="M12 2a7 7 0 017 7c0 5.25-7 13-7 13S5 14.25 5 9a7 7 0 017-7z" />
      <circle cx="12" cy="9" r="2.5" />
    </svg>
  );
}

export function SettingsIcon() {
  return (
    <svg {...iconProps} viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}

export const NAV_ICON_MAP: Record<string, () => JSX.Element> = {
  overview: OverviewIcon,
  campaigns: CampaignsIcon,
  adsets: AdSetsIcon,
  ads: AdsIcon,
  creatives: CreativesIcon,
  rules: RulesIcon,
  competitors: CompetitorsIcon,
  insights: InsightsIcon,
  settings: SettingsIcon,
};
