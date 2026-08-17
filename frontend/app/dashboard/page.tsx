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
      <div className="p-8">
        <div className="animate-pulse space-y-8">
          <div className="h-8 w-64 bg-slate-200 rounded-lg" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-slate-100 rounded-[2rem]" />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 h-96 bg-slate-100 rounded-[3rem]" />
            <div className="h-96 bg-slate-100 rounded-[3rem]" />
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
          <a href="/dashboard/settings" className="block mb-6 no-underline">
            <div className={`rounded-[2rem] p-6 border-2 transition-all hover:scale-[1.02] cursor-pointer ${
              isDark
                ? 'bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-800/50 hover:border-blue-700'
                : 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200 hover:border-blue-300'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${isDark ? 'bg-blue-900/50' : 'bg-blue-100'}`}>
                    <svg className={`w-6 h-6 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                  </div>
                  <div>
                    <p className={`text-xs font-bold uppercase tracking-wide ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Active Bot Mode
                    </p>
                    <p className={`text-lg font-bold mt-1 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      {getBotModeLabel(bot?.mode || "default")}
                    </p>
                  </div>
                </div>
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${isDark ? 'bg-green-900/30 text-green-400' : 'bg-green-100 text-green-700'}`}>
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                  <span className="text-xs font-bold">Active</span>
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
             <div className="h-full flex items-center justify-center text-center text-zinc-500 text-sm">Could not load usage data.</div>
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
