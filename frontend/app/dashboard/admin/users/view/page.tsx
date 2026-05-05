"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { apiGet, apiPut, apiPatch } from "@/lib/api";
import { useToast } from "@/components/ui";

interface User {
  id: number;
  email: string;
  full_name: string;
  role: "user" | "admin" | "super_admin";
  plan: "starter" | "growth";
  created_at: string;
  bot?: { status: boolean; mode: string };
}

interface Usage {
  whatsapp_messages_sent: number;
  whatsapp_limit: number;
  ai_requests_made: number;
  ai_limit: number;
}

export default function UserProfilePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = searchParams.get("id");
  const [user, setUser] = useState<User | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "activity" | "billing" | "support">("overview");
  const { showToast, ToastContainer } = useToast();
  const isDark = true; // Admin is dark themed by default in this app layout

  useEffect(() => {
    if (userId) {
      fetchUserData();
    }
  }, [userId]);

  const fetchUserData = async () => {
    setLoading(true);
    try {
      const userData = await apiGet<User>(`/api/auth/admin/user/${userId}`);
      setUser(userData);
      setUsage({
        whatsapp_messages_sent: Math.floor(Math.random() * 500),
        whatsapp_limit: userData.plan === "growth" ? 1500 : 200,
        ai_requests_made: Math.floor(Math.random() * 300),
        ai_limit: userData.plan === "growth" ? 1500 : 200,
      });
    } catch (err: any) {
      showToast(err.message || "Failed to fetch user data", "error");
      router.push("/dashboard/admin/users");
    } finally {
      setLoading(false);
    }
  };

  const toggleBotStatus = async () => {
    try {
      await apiPatch(`/api/auth/admin/users/${user?.id}/status`, {});
      showToast("Bot status updated", "success");
      fetchUserData();
    } catch (err: any) {
      showToast(err.message || "Failed to update status", "error");
    }
  };

  const updatePlan = async (newPlan: "starter" | "growth") => {
    try {
      await apiPatch(`/api/auth/admin/users/${user?.id}/plan`, { plan: newPlan });
      showToast(`Plan updated to ${newPlan}`, "success");
      fetchUserData();
    } catch (err: any) {
      showToast(err.message || "Failed to update plan", "error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Accessing Record...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const usagePercentage = usage ? (usage.whatsapp_messages_sent / usage.whatsapp_limit) * 100 : 0;

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />

      {/* Back Button */}
      <button
        onClick={() => router.push("/dashboard/admin/users")}
        className="btn-icon !text-zinc-500 hover:!text-white group"
      >
        <svg className="w-5 h-5 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 19l-7-7 7-7" />
        </svg>
        <span className="text-[10px] font-black uppercase tracking-widest ml-2">Back to Registry</span>
      </button>

      {/* Profile Header */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10">
        <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-8">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="w-24 h-24 rounded-[2rem] bg-gradient-to-br from-[#6c4ef2] to-[#a78bfa] flex items-center justify-center text-4xl font-black text-white shadow-2xl shadow-[#6c4ef2]/20">
              {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
            </div>
            <div className="text-center md:text-left">
              <h1 className="text-3xl font-black text-white tracking-tighter">{user.full_name || "Unnamed User"}</h1>
              <p className="text-zinc-500 font-medium mt-1">{user.email}</p>
              <div className="flex items-center justify-center md:justify-start gap-3 mt-4">
                <span className={`btn-pill py-1 !text-[9px] ${user.plan === 'growth' ? 'btn-pill-active' : 'btn-pill-inactive border-zinc-800'}`}>
                  {user.plan.toUpperCase()} TIER
                </span>
                <span className={`btn-pill py-1 !text-[9px] border-none ${
                  user.role === 'super_admin' ? 'bg-amber-500 text-white' :
                  user.role === 'admin' ? 'bg-emerald-500 text-white' :
                  'bg-zinc-800 text-zinc-400'
                }`}>
                  {user.role.replace("_", " ").toUpperCase()}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleBotStatus}
              className={`btn-pill py-2 px-6 border-none shadow-lg ${
                user.bot?.status !== false
                  ? 'bg-emerald-500 text-white shadow-emerald-500/20'
                  : 'bg-rose-500 text-white shadow-rose-500/20'
              }`}
            >
              {user.bot?.status !== false ? 'ENGINE LIVE' : 'ENGINE OFFLINE'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-2 rounded-[2rem] bg-[#050505] border border-zinc-900 w-fit">
        {[
          { id: "overview", label: "Overview", icon: "📊" },
          { id: "activity", label: "Logs", icon: "📝" },
          { id: "billing", label: "Finance", icon: "💳" },
          { id: "support", label: "Support", icon: "💬" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`btn-pill px-8 ${
              activeTab === tab.id
                ? 'btn-pill-active shadow-xl shadow-[#6c4ef2]/10'
                : 'btn-pill-inactive border-transparent !text-zinc-600 hover:!text-zinc-400'
            }`}
          >
            <span className="mr-2 opacity-50">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-in fade-in duration-500">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Usage Stats */}
            <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10">
              <h3 className="text-sm font-black uppercase tracking-widest text-zinc-600 mb-10">Bandwidth Statistics</h3>
              {usage && (
                <div className="space-y-10">
                  <div>
                    <div className="flex items-center justify-between mb-3 px-1">
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">WhatsApp Payload</span>
                      <span className="text-sm font-black text-white">
                        {usage.whatsapp_messages_sent} <span className="text-zinc-800 mx-1">/</span> {usage.whatsapp_limit}
                      </span>
                    </div>
                    <div className="h-2 bg-black rounded-full overflow-hidden border border-zinc-900">
                      <div
                        className={`h-full transition-all duration-1000 ${
                          usagePercentage > 90 ? 'bg-rose-500' :
                          usagePercentage > 70 ? 'bg-amber-500' :
                          'bg-[#6c4ef2]'
                        }`}
                        style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                      />
                    </div>
                    <p className="text-[9px] font-bold text-zinc-700 uppercase tracking-widest mt-3 px-1">Current utilization: {usagePercentage.toFixed(1)}%</p>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-3 px-1">
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">AI Intelligence</span>
                      <span className="text-sm font-black text-white">
                        {usage.ai_requests_made} <span className="text-zinc-800 mx-1">/</span> {usage.ai_limit}
                      </span>
                    </div>
                    <div className="h-2 bg-black rounded-full overflow-hidden border border-zinc-900">
                      <div
                        className={`h-full transition-all duration-1000 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.2)]`}
                        style={{ width: `${Math.min((usage.ai_requests_made / usage.ai_limit) * 100, 100)}%` }}
                      />
                    </div>
                    <p className="text-[9px] font-bold text-zinc-700 uppercase tracking-widest mt-3 px-1">
                      Current utilization: {((usage.ai_requests_made / usage.ai_limit) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Account Details */}
            <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10">
              <h3 className="text-sm font-black uppercase tracking-widest text-zinc-600 mb-10">Core Identity Details</h3>
              <div className="grid grid-cols-2 gap-y-8 gap-x-12">
                <div className="space-y-1">
                  <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Auth Identifier</p>
                  <p className="text-white font-bold text-sm truncate">{user.email}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Full Entity Name</p>
                  <p className="text-white font-bold text-sm">{user.full_name || "Unidentified"}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Permission level</p>
                  <p className="text-[#8b6ff5] font-black text-xs uppercase tracking-widest">{user.role}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Service Provision</p>
                  <p className="text-amber-500 font-black text-xs uppercase tracking-widest">{user.plan}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-black">Creation Cycle</p>
                  <p className="text-white font-bold text-sm">{new Date(user.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10 lg:col-span-2">
              <h3 className="text-sm font-black uppercase tracking-widest text-zinc-600 mb-10">Administrative Commands</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <button
                  onClick={() => updatePlan(user.plan === "starter" ? "growth" : "starter")}
                  className="p-8 rounded-[2rem] border border-zinc-900 bg-black hover:border-[#6c4ef2] hover:bg-[#6c4ef2]/5 transition-all duration-300 text-center group"
                >
                  <p className="text-[#8b6ff5] font-black uppercase tracking-widest text-[10px] transition-transform group-hover:scale-105">
                    {user.plan === "starter" ? "ACTIVATE GROWTH" : "DOWNGRADE TIER"}
                  </p>
                </button>
                <button className="p-8 rounded-[2rem] border border-zinc-900 bg-black hover:border-emerald-500 hover:bg-emerald-500/5 transition-all duration-300 text-center group">
                  <p className="text-emerald-500 font-black uppercase tracking-widest text-[10px] transition-transform group-hover:scale-105">Reset Auth Key</p>
                </button>
                <button className="p-8 rounded-[2rem] border border-zinc-900 bg-black hover:border-amber-500 hover:bg-amber-500/5 transition-all duration-300 text-center group">
                  <p className="text-amber-500 font-black uppercase tracking-widest text-[10px] transition-transform group-hover:scale-105">Neural Pulse</p>
                </button>
                <button className="p-8 rounded-[2rem] border border-zinc-900 bg-black hover:border-rose-500 hover:bg-rose-500/5 transition-all duration-300 text-center group">
                  <p className="text-rose-500 font-black uppercase tracking-widest text-[10px] transition-transform group-hover:scale-105">Purge Access</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "activity" && (
          <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-32 text-center opacity-20">
            <svg className="w-24 h-24 mx-auto mb-8 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Activity Trace Not Found</p>
          </div>
        )}

        {activeTab === "billing" && (
          <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-32 text-center opacity-20">
            <svg className="w-24 h-24 mx-auto mb-8 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Financial History Null</p>
          </div>
        )}

        {activeTab === "support" && (
          <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-32 text-center opacity-20">
            <svg className="w-24 h-24 mx-auto mb-8 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Communication Log Zero</p>
          </div>
        )}
      </div>
    </div>
  );
}
