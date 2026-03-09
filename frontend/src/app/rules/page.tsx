"use client";

import { useState } from "react";
import { useRules, useCreateRule, useUpdateRule, useDeleteRule } from "@/hooks/useRules";
import type { Rule } from "@/lib/types";
import RuleList from "@/components/rules/RuleList";
import RuleForm from "@/components/rules/RuleForm";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

type ModalState =
  | { mode: "none" }
  | { mode: "create" }
  | { mode: "edit"; rule: Rule }
  | { mode: "history"; rule: Rule }
  | { mode: "delete"; rule: Rule };

export default function RulesPage() {
  const { data: rules = [], isLoading } = useRules();
  const createRule = useCreateRule();
  const updateRule = useUpdateRule();
  const deleteRule = useDeleteRule();

  const [modal, setModal] = useState<ModalState>({ mode: "none" });

  const handleToggle = (id: string, enabled: boolean) => {
    updateRule.mutate({ id, data: { is_enabled: enabled } });
  };

  const handleSubmit = (data: Partial<Rule>) => {
    if (modal.mode === "edit" && modal.rule) {
      updateRule.mutate(
        { id: modal.rule.id, data },
        { onSuccess: () => setModal({ mode: "none" }) }
      );
    } else {
      createRule.mutate(data, {
        onSuccess: () => setModal({ mode: "none" }),
      });
    }
  };

  const handleDelete = () => {
    if (modal.mode !== "delete") return;
    deleteRule.mutate(modal.rule.id, {
      onSuccess: () => setModal({ mode: "none" }),
    });
  };

  const isFormOpen = modal.mode === "create" || modal.mode === "edit";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Automation Rules</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Automatically pause, scale, and adjust ads based on performance triggers.
        </p>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : rules.length === 0 && !isFormOpen ? (
        <EmptyState
          title="No rules configured"
          description="Create your first automation rule to start optimising spend automatically."
          action={
            <button
              onClick={() => setModal({ mode: "create" })}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
            >
              + Create First Rule
            </button>
          }
        />
      ) : (
        <>
          {/* Inline form (slide-in style) */}
          {isFormOpen && (
            <div className="border border-gray-700 rounded-xl p-6 bg-gray-900/50">
              <h2 className="text-base font-semibold text-gray-200 mb-5">
                {modal.mode === "edit" ? "Edit Rule" : "Create Rule"}
              </h2>
              <RuleForm
                initialValues={modal.mode === "edit" ? modal.rule : undefined}
                onSubmit={handleSubmit}
                onCancel={() => setModal({ mode: "none" })}
              />
            </div>
          )}

          {!isFormOpen && (
            <RuleList
              rules={rules}
              onToggle={handleToggle}
              onEdit={(rule) => setModal({ mode: "edit", rule })}
              onCreate={() => setModal({ mode: "create" })}
              onViewHistory={(rule) => setModal({ mode: "history", rule })}
            />
          )}
        </>
      )}

      {/* History modal (simple) */}
      {modal.mode === "history" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md space-y-4">
            <h2 className="text-base font-semibold text-gray-200">
              History: {modal.rule.name}
            </h2>
            <p className="text-sm text-gray-400">
              Triggered {modal.rule.trigger_count ?? 0} times. Detailed trigger log
              coming soon.
            </p>
            <button
              onClick={() => setModal({ mode: "none" })}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Confirm delete */}
      <ConfirmDialog
        open={modal.mode === "delete"}
        title="Delete Rule"
        description={`Are you sure you want to delete "${modal.mode === "delete" ? modal.rule.name : ""}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDelete}
        onCancel={() => setModal({ mode: "none" })}
      />
    </div>
  );
}
