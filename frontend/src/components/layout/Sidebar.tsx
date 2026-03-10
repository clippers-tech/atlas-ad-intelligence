"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { NAV_ITEMS } from "@/lib/constants";
import { NAV_ICON_MAP } from "./NavIcons";

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[var(--sidebar-width)] h-screen bg-[var(--surface)] border-r border-[var(--border)] flex flex-col fixed left-0 top-0 z-30">
      {/* Brand */}
      <div className="px-5 py-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"
                stroke="#F59E0B" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-[var(--text)] tracking-tight">
              ATLAS
            </h1>
            <p className="text-[11px] text-[var(--muted)] leading-none mt-0.5">
              Ad Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-3"
        style={{ overscrollBehavior: "contain" }}>
        <div className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const IconComponent = NAV_ICON_MAP[item.icon];

            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150",
                  isActive
                    ? "bg-amber-500/12 text-amber-400"
                    : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]"
                )}
              >
                <span className={clsx(
                  "flex-shrink-0",
                  isActive ? "text-amber-400" : "text-[var(--muted)]"
                )}>
                  {IconComponent && <IconComponent />}
                </span>
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[var(--border)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-500/60" />
          <span className="text-[11px] text-[var(--muted)]">
            Meta Ads Only
          </span>
        </div>
      </div>
    </aside>
  );
}
