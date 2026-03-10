"use client";

import { useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  variant?: "danger" | "default";
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open, title, message, confirmLabel = "Confirm",
  variant = "default", onConfirm, onCancel
}: ConfirmDialogProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = ""; };
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onCancel} />
      <div className="relative bg-[var(--surface-2)] border border-[var(--border)] rounded-xl p-5 max-w-sm w-full mx-4 shadow-xl">
        <h3 className="text-sm font-semibold text-[var(--text)] mb-1.5">{title}</h3>
        <p className="text-[12px] text-[var(--text-secondary)] mb-5">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] bg-[var(--surface-3)] hover:bg-[var(--border)] rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-3 py-1.5 text-[12px] font-medium rounded-lg transition-colors ${
              variant === "danger"
                ? "bg-red-500/15 text-red-400 hover:bg-red-500/25"
                : "bg-amber-500/15 text-amber-400 hover:bg-amber-500/25"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
