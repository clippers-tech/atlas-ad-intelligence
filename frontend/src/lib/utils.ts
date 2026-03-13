import { format, formatDistanceToNow, parseISO } from "date-fns";

const LOCALE_MAP: Record<string, string> = {
  AED: "en-AE",
  GBP: "en-GB",
  USD: "en-US",
  EUR: "de-DE",
  AUD: "en-AU",
  CAD: "en-CA",
};

function localeFor(currency: string): string {
  return LOCALE_MAP[currency] || "en-AE";
}

export function formatCurrency(value: number, currency = "AED"): string {
  return new Intl.NumberFormat(localeFor(currency), {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatCurrencyDecimal(value: number, currency = "AED"): string {
  return new Intl.NumberFormat(localeFor(currency), {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function currencySymbol(currency = "AED"): string {
  const parts = new Intl.NumberFormat(localeFor(currency), {
    style: "currency",
    currency,
  }).formatToParts(0);
  return parts.find((p) => p.type === "currency")?.value ?? currency;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-GB").format(value);
}

export function formatRoas(value: number): string {
  return `${value.toFixed(2)}x`;
}

export function formatDate(dateStr: string): string {
  return format(parseISO(dateStr), "MMM d, yyyy");
}

export function formatDateTime(dateStr: string): string {
  return format(parseISO(dateStr), "MMM d, yyyy h:mm a");
}

export function formatRelative(dateStr: string): string {
  return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
}

export function getChangeColor(current: number, previous: number, inverse = false): string {
  if (current === previous) return "text-gray-400";
  const better = inverse ? current < previous : current > previous;
  return better ? "text-emerald-400" : "text-red-400";
}

export function getChangeArrow(current: number, previous: number): string {
  if (current > previous) return "↑";
  if (current < previous) return "↓";
  return "→";
}

export function calcChange(current: number, previous: number): number {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
}

export function truncate(str: string, len: number): string {
  if (str.length <= len) return str;
  return str.slice(0, len) + "…";
}

export function stageColor(stage: string): string {
  const colors: Record<string, string> = {
    new: "bg-blue-500/20 text-blue-400",
    qualified: "bg-cyan-500/20 text-cyan-400",
    call_completed: "bg-violet-500/20 text-violet-400",
    proposal_sent: "bg-amber-500/20 text-amber-400",
    negotiation: "bg-orange-500/20 text-orange-400",
    closed_won: "bg-emerald-500/20 text-emerald-400",
    closed_lost: "bg-red-500/20 text-red-400",
  };
  return colors[stage] || "bg-gray-500/20 text-gray-400";
}
