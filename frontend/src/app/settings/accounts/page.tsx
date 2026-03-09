"use client";

import { useState } from "react";
import { useAccounts, useUpdateAccount } from "@/hooks/useSettings";
import type { Account } from "@/lib/types";
import AccountForm from "@/components/settings/AccountForm";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

export default function AccountsPage() {
  const { data: accounts = [], isLoading } = useAccounts();
  const updateAccount = useUpdateAccount();
  const [editTarget, setEditTarget] = useState<Account | null>(null);

  const handleSave = (data: Partial<Account>) => {
    if (!editTarget) return;
    updateAccount.mutate(
      { id: editTarget.id, data },
      { onSuccess: () => setEditTarget(null) }
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Account Settings</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Manage your ad accounts, targets, and integrations.
        </p>
      </div>

      {/* Edit form */}
      {editTarget && (
        <div className="border border-gray-700 rounded-xl p-6 bg-gray-900/50">
          <h2 className="text-base font-semibold text-gray-200 mb-5">
            Edit Account: {editTarget.name}
          </h2>
          <AccountForm
            initialValues={editTarget}
            onSubmit={handleSave}
            onCancel={() => setEditTarget(null)}
          />
        </div>
      )}

      {/* Accounts table */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : accounts.length === 0 ? (
        <EmptyState
          title="No accounts configured"
          description="Accounts are provisioned by your system administrator."
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/50">
                {[
                  "Name",
                  "Business Type",
                  "Meta Account ID",
                  "Target CPL",
                  "Target ROAS",
                  "Currency",
                  "Status",
                  "Actions",
                ].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-200">{account.name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 text-gray-400 capitalize">
                      {account.business_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">
                    {account.meta_ad_account_id}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {account.target_cpl != null ? `£${account.target_cpl}` : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {account.target_roas != null ? `${account.target_roas}x` : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{account.currency}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        account.is_active
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-gray-700 text-gray-500"
                      }`}
                    >
                      {account.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setEditTarget(account)}
                      className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
