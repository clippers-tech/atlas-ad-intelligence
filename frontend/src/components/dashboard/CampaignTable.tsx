"use client";

import { Card } from "@/components/common/Card";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import type { CampaignRow } from "@/lib/types";
import { formatCurrency, formatCurrencyDecimal, formatNumber, formatRoas } from "@/lib/utils";

interface CampaignTableProps {
  campaigns: CampaignRow[];
  targetCpl?: number | null;
}

export function CampaignTable({ campaigns, targetCpl }: CampaignTableProps) {
  return (
    <Card title="Campaign Performance" noPadding>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border)]">
              {["Campaign", "Status", "Spend", "Leads", "CPL", "Bookings", "Revenue", "ROAS"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {campaigns.map((c) => {
              const cplOver = targetCpl && c.cpl > targetCpl;
              return (
                <tr key={c.campaign_id ?? c.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors">
                  <td className="px-4 py-3 pl-5">
                    <span className="text-[13px] font-medium text-[var(--text)]">{c.name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge label={c.status} variant={getStatusVariant(c.status)} dot />
                  </td>
                  <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                    {formatCurrency(c.spend)}
                  </td>
                  <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                    {formatNumber(c.leads)}
                  </td>
                  <td className={`px-4 py-3 text-[13px] tabular-nums ${cplOver ? "text-red-400" : "text-[var(--text)]"}`}>
                    {formatCurrencyDecimal(c.cpl)}
                  </td>
                  <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                    {formatNumber(c.bookings)}
                  </td>
                  <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                    {formatCurrency(c.revenue)}
                  </td>
                  <td className="px-4 py-3 pr-5 text-[13px] tabular-nums text-[var(--text)]">
                    {formatRoas(c.roas)}
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
