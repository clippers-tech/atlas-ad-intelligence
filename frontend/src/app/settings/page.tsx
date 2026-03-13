"use client";

import { useState } from "react";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";

type Tab = "accounts" | "targets" | "notifications";

export default function SettingsPage() {
  const { currentAccount, accounts, isLoading: accountLoading } = useAccountContext();
  const [activeTab, setActiveTab] = useState<Tab>("accounts");

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to manage settings." />;
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "accounts", label: "Accounts" },
    { id: "targets", label: "Targets" },
    { id: "notifications", label: "Notifications" },
  ];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Settings" subtitle="Manage accounts and configuration" />

      {/* Tab bar */}
      <div className="flex gap-1 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-[12px] font-medium rounded-md transition-all duration-150 ${
              activeTab === tab.id
                ? "bg-amber-500/15 text-amber-400"
                : "text-[var(--muted)] hover:text-[var(--text-secondary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "accounts" && (
        <Card title="Ad Accounts" subtitle="Meta ad accounts connected to ATLAS">
          <div className="flex flex-col gap-3">
            {accounts.map((acct) => (
              <div key={acct.id} className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]/50">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center text-amber-400 text-[12px] font-bold">
                    {acct.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-[13px] font-medium text-[var(--text)]">{acct.name}</p>
                    <p className="text-[11px] text-[var(--muted)]">ID: {acct.meta_ad_account_id}</p>
                  </div>
                </div>
                <span className={`w-2 h-2 rounded-full ${acct.is_active ? "bg-emerald-400" : "bg-[var(--muted)]"}`} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === "targets" && (
        <Card title="Performance Targets" subtitle="Set target metrics for alerts and automation">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: "Target CPL", value: currentAccount.target_cpl, unit: currentAccount.currency || "AED" },
              { label: "Target CPA", value: currentAccount.target_cpa, unit: currentAccount.currency || "AED" },
              { label: "Target ROAS", value: currentAccount.target_roas, unit: "x" },
            ].map((t) => (
              <div key={t.label} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]/50">
                <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider mb-1">{t.label}</p>
                <p className="text-lg font-bold text-[var(--text)] tabular-nums">
                  {t.value !== null && t.value !== undefined ? `${t.value} ${t.unit}` : "Not set"}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === "notifications" && (
        <Card title="Notification Settings" subtitle="Configure how ATLAS alerts you">
          <div className="text-[12px] text-[var(--text-secondary)]">
            <p>Telegram integration for real-time alerts.</p>
            <div className="mt-3 p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]/50">
              <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider mb-1">Telegram Chat ID</p>
              <p className="text-[13px] text-[var(--text)] font-mono">
                {currentAccount.telegram_chat_id || "Not configured"}
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
