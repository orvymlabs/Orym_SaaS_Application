"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useToast } from "@/components/ui";

export default function AdminDashboardPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { showToast, ToastContainer } = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [u, s] = await Promise.all([
        apiGet("/api/admin/users"),
        apiGet("/api/admin/stats")
      ]);
      setUsers(u);
      setStats(s);
    } catch (err: any) {
      showToast(err.message || "Failed to fetch nexus data", "error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#6c4ef2]/20 border-t-[#6c4ef2] rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Syncing Nexus Intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-5xl font-black text-white tracking-tighter uppercase italic">Nexus Core</h1>
          <p className="text-zinc-500 font-medium mt-1">Platform-wide administrative intelligence and operation oversight</p>
        </div>
        <button
          onClick={fetchData}
          className="btn-primary !bg-[#6c4ef2] shadow-2xl shadow-[#6c4ef2]/20"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          Sync Nexus
        </button>
      </div>

      {/* High-Level Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { label: "Total Agents", value: stats.total_users, desc: "Registered credentials", color: "white" },
            { label: "Active Nodes", value: stats.active_users, desc: "Paid subscribers", color: "emerald-500" },
            { label: "Signal Volume", value: stats.total_messages, desc: "Messages processed", color: "#6c4ef2" },
            { label: "Global Yield", value: `$${stats.revenue_total}`, desc: "Est. Monthly Revenue", color: "amber-500" },
          ].map((s, i) => (
            <div key={i} className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:opacity-20 transition-all" />
              <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{s.label}</p>
              <p className="text-5xl font-black text-white mt-4 tracking-tighter" style={{ color: s.color.startsWith('#') ? s.color : undefined }}>{s.value}</p>
              <p className="text-[10px] font-bold text-zinc-500 mt-4 uppercase tracking-tighter opacity-50">{s.desc}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tier Distribution & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Tier Distribution Architecture */}
        <div className="bg-[#090909] p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
          <h3 className="text-xs font-black uppercase tracking-[0.3em] text-zinc-600 ml-1 mb-10">Tier Distribution Architecture</h3>
          <div className="space-y-10">
            {stats && Object.entries(stats.plan_distribution || {}).map(([plan, count]: any) => (
              <div key={plan} className="space-y-4">
                <div className="flex justify-between items-end px-1">
                  <p className="text-xs font-black text-white uppercase tracking-widest">{plan}</p>
                  <p className="text-[10px] font-black text-zinc-500">{count} NODES — {Math.round((count / stats.total_users) * 100)}%</p>
                </div>
                <div className="h-3 bg-black rounded-full overflow-hidden border border-zinc-900 p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-[#6c4ef2] to-[#8b6ff5] rounded-full shadow-[0_0_15px_rgba(108,78,242,0.3)] transition-all duration-1000"
                    style={{ width: `${(count / stats.total_users) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden flex flex-col">
          <div className="px-10 py-8 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
            <h3 className="text-xs font-black uppercase tracking-[0.3em] text-zinc-600">Recent Onboardings</h3>
            <span className="btn-pill btn-pill-active py-1 !text-[9px] border-none">LIVE STREAM</span>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <table className="w-full text-left">
              <tbody className="divide-y divide-zinc-900">
                {stats?.recent_signups?.map((user: any) => (
                  <tr key={user.id} className="hover:bg-white/5 transition-all group">
                    <td className="px-10 py-7">
                      <p className="text-sm font-bold text-white group-hover:text-[#6c4ef2] transition-colors">{user.email}</p>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className={`w-1 h-1 rounded-full ${user.plan !== 'free' ? 'bg-emerald-500' : 'bg-zinc-700'}`}></span>
                        <p className="text-[9px] text-zinc-600 uppercase font-black tracking-widest">{user.plan} tier</p>
                      </div>
                    </td>
                    <td className="px-10 py-7 text-right">
                      <p className="text-[10px] text-zinc-500 font-black uppercase tracking-widest">
                        {new Date(user.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-[9px] text-zinc-800 font-bold mt-1 uppercase">Authentication Successful</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {!stats && !loading && (
        <div className="text-center py-32 opacity-30">
          <p className="text-[10px] font-black uppercase tracking-[0.4em]">Dashboard data unavailable</p>
          <p className="text-sm font-medium mt-2">Could not load platform statistics. Please refresh or check console for errors.</p>
        </div>
      )}
    </div>
  );
}
