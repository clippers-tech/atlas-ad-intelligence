"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import type { Account } from "@/lib/types";
import { fetchData } from "@/lib/api";

interface AccountContextType {
  accounts: Account[];
  currentAccount: Account | null;
  switchAccount: (accountId: string) => void;
  isLoading: boolean;
}

const AccountContext = createContext<AccountContextType>({
  accounts: [],
  currentAccount: null,
  switchAccount: () => {},
  isLoading: true,
});

export function AccountProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [currentAccount, setCurrentAccount] = useState<Account | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData<{ data: Account[] }>("/accounts")
      .then((res) => {
        const list = res.data || [];
        setAccounts(list);
        const savedId = localStorage.getItem("atlas_account_id");
        const found = list.find((a) => a.id === savedId);
        const initial = found || list[0] || null;
        setCurrentAccount(initial);
        if (initial) localStorage.setItem("atlas_account_id", initial.id);
      })
      .catch(() => setAccounts([]))
      .finally(() => setIsLoading(false));
  }, []);

  const switchAccount = useCallback(
    (accountId: string) => {
      const acct = accounts.find((a) => a.id === accountId);
      if (acct) {
        setCurrentAccount(acct);
        localStorage.setItem("atlas_account_id", acct.id);
      }
    },
    [accounts]
  );

  return (
    <AccountContext.Provider value={{ accounts, currentAccount, switchAccount, isLoading }}>
      {children}
    </AccountContext.Provider>
  );
}

export function useAccountContext() {
  return useContext(AccountContext);
}
