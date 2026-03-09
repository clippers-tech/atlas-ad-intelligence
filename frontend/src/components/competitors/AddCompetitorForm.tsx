"use client";

import { useState, type FormEvent } from "react";

interface AddCompetitorData {
  competitor_name: string;
  meta_page_id?: string;
  website_url?: string;
}

interface AddCompetitorFormProps {
  onSubmit: (data: AddCompetitorData) => void;
  onCancel: () => void;
}

export default function AddCompetitorForm({
  onSubmit,
  onCancel,
}: AddCompetitorFormProps) {
  const [name, setName] = useState("");
  const [metaPageId, setMetaPageId] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit({
      competitor_name: name.trim(),
      ...(metaPageId.trim() ? { meta_page_id: metaPageId.trim() } : {}),
      ...(websiteUrl.trim() ? { website_url: websiteUrl.trim() } : {}),
    });
  };

  const inputClass =
    "w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500 placeholder-gray-600";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Name */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Competitor Name <span className="text-red-400">*</span>
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g. Acme Marketing Agency"
          className={inputClass}
        />
      </div>

      {/* Meta Page ID */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Meta Page ID{" "}
          <span className="text-gray-600 font-normal normal-case">(optional)</span>
        </label>
        <input
          value={metaPageId}
          onChange={(e) => setMetaPageId(e.target.value)}
          placeholder="e.g. 123456789"
          className={inputClass}
          pattern="[0-9]*"
        />
        <p className="text-xs text-gray-600 mt-1">
          Found in facebook.com/pg/[page-name]/about → Page ID
        </p>
      </div>

      {/* Website URL */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Website URL{" "}
          <span className="text-gray-600 font-normal normal-case">(optional)</span>
        </label>
        <input
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          placeholder="https://example.com"
          type="url"
          className={inputClass}
        />
      </div>

      {/* Buttons */}
      <div className="flex gap-3 pt-1">
        <button
          type="submit"
          disabled={!name.trim()}
          className="px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
        >
          Add Competitor
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
