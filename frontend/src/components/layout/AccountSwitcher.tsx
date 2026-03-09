"use client";

import { useAccountContext } from "@/contexts/AccountContext";
import { useState, useRef, useEffect } from "react";
import clsx from "clsx";

const TYPE_COLORS: Record<string, string> = {
  web3: "bg-violet-500/20 text-violet-400",
  clippers: "bg-emerald-500/20 text-emerald-400",
  agency: "bg-blue-500/20 text-blue-400",
};

export default function AccountSwitcher() {
  const { accounts, currentAccount, switchAccount } = useAccountContext();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!currentAccount) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#1a1a1a] border border-[#333] hover:border-[#555] transition-colors"
      >
        <span className={clsx("text-xs px-1.5 py-0.5 rounded", TYPE_COLORS[currentAccount.business_type])}>
          {currentAccount.business_type.toUpperCase()}
        </span>
        <span className="text-sm text-white font-medium">{currentAccount.name}</span>
        <span className="text-xs text-gray-500">▾</span>
      </button>
      {open && (
        <div className="absolute top-full mt-1 right-0 w-64 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl z-50">
          {accounts.map((acct) => (
            <button
              key={acct.id}
              onClick={() => { switchAccount(acct.id); setOpen(false); }}
              className={clsx(
                "w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors",
                acct.id === currentAccount.id ? "bg-white/10 text-white" : "text-gray-400 hover:bg-white/5"
              )}
            >
              <span className={clsx("text-xs px-1.5 py-0.5 rounded", TYPE_COLORS[acct.business_type])}>
                {acct.business_type.toUpperCase()}
              </span>
              <span className="flex-1 text-left">{acct.name}</span>
              {acct.id === currentAccount.id && <span className="text-emerald-400">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
