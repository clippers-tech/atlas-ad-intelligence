"use client";

import { useState, type FormEvent } from "react";
import type { Account } from "@/lib/types";

interface AccountFormProps {
  initialValues?: Account;
  onSubmit: (data: Partial<Account>) => void;
  onCancel: () => void;
}

const BUSINESS_TYPES = [
  { value: "web3", label: "Web3" },
  { value: "clippers", label: "Clippers" },
  { value: "agency", label: "Agency" },
] as const;

const CURRENCIES = ["GBP", "USD", "EUR", "AUD", "CAD"];

const TIMEZONES = [
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
  "America/Chicago",
  "Europe/Paris",
  "Asia/Dubai",
  "Australia/Sydney",
];

export default function AccountForm({
  initialValues,
  onSubmit,
  onCancel,
}: AccountFormProps) {
  const [name, setName] = useState(initialValues?.name ?? "");
  const [businessType, setBusinessType] = useState<Account["business_type"]>(
    initialValues?.business_type ?? "agency"
  );
  const [metaAdAccountId, setMetaAdAccountId] = useState(
    initialValues?.meta_ad_account_id ?? ""
  );
  const [targetCpl, setTargetCpl] = useState(String(initialValues?.target_cpl ?? ""));
  const [targetCpa, setTargetCpa] = useState(String(initialValues?.target_cpa ?? ""));
  const [targetRoas, setTargetRoas] = useState(String(initialValues?.target_roas ?? ""));
  const [timezone, setTimezone] = useState(initialValues?.timezone ?? "Europe/London");
  const [currency, setCurrency] = useState(initialValues?.currency ?? "GBP");
  const [telegramChatId, setTelegramChatId] = useState(
    initialValues?.telegram_chat_id ?? ""
  );

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      business_type: businessType,
      meta_ad_account_id: metaAdAccountId,
      target_cpl: targetCpl ? parseFloat(targetCpl) : null,
      target_cpa: targetCpa ? parseFloat(targetCpa) : null,
      target_roas: targetRoas ? parseFloat(targetRoas) : null,
      timezone,
      currency,
      telegram_chat_id: telegramChatId || null,
    });
  };

  const inputClass =
    "w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500 placeholder-gray-600";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Name */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Account Name <span className="text-red-400">*</span>
        </label>
        <input value={name} onChange={(e) => setName(e.target.value)} required className={inputClass} placeholder="e.g. Lumina Web3" />
      </div>

      {/* Business Type */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Business Type</label>
        <select value={businessType} onChange={(e) => setBusinessType(e.target.value as Account["business_type"])} className={inputClass}>
          {BUSINESS_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      {/* Meta Ad Account ID */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Meta Ad Account ID</label>
        <input value={metaAdAccountId} onChange={(e) => setMetaAdAccountId(e.target.value)} className={inputClass} placeholder="act_123456789" />
      </div>

      {/* Targets */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Target CPL (£)</label>
          <input type="number" value={targetCpl} onChange={(e) => setTargetCpl(e.target.value)} min={0} step={0.01} className={inputClass} placeholder="0.00" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Target CPA (£)</label>
          <input type="number" value={targetCpa} onChange={(e) => setTargetCpa(e.target.value)} min={0} step={0.01} className={inputClass} placeholder="0.00" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Target ROAS</label>
          <input type="number" value={targetRoas} onChange={(e) => setTargetRoas(e.target.value)} min={0} step={0.01} className={inputClass} placeholder="3.00" />
        </div>
      </div>

      {/* Timezone + Currency */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Timezone</label>
          <select value={timezone} onChange={(e) => setTimezone(e.target.value)} className={inputClass}>
            {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Currency</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)} className={inputClass}>
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Telegram */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Telegram Chat ID <span className="text-gray-600 font-normal normal-case">(optional)</span></label>
        <input value={telegramChatId} onChange={(e) => setTelegramChatId(e.target.value)} className={inputClass} placeholder="-100123456789" />
      </div>

      {/* Buttons */}
      <div className="flex gap-3 pt-1">
        <button type="submit" className="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors">
          {initialValues ? "Save Changes" : "Create Account"}
        </button>
        <button type="button" onClick={onCancel} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors">
          Cancel
        </button>
      </div>
    </form>
  );
}
