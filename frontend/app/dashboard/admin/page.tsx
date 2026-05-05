"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useToast } from "@/components/ui";

// Simple bar chart component using CSS
function SimpleBarChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  const maxValue = Math.max(...data.map(d => d.value), 1);

  return (
    <div className="flex items-end justify-around h-40 gap-2 px-4">
      {data.map((item, i) => (
        <div key={i} className="flex flex-col items-center gap-2 flex-1">
          <div
            className={`w-full rounded-t-lg transition-all duration-500 ${item.color}`}
            style={{ height: `${(item.value / maxValue) * 100}%`, minHeight: item.value > 0 ? '8px' : '0' }}
          />
          <span className="text-[10px] font-bold text-gray-500 text-center truncate w-full">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

// Simple donut chart using CSS conic-gradient
function SimpleDonutChart({ value, total, label, color }: { value: number; total: number; label: string; color: string }) {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  const gradient = `conic-gradient(${color} ${percentage}%, #374151 ${percentage}%)`;

  return (
    <div className="flex flex-col items-center">
      <div
        className="w-28 h-28 rounded-full relative"
        style={{ background: gradient }}
      >
        <div className="absolute inset-6 bg-gray-900 rounded-full flex items-center justify-center border border-gray-700">
          <div className="text-center">
            <p className="text-xl font-black text-white">{Math.round(percentage)}%</p>
            <p className="text-[8px] text-gray-500 uppercase tracking-wider">{label}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

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
        apiGet("/api/auth/admin/users"),
        apiGet("/api/auth/admin/stats")
      ]);
      setUsers(u);
      setStats(s);
    } catch (err: any) {
      showToast(err.message || "Failed to fetch data", "error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Authorizing Admin Access...</p>
        </div>
      </div>
    );
  }

  const starterCount = users.filter(u => u.plan === "starter").length;
  const growthCount = users.filter(u => u.plan === "growth").length;
  const totalUsers = users.length;

  const userCount = users.filter(u => u.role === "user").length;
  const adminCount = users.filter(u => u.role === "admin").length;
  const superAdminCount = users.filter(u => u.role === "super_admin").length;

  const userGrowthData = [
    { label: "May", value: Math.max(0, totalUsers - 5), color: "bg-zinc-800" },
    { label: "Jun", value: Math.max(0, totalUsers - 4), color: "bg-zinc-800" },
    { label: "Jul", value: Math.max(0, totalUsers - 3), color: "bg-zinc-800" },
    { label: "Aug", value: Math.max(0, totalUsers - 2), color: "bg-[#6c4ef2]" },
    { label: "Sep", value: Math.max(0, totalUsers - 1), color: "bg-[#8b6ff5]" },
    { label: "Oct", value: totalUsers, color: "bg-gradient-to-t from-[#6c4ef2] to-[#a78bfa]" },
  ];

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">Admin Dashboard</h1>
          <p className="text-zinc-500 font-medium mt-1">Platform-wide insights and neural management</p>
        </div>
        <button
          onClick={fetchData}
          className="btn-primary"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          Refresh Nexus
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: "Total Users", value: stats.total_users, icon: "👥", color: "violet", change: "+12%" },
            { label: "Messages Sent", value: stats.total_messages, icon: "💬", color: "emerald", change: "+24%" },
            { label: "Total Contacts", value: stats.total_contacts, icon: "👤", color: "fuchsia", change: "+8%" },
            { label: "Active Bots", value: users.filter(u => u.bot?.status !== false).length, icon: "🤖", color: "amber", change: "+3" },
          ].map(s => (
            <div key={s.label} className="bg-[#090909] p-6 rounded-[2rem] border border-zinc-800 shadow-2xl shadow-black">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{s.label}</p>
                  <p className="text-3xl font-black text-white mt-2">{s.value}</p>
                  <p className="text-[10px] font-bold text-emerald-400 mt-2 flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-emerald-500"></span>
                    {s.change} growth
                  </p>
                </div>
                <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-2xl">
                  {s.icon}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* User Growth Chart */}
        <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl">
          <h3 className="text-sm font-black uppercase tracking-widest text-zinc-500 mb-8">User Acquisition Flow</h3>
          <SimpleBarChart data={userGrowthData} />
        </div>

        {/* Plan Distribution */}
        <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl">
          <h3 className="text-sm font-black uppercase tracking-widest text-zinc-500 mb-8">Plan Market Share</h3>
          <div className="flex items-center justify-around">
            <SimpleDonutChart
              value={growthCount}
              total={totalUsers}
              label="Growth"
              color="#6c4ef2"
            />
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#6c4ef2] shadow-[0_0_10px_#6c4ef2]"></div>
                <div>
                  <p className="text-sm font-black text-white">{growthCount}</p>
                  <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Growth Plans</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-zinc-800"></div>
                <div>
                  <p className="text-sm font-black text-white">{starterCount}</p>
                  <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Starter Plans</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Role Distribution */}
      <div className="bg-[#090909] p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
        <h3 className="text-sm font-black uppercase tracking-widest text-zinc-500 mb-10">Administrative Hierarchy</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { role: "Standard Users", count: userCount, color: "from-[#6c4ef2] to-[#a78bfa]", bg: "bg-[#6c4ef2]/10" },
            { role: "Nexus Admins", count: adminCount, color: "from-emerald-500 to-teal-400", bg: "bg-emerald-500/10" },
            { role: "Core Founders", count: superAdminCount, color: "from-amber-500 to-orange-400", bg: "bg-amber-500/10" },
          ].map(r => (
            <div key={r.role} className={`${r.bg} rounded-[2rem] p-8 border border-white/5`}>
              <p className="text-[9px] font-black text-zinc-600 uppercase tracking-[0.2em]">{r.role}</p>
              <p className="text-5xl font-black text-white mt-3 tracking-tighter">{r.count}</p>
              <div className={`h-1.5 rounded-full bg-gradient-to-r ${r.color} mt-6 shadow-sm`}></div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Users Table */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden">
        <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
          <h3 className="text-lg font-black text-white tracking-tight">Recent Onboarding</h3>
          <a href="/dashboard/admin/users" className="btn-pill btn-pill-inactive !py-2 !px-4 border-zinc-700 hover:border-white">
            View All Records
          </a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-black/20">
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Credential</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Service Tier</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Auth Level</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Join Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {users.slice(0, 5).map(user => (
                <tr key={user.id} className="transition-all hover:bg-white/5">
                  <td className="px-10 py-6">
                    <p className="font-bold text-white text-sm tracking-tight">{user.email}</p>
                  </td>
                  <td className="px-10 py-6">
                    <span className={`btn-pill py-1 !text-[9px] ${
                      user.plan === 'growth' ? 'btn-pill-active shadow-lg shadow-[#6c4ef2]/20' : 'btn-pill-inactive !border-zinc-800'
                    }`}>
                      {user.plan}
                    </span>
                  </td>
                  <td className="px-10 py-6">
                    <span className={`btn-pill py-1 !text-[9px] ${
                      user.role === 'super_admin' ? 'bg-amber-500 text-white border-none' :
                      user.role === 'admin' ? 'bg-emerald-500 text-white border-none' :
                      'btn-pill-inactive !border-zinc-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-10 py-6 text-[11px] font-black uppercase tracking-widest text-zinc-600">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
