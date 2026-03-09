"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";

const NAV = [
  { label: "Dashboard", href: "/dashboard", icon: "📊", children: [
    { label: "Overview", href: "/dashboard" },
    { label: "Actions", href: "/dashboard/actions" },
    { label: "Anomalies", href: "/dashboard/anomalies" },
    { label: "Creatives", href: "/dashboard/creatives" },
    { label: "Audiences", href: "/dashboard/audiences" },
    { label: "Funnel", href: "/dashboard/funnel" },
  ]},
  { label: "Leads", href: "/leads", icon: "👤" },
  { label: "Rules", href: "/rules", icon: "🎯" },
  { label: "Insights", href: "/insights", icon: "🧠" },
  { label: "Competitors", href: "/competitors", icon: "🔍" },
  { label: "Reports", href: "/reports", icon: "📄" },
  { label: "Settings", href: "/settings/accounts", icon: "⚙️", children: [
    { label: "Accounts", href: "/settings/accounts" },
    { label: "Seasonality", href: "/settings/seasonality" },
  ]},
];

export default function Sidebar() {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState<string | null>("Dashboard");

  return (
    <aside className="w-56 h-screen bg-[#0f0f0f] border-r border-[#262626] flex flex-col fixed left-0 top-0 z-30">
      <div className="p-4 border-b border-[#262626]">
        <h1 className="text-lg font-bold tracking-tight text-white">
          ⚡ ATLAS
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">Ad Intelligence System</p>
      </div>
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          const isOpen = expanded === item.label;
          const hasChildren = item.children && item.children.length > 0;

          return (
            <div key={item.label}>
              <button
                onClick={() => {
                  if (hasChildren) setExpanded(isOpen ? null : item.label);
                }}
                className={clsx(
                  "w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors",
                  isActive ? "text-white bg-white/5" : "text-gray-400 hover:text-white hover:bg-white/5"
                )}
              >
                <span className="text-base">{item.icon}</span>
                {!hasChildren ? (
                  <Link href={item.href} className="flex-1 text-left">{item.label}</Link>
                ) : (
                  <span className="flex-1 text-left">{item.label}</span>
                )}
                {hasChildren && (
                  <span className="text-xs">{isOpen ? "▾" : "▸"}</span>
                )}
              </button>
              {hasChildren && isOpen && (
                <div className="ml-8 border-l border-[#262626]">
                  {item.children!.map((child) => (
                    <Link
                      key={child.href}
                      href={child.href}
                      className={clsx(
                        "block px-3 py-1.5 text-xs transition-colors",
                        pathname === child.href
                          ? "text-white bg-white/5"
                          : "text-gray-500 hover:text-white"
                      )}
                    >
                      {child.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
      <div className="p-3 border-t border-[#262626] text-xs text-gray-600">
        v1.0.0
      </div>
    </aside>
  );
}
