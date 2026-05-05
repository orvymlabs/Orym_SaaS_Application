"use client";

export default function Footer() {
  return (
    <footer className="w-full py-4 text-center border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Powered by{" "}
        <a
          href="https://orvym.com"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-blue-600 dark:text-blue-400 hover:underline"
        >
          ORVYM LABS
        </a>
      </p>
    </footer>
  );
}
