"use client";

import { useState } from "react";
import { useRules, useUpdateRule } from "@/hooks/useRules";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import type { Rule } from "@/lib/types";
import { formatCurrency, formatNumber, formatRelative } from "@/lib/utils";
import RuleForm from "@/components/rules/RuleForm";
import { postData, deleteData } from "@/lib/api";
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
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const queryClient = useQueryClient();
  const updateRule = useUpdateRule();

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to manage rules." />;
  }

  if (isLoading) return <PageLoader />;
  const rules: Rule[] = data ?? [];

  const handleEdit = (rule: Rule) => {
    setEditingRule(rule);
    setShowForm(false); // close new-rule form if open
  };

  const handleEditSubmit = async (data: Partial<Rule>) => {
    if (!editingRule) return;
    await updateRule.mutateAsync({ id: editingRule.id, data });
    setEditingRule(null);
  };

  const handleCreate = async (data: Partial<Rule>) => {
    await postData("/rules", { ...data, account_id: currentAccount.id });
    queryClient.invalidateQueries({ queryKey: ["rules"] });
    setShowForm(false);
  };

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Rules"
        subtitle="Automation rules to optimize, scale, or kill ads"
        actions={
          <button
            onClick={() => { setShowForm(!showForm); setEditingRule(null); }}
            className="px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-[12px] font-medium hover:bg-amber-500/25 transition-colors"
          >
            + New Rule
          </button>
        }
      />

      {/* New rule form */}
      {showForm && !editingRule && (
        <Card title="Create New Rule" subtitle="Define conditions and actions for automated ad management">
          <RuleForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </Card>
      )}

      {/* Edit rule form */}
      {editingRule && (
        <Card title={`Edit: ${editingRule.name}`} subtitle="Modify rule settings, conditions, or budget">
          <RuleForm
            initialValues={editingRule}
            onSubmit={handleEditSubmit}
            onCancel={() => setEditingRule(null)}
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
            <RuleCardInline
              key={rule.id}
              rule={rule}
              isEditing={editingRule?.id === rule.id}
              onEdit={() => handleEdit(rule)}
              onDelete={async () => {
                if (!confirm(`Delete rule "${rule.name}"?`)) return;
                await deleteData(`/rules/${rule.id}`);
                queryClient.invalidateQueries({ queryKey: ["rules"] });
                if (editingRule?.id === rule.id) setEditingRule(null);
              }}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Inline rule card with edit + delete buttons */
function RuleCardInline({
  rule,
  isEditing,
  onEdit,
  onDelete,
}: {
  rule: Rule;
  isEditing: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <Card
      className={`hover:border-[var(--border-light)] transition-colors ${
        isEditing ? "ring-1 ring-amber-500/40" : ""
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusBadge
            label={rule.type.toUpperCase()}
            variant={(typeColors[rule.type] || "muted") as "danger" | "success" | "info" | "amber" | "muted"}
          />
          <span className={`w-2 h-2 rounded-full ${rule.is_enabled ? "bg-emerald-400" : "bg-[var(--muted)]"}`} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[var(--muted)]">Priority: {rule.priority}</span>
          <button
            onClick={onEdit}
            className="px-2 py-1 rounded-md bg-[var(--surface-2)] text-[11px] text-[var(--muted)] hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 rounded-md bg-[var(--surface-2)] text-[11px] text-[var(--muted)] hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            Delete
          </button>
        </div>
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
  );
}
