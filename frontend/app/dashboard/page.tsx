"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";

import StatCards from "@/components/dashboard/StatCards";
import AnalyticsChart from "@/components/dashboard/AnalyticsChart";
import RightColumn from "@/components/dashboard/RightColumn";

import "@/components/dashboard/dashboard.css";

export default function DashboardPage() {
  const [bot, setBot] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [integrations, setIntegrations] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { isDark } = useTheme();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [botData, leadsData, usageData, convData, integData] = await Promise.all([
          apiGet("/api/bots/me").catch(() => ({ mode: "default", status: false })),
          apiGet("/api/leads?limit=10").catch(() => []),
          apiGet("/api/auth/usage").catch(() => ({
            whatsapp_messages_sent: 0,
            whatsapp_limit: 200,
            ai_requests_made: 0,
            ai_limit: 1500,
            plan: "starter",
          })),
          apiGet("/api/conversations/").catch(() => []),
          apiGet("/api/integrations/me").catch(() => null),
        ]);

        setBot(botData);
        setLeads(leadsData);
        setUsage(usageData);
        setConversations(convData);
        setIntegrations(integData);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Listen for bot mode changes from settings page
    const handleBotModeChange = () => {
      apiGet("/api/bots/me").then((botData) => {
        setBot(botData);
      }).catch(console.error);
    };

    window.addEventListener('botModeChanged', handleBotModeChange);

    return () => {
      window.removeEventListener('botModeChanged', handleBotModeChange);
    };
  }, []);

  /* ---------------- LOADING UI ---------------- */
  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className={`h-6 w-48 rounded-lg ${isDark ? 'bg-zinc-800' : 'bg-slate-200'}`} />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className={`h-28 rounded-2xl ${isDark ? 'bg-zinc-900' : 'bg-slate-100'}`} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className={`lg:col-span-2 h-80 rounded-2xl ${isDark ? 'bg-zinc-900' : 'bg-slate-100'}`} />
            <div className={`h-80 rounded-2xl ${isDark ? 'bg-zinc-900' : 'bg-slate-100'}`} />
          </div>
        </div>
      </div>
    );
  }

  /* ---------------- MAIN UI ---------------- */
  const getBotModeLabel = (mode: string) => {
    const modes: Record<string, string> = {
      default: "Customize Flow Mode",
      predefined: "Keyword Trigger Mode",
      ai: "Dynamic AI Mode"
    };
    return modes[mode] || "Customize Flow Mode";
  };

  return (
    <div className="main">
      <div className="dashboard-content">
        {/* LEFT COLUMN */}
        <div className="col-left">

          {/* Active Bot Mode Card */}
          <a href="/dashboard/settings" className="block no-underline">
            <div className={`group rounded-[1.25rem] p-6 border transition-all duration-300 cursor-pointer ${
              isDark
                ? 'bg-gradient-to-br from-[#0c0c1d] to-[#09090b] border-zinc-800/60 hover:border-violet-500/30 hover:shadow-[0_8px_32px_-8px_rgba(108,78,242,0.15)]'
                : 'bg-gradient-to-br from-white to-violet-50/30 border-slate-200 hover:border-violet-300 hover:shadow-[0_8px_32px_-8px_rgba(108,78,242,0.12)]'
            }`}>
              <div className="flex items-center justify-between gap-6">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className={`flex-shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center transition-colors duration-300 ${
                    isDark ? 'bg-violet-500/10 group-hover:bg-violet-500/15' : 'bg-violet-100 group-hover:bg-violet-200/70'
                  }`}>
                    <svg className={`w-6 h-6 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className={`text-[10px] font-bold uppercase tracking-[0.15em] ${isDark ? 'text-zinc-500' : 'text-slate-400'}`}>
                      Active Bot Mode
                    </p>
                    <p className={`text-lg font-bold mt-1 truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      {getBotModeLabel(bot?.mode || "default")}
                    </p>
                  </div>
                </div>

                {/* AI Neural Visual */}
                <div className="hidden sm:flex items-center justify-center flex-shrink-0 w-20 h-20 opacity-40 group-hover:opacity-60 transition-opacity duration-300">
                  <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
                    <circle cx="40" cy="40" r="6" fill={isDark ? '#8b6ff5' : '#6c4ef2'} opacity="0.6" />
                    <circle cx="40" cy="40" r="14" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.8" opacity="0.3" />
                    <circle cx="40" cy="40" r="24" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.5" opacity="0.15" />
                    <circle cx="40" cy="16" r="3" fill={isDark ? '#60a5fa' : '#3b82f6'} opacity="0.5" />
                    <circle cx="60" cy="28" r="3" fill={isDark ? '#4ade80' : '#10b981'} opacity="0.5" />
                    <circle cx="60" cy="52" r="3" fill={isDark ? '#a78bfa' : '#6c4ef2'} opacity="0.5" />
                    <circle cx="40" cy="64" r="3" fill={isDark ? '#fbbf24' : '#f59e0b'} opacity="0.5" />
                    <circle cx="20" cy="52" r="3" fill={isDark ? '#60a5fa' : '#3b82f6'} opacity="0.5" />
                    <circle cx="20" cy="28" r="3" fill={isDark ? '#4ade80' : '#10b981'} opacity="0.5" />
                    <line x1="40" y1="40" x2="40" y2="16" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                    <line x1="40" y1="40" x2="60" y2="28" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                    <line x1="40" y1="40" x2="60" y2="52" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                    <line x1="40" y1="40" x2="40" y2="64" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                    <line x1="40" y1="40" x2="20" y2="52" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                    <line x1="40" y1="40" x2="20" y2="28" stroke={isDark ? '#8b6ff5' : '#6c4ef2'} strokeWidth="0.6" opacity="0.25" />
                  </svg>
                </div>

                <div className={`flex-shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-full text-[10px] font-bold uppercase tracking-wider transition-colors duration-300 ${
                  isDark
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15'
                    : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                }`}>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                  <span>Active</span>
                </div>
              </div>
            </div>
          </a>

          <StatCards
            messagesCount={`${usage?.whatsapp_messages_sent ?? 0}/${usage?.whatsapp_limit ?? 200}`}
            contactsCount={leads.length}
            aiRequestsCount={`${usage?.ai_requests_made ?? 0}/${usage?.ai_limit ?? 1500}`}
            isDark={isDark}
          />
          
          {/* Handle cases where analytics data might be empty */}
          {usage?.whatsapp_messages_sent === undefined && usage?.ai_requests_made === undefined ? (
             <div className={`h-40 flex items-center justify-center text-center rounded-2xl border ${
               isDark ? 'bg-zinc-900/50 border-zinc-800 text-zinc-600' : 'bg-slate-50 border-slate-200 text-slate-400'
             } text-[11px] font-bold uppercase tracking-[0.12em]`}>Could not load usage data.</div>
          ) : (
            <AnalyticsChart isDark={isDark} />
          )}
        </div>

        {/* RIGHT COLUMN */}
        <RightColumn
          messagesCount={`${usage?.whatsapp_messages_sent ?? 0}/${usage?.whatsapp_limit ?? 200}`}
          aiRequestsCount={`${usage?.ai_requests_made ?? 0}/${usage?.ai_limit ?? 1500}`}
          bot={bot}
          usage={usage}
          isDark={isDark}
          integrations={integrations}
        />
      </div>
    </div>
  );
}
