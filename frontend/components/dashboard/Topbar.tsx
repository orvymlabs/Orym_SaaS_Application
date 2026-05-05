"use client";

interface TopbarProps {
  isDark: boolean;
  botStatus: boolean;
  userName?: string;
}

export default function Topbar({ isDark, botStatus, userName = "Farrukh" }: TopbarProps) {
  return (
    <div className="mb-6">
      <h1 className={`text-2xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Dashboard</h1>
      <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} text-sm font-medium`}>Welcome back, {userName} 👋</p>
    </div>
  );
}
