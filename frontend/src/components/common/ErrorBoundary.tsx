"use client";

import { Component, ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
          <div className="w-12 h-12 rounded-xl bg-red-500/12 border border-red-500/20 flex items-center justify-center mb-4">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="#EF4444" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
            Something went wrong
          </h3>
          <p className="text-[12px] text-[var(--muted)] max-w-xs mb-4">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-[12px] font-medium hover:bg-amber-500/25 transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
