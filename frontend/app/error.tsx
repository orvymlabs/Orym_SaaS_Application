"use client";
import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 flex items-center justify-center p-4">
      <div className="max-w-2xl mx-auto text-center space-y-8">
        {/* Error Icon */}
        <div className="relative">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center shadow-2xl shadow-red-200">
            <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="absolute inset-0 blur-3xl bg-gradient-to-r from-red-400 to-orange-400 opacity-20 -z-10"></div>
        </div>

        {/* Message */}
        <div className="space-y-4">
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 tracking-tight">
            Something Went Wrong
          </h1>
          <p className="text-xl text-slate-600 max-w-md mx-auto">
            We encountered an unexpected error. Please try again.
          </p>
          {error.message && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl max-w-lg mx-auto">
              <p className="text-sm text-red-800 font-mono break-words">
                {error.message}
              </p>
            </div>
          )}
        </div>

        {/* Logo */}
        <div className="flex justify-center">
          <div className="bg-white p-6 rounded-3xl shadow-xl shadow-red-100 border border-slate-100">
            <img src="/logo.png" alt="ORVYM" className="w-20 h-20 object-contain" />
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <button
            onClick={reset}
            className="px-8 py-4 bg-gradient-to-r from-red-600 to-orange-600 text-white rounded-2xl font-bold shadow-lg shadow-red-200 hover:shadow-xl hover:shadow-red-300 transition-all hover:-translate-y-0.5"
          >
            Try Again
          </button>
          <Link
            href="/dashboard"
            className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-bold border-2 border-slate-200 hover:border-red-300 hover:bg-red-50 transition-all"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/"
            className="px-8 py-4 bg-slate-100 text-slate-700 rounded-2xl font-bold hover:bg-slate-200 transition-all"
          >
            Go Home
          </Link>
        </div>

        {/* Help Text */}
        <div className="pt-8">
          <p className="text-sm text-slate-500">
            If this problem persists, please contact support.
          </p>
        </div>
      </div>
    </div>
  );
}
