"use client";

import { useState, type FormEvent } from "react";

interface AddCompetitorData {
  competitor_name: string;
  meta_page_id?: string;
  website_url?: string;
  facebook_url?: string;
  scraper_country: string;
  scraper_media_type: string;
  scraper_platforms: string;
  scraper_language: string;
}

interface Props {
  onSubmit: (data: AddCompetitorData) => void;
  onCancel: () => void;
}

const COUNTRIES = [
  { value: "ALL", label: "All Countries" },
  { value: "US", label: "United States" },
  { value: "GB", label: "United Kingdom" },
  { value: "AU", label: "Australia" },
  { value: "CA", label: "Canada" },
  { value: "DE", label: "Germany" },
  { value: "FR", label: "France" },
  { value: "IN", label: "India" },
  { value: "BR", label: "Brazil" },
];

const MEDIA_TYPES = [
  { value: "all", label: "All Media" },
  { value: "image", label: "Image Only" },
  { value: "video", label: "Video Only" },
  { value: "meme", label: "Meme Only" },
];

const PLATFORMS = [
  { value: "facebook", label: "Facebook" },
  { value: "instagram", label: "Instagram" },
  { value: "messenger", label: "Messenger" },
  { value: "audience_network", label: "Audience Network" },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
  { value: "ar", label: "Arabic" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
];

const inputCls =
  "w-full bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text)] text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-amber-500/50 placeholder-[var(--muted)]";

const selectCls =
  "w-full bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text)] text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-amber-500/50";

const labelCls =
  "block text-xs font-semibold text-[var(--muted)] uppercase tracking-wide mb-1.5";

export default function AddCompetitorForm({ onSubmit, onCancel }: Props) {
  const [name, setName] = useState("");
  const [pageId, setPageId] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [fbUrl, setFbUrl] = useState("");
  const [country, setCountry] = useState("ALL");
  const [mediaType, setMediaType] = useState("all");
  const [selectedPlatforms, setSelectedPlatforms] = useState(["facebook", "instagram"]);
  const [language, setLanguage] = useState("en");

  const togglePlatform = (val: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(val) ? prev.filter((p) => p !== val) : [...prev, val]
    );
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit({
      competitor_name: name.trim(),
      ...(pageId.trim() ? { meta_page_id: pageId.trim() } : {}),
      ...(websiteUrl.trim() ? { website_url: websiteUrl.trim() } : {}),
      ...(fbUrl.trim() ? { facebook_url: fbUrl.trim() } : {}),
      scraper_country: country,
      scraper_media_type: mediaType,
      scraper_platforms: selectedPlatforms.join(","),
      scraper_language: language,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Identity */}
      <SectionLabel text="Competitor Identity" />
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className={labelCls}>
            Name <span className="text-red-400">*</span>
          </label>
          <input value={name} onChange={(e) => setName(e.target.value)}
            required placeholder="e.g. SHEIN" className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Meta Page ID</label>
          <input value={pageId} onChange={(e) => setPageId(e.target.value)}
            placeholder="e.g. 15087023444" className={inputCls} pattern="[0-9]*" />
          <p className="text-[10px] text-[var(--muted)] mt-1">
            Numeric ID from the page&apos;s About section
          </p>
        </div>
        <div>
          <label className={labelCls}>Website URL</label>
          <input value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://shein.com" type="url" className={inputCls} />
        </div>
      </div>

      {/* Scraper Config */}
      <SectionLabel text="Scraper Configuration" />
      <div>
        <label className={labelCls}>Facebook Page URL</label>
        <input value={fbUrl} onChange={(e) => setFbUrl(e.target.value)}
          placeholder="https://www.facebook.com/SHEINOFFICIAL" className={inputCls} />
        <p className="text-[10px] text-[var(--muted)] mt-1">
          Direct FB page link — scraper uses this alongside the Ad Library URL
        </p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className={labelCls}>Country</label>
          <select value={country} onChange={(e) => setCountry(e.target.value)} className={selectCls}>
            {COUNTRIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>Media Type</label>
          <select value={mediaType} onChange={(e) => setMediaType(e.target.value)} className={selectCls}>
            {MEDIA_TYPES.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>Language</label>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className={selectCls}>
            {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>
      </div>

      {/* Platforms multi-select */}
      <div>
        <label className={labelCls}>Platforms</label>
        <div className="flex gap-2 flex-wrap">
          {PLATFORMS.map((p) => (
            <button key={p.value} type="button" onClick={() => togglePlatform(p.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedPlatforms.includes(p.value)
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                  : "bg-[var(--surface-2)] text-[var(--muted)] border border-[var(--border)]"
              }`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={!name.trim()}
          className="px-5 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors">
          Add Competitor
        </button>
        <button type="button" onClick={onCancel}
          className="px-4 py-2 bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--muted)] text-sm rounded-lg transition-colors">
          Cancel
        </button>
      </div>
    </form>
  );
}

function SectionLabel({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 pt-1">
      <span className="text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider">
        {text}
      </span>
      <div className="flex-1 h-px bg-[var(--border)]" />
    </div>
  );
}
