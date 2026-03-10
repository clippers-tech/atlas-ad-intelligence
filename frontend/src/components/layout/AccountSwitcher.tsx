"use client";

import { useState, useRef, useEffect } from "react";
import { useAccountContext } from "@/contexts/AccountContext";
import clsx from "clsx";

export default function AccountSwitcher() {
  const { accounts, currentAccount, switchAccount } = useAccountContext();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!currentAccount) {
    return (
      <div className="text-[12px] text-[var(--muted)]">
        No accounts
      </div>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--surface-2)] hover:bg-[var(--surface-3)] transition-colors text-[12px] font-medium text-[var(--text)]"
      >
        <div className="w-5 h-5 rounded bg-amber-500/20 flex items-center justify-center text-amber-400 text-[10px] font-bold">
          {currentAccount.name.charAt(0)}
        </div>
        <span className="max-w-[120px] truncate">{currentAccount.name}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" className="text-[var(--muted)]">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && accounts.length > 1 && (
        <div className="absolute top-full right-0 mt-1 w-56 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg shadow-lg shadow-black/30 overflow-hidden z-50">
          {accounts.map((acct) => (
            <button
              key={acct.id}
              onClick={() => { switchAccount(acct.id); setOpen(false); }}
              className={clsx(
                "w-full flex items-center gap-2.5 px-3 py-2.5 text-[12px] transition-colors text-left",
                acct.id === currentAccount.id
                  ? "bg-amber-500/10 text-amber-400"
                  : "text-[var(--text-secondary)] hover:bg-[var(--surface-3)] hover:text-[var(--text)]"
              )}
            >
              <div className={clsx(
                "w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold",
                acct.id === currentAccount.id
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-[var(--surface-3)] text-[var(--muted)]"
              )}>
                {acct.name.charAt(0)}
              </div>
              <span className="truncate">{acct.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
