"use client";

import { useState } from "react";
import { useRules } from "@/hooks/useRules";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import type { Rule } from "@/lib/types";
import { formatCurrency, formatNumber, formatRelative } from "@/lib/utils";
import RuleForm from "@/components/rules/RuleForm";
import { postData } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

const typeColors: Record<string, string> = {
  kill: "danger",
  scale: "success",
  launch: "info",
  bid: "amber",
};

export default function RulesPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const { data, isLoading } = useRules();
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to manage rules." />;
  }

  if (isLoading) return <PageLoader />;
  const rules: Rule[] = data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Rules"
        subtitle="Automation rules to optimize, scale, or kill ads"
        actions={
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-[12px] font-medium hover:bg-amber-500/25 transition-colors"
          >
            + New Rule
          </button>
        }
      />
      {showForm && (
        <Card title={"Create New Rule"} subtitle={"Define conditions and actions for automated ad management"}>
          <RuleForm
            onSubmit={async (data) => {
              await postData("/rules", { ...data, account_id: currentAccount.id });
              queryClient.invalidateQueries({ queryKey: ["rules"] });
              setShowForm(false);
            }}
            onCancel={() => setShowForm(false)}
          />
        </Card>
      )}
      {rules.length === 0 && !showForm ? (
        <EmptyState
          title="No rules yet"
          description="Create automation rules to automatically manage your Meta ads based on performance metrics."
          action={{ label: "Create First Rule", onClick: () => setShowForm(true) }}
        />
      ) : rules.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map((rule) => (
            <Card key={rule.id} className="hover:border-[var(--border-light)] transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <StatusBadge
                    label={rule.type.toUpperCase()}
                    variant={(typeColors[rule.type] || "muted") as "danger" | "success" | "info" | "amber" | "muted"}
                  />
                  <span className={`w-2 h-2 rounded-full ${rule.is_enabled ? "bg-emerald-400" : "bg-[var(--muted)]"}`} />
                </div>
                <span className="text-[11px] text-[var(--muted)]">
                  Priority: {rule.priority}
                </span>
              </div>
              <h4 className="text-[13px] font-semibold text-[var(--text)] mb-1">{rule.name}</h4>
              {rule.description && (
                <p className="text-[12px] text-[var(--text-secondary)] mb-3">{rule.description}</p>
              )}
              {rule.budget_limit != null && (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-[var(--muted)]">Budget</span>
                    <span className="text-[11px] font-medium text-[var(--text)]">
                      {formatCurrency(rule.budget_spent ?? 0)} / {formatCurrency(rule.budget_limit)}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[var(--surface-2)] overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        (rule.budget_spent ?? 0) >= rule.budget_limit
                          ? "bg-red-500"
                          : (rule.budget_spent ?? 0) / rule.budget_limit > 0.75
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, ((rule.budget_spent ?? 0) / rule.budget_limit) * 100)}%` }}
                    />
                  </div>
                </div>
              )}
              <div className="flex items-center gap-4 pt-3 border-t border-[var(--border)]/50">
                <div className="text-[11px] text-[var(--muted)]">
                  Triggers: <span className="text-[var(--text)] font-medium">{formatNumber(rule.trigger_count ?? 0)}</span>
                </div>
                {rule.last_triggered && (
                  <div className="text-[11px] text-[var(--muted)]">
                    Last: <span className="text-[var(--text-secondary)]">{formatRelative(rule.last_triggered)}</span>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}
