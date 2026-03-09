"use client";

import { Component, ReactNode, ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
          <div className="rounded-xl bg-[#1a1a1a] border border-[#262626] px-10 py-12 max-w-md w-full">
            <div className="text-3xl mb-4" role="img" aria-label="Error">
              ⚠️
            </div>
            <h3 className="text-base font-semibold text-gray-200 mb-2">
              Something went wrong
            </h3>
            {this.state.error && (
              <p className="text-xs text-gray-600 font-mono mb-4 truncate">
                {this.state.error.message}
              </p>
            )}
            <p className="text-sm text-gray-500 leading-relaxed mb-6">
              An unexpected error occurred. You can try reloading this section
              or refreshing the page.
            </p>
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
