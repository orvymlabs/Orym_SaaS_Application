"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";

import Topbar from "@/components/dashboard/Topbar";
import StatCards from "@/components/dashboard/StatCards";
import AnalyticsChart from "@/components/dashboard/AnalyticsChart";
import RightColumn from "@/components/dashboard/RightColumn";

import "@/components/dashboard/dashboard.css";

export default function DashboardPage() {
  const [bot, setBot] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const { isDark } = useTheme();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [botData, leadsData, usageData, convData] = await Promise.all([
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
        ]);

        setBot(botData);
        setLeads(leadsData);
        setUsage(usageData);
        setConversations(convData); 
      } catch (error) {
        console.error("Dashboard fetch error:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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
  return (
    <div className="main">
      <Topbar
        isDark={isDark}
        botStatus={bot?.status ?? false}
        userName={bot?.name ?? "User"}
      />

      <div className="dashboard-content">
        {/* LEFT COLUMN */}
        <div className="col-left">
          <StatCards
            messagesCount={`${usage?.whatsapp_messages_sent ?? 0}/${usage?.whatsapp_limit ?? 200}`}
            contactsCount={leads.length}
            aiRequestsCount={`${usage?.ai_requests_made ?? 0}/${usage?.ai_limit ?? 1500}`}
            isDark={isDark}
          />

          {/* AnalyticsChart is assumed to fetch its own data or use context, as per instructions. */}
          <AnalyticsChart isDark={isDark} />
        </div>

        {/* RIGHT COLUMN */}
        <RightColumn
          messagesCount={`${usage?.whatsapp_messages_sent ?? 0}/${usage?.whatsapp_limit ?? 200}`}
          aiRequestsCount={`${usage?.ai_requests_made ?? 0}/${usage?.ai_limit ?? 1500}`}
          bot={bot}
          usage={usage}
          isDark={isDark}
        />
      </div>
    </div>
  );
}
