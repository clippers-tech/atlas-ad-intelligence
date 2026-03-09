"use client";

import { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="rounded-xl bg-[#1a1a1a] border border-[#262626] px-10 py-12 max-w-md w-full">
        {icon && (
          <div
            className="text-4xl mb-4 select-none"
            role="img"
            aria-label={title}
          >
            {icon}
          </div>
        )}
        <h3 className="text-base font-semibold text-gray-200 mb-2">
          {title}
        </h3>
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          {description}
        </p>
        {action && (
          <div className="flex justify-center">
            {action}
          </div>
        )}
      </div>
    </div>
  );
}
