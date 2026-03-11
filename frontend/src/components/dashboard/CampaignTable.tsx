"use client";

import { Card } from "@/components/common/Card";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import type { CampaignRow } from "@/lib/types";
import {
  formatCurrency,
  formatCurrencyDecimal,
  formatNumber,
  formatPercent,
} from "@/lib/utils";

interface CampaignTableProps {
  campaigns: CampaignRow[];
  targetCpl?: number | null;
}

const HEADERS = [
  "Campaign",
  "Status",
  "Spend",
  "Impressions",
  "Link Clicks",
  "CPM",
  "CTR (Link)",
  "CPC (Link)",
  "LPV",
  "Results",
  "CPL",
] as const;

export function CampaignTable({ campaigns, targetCpl }: CampaignTableProps) {
  return (
    <Card title="Campaign Performance" noPadding>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border)]">
              {HEADERS.map((h) => (
                <th
                  key={h}
                  className="px-3 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5 whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {campaigns.map((c) => {
              const cplOver = targetCpl && c.cpl > targetCpl;
              const cell =
                "px-3 py-3 text-[13px] tabular-nums text-[var(--text)] whitespace-nowrap";
              return (
                <tr
                  key={c.campaign_id ?? c.id}
                  className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors"
                >
                  <td className="px-3 py-3 pl-5 min-w-[180px]">
                    <span className="text-[13px] font-medium text-[var(--text)] line-clamp-1">
                      {c.name}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge
                      label={c.status}
                      variant={getStatusVariant(c.status)}
                      dot
                    />
                  </td>
                  <td className={cell}>{v(c.spend, formatCurrency)}</td>
                  <td className={cell}>{v(c.impressions, formatNumber)}</td>
                  <td className={cell}>{v(c.link_clicks, formatNumber)}</td>
                  <td className={cell}>{v(c.cpm, formatCurrencyDecimal)}</td>
                  <td className={cell}>{v(c.ctr_link, formatPercent)}</td>
                  <td className={cell}>{v(c.cpc_link, formatCurrencyDecimal)}</td>
                  <td className={cell}>
                    {v(c.landing_page_views, formatNumber)}
                  </td>
                  <td className={cell}>{v(c.leads, formatNumber)}</td>
                  <td
                    className={`px-3 py-3 pr-5 text-[13px] tabular-nums whitespace-nowrap ${
                      cplOver ? "text-red-400" : "text-[var(--text)]"
                    }`}
                  >
                    {v(c.cpl, formatCurrencyDecimal)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function v(n: number | undefined, fmt: (n: number) => string): string {
  if (n === undefined || n === null || n === 0) return "—";
  return fmt(n);
}
