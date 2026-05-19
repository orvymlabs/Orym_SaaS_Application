"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export default function RevenuePage() {
  const [financeData, setFinanceData] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [f, u, p] = await Promise.all([
        apiGet("/api/admin/financials"),
        apiGet("/api/admin/users"),
        apiGet("/api/admin/plans")
      ]);
      setFinanceData(f);
      setUsers(u);
      setPlans(p);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const planPrices = plans.reduce((acc, p) => {
    acc[p.plan_name] = p.monthly_price;
    return acc;
  }, {} as Record<string, number>);

  const getYield = (plan: string) => planPrices[plan] || 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Calculating Global Revenue...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div>
        <h1 className="text-4xl font-black text-white tracking-tighter">Finance & Tiers</h1>
        <p className="text-zinc-500 font-medium mt-1">Track platform recurring revenue and subscription health</p>
      </div>

      {/* Revenue Stats */}
      {financeData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl shadow-black relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#10b981]/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-[#10b981]/10 transition-all" />
            <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Monthly Recurring Revenue</p>
            <p className="text-5xl font-black text-white mt-4 tracking-tighter">${financeData.total_revenue} <span className="text-xl text-zinc-700">/MO</span></p>
            <p className="text-[10px] font-bold text-zinc-500 mt-4">Total platform volume</p>
          </div>
          
          {plans.slice(1, 3).map(plan => (
            <div key={plan.id} className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl shadow-black">
              <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{plan.plan_name.toUpperCase()} Subscriptions</p>
              <p className="text-4xl font-black text-white mt-4">{users.filter(u => u.plan === plan.plan_name).length}</p>
              <p className="text-[10px] font-bold text-amber-500 mt-4">${financeData.revenue_by_plan[plan.plan_name] || 0} in recurring yield</p>
            </div>
          ))}
        </div>
      )}

      {/* Subscriptions Table */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden">
        <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
          <h3 className="text-xl font-black text-white tracking-tight">Subscription Registry</h3>
          <span className="btn-pill btn-pill-active py-1 !text-[9px] border-none shadow-lg shadow-[#6c4ef2]/20">{users.length} ENTRIES</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-black/20">
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Subscriber</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Service Tier</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Auth Level</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em] text-right">Yield</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {users.map(user => (
                <tr key={user.id} className="transition-all hover:bg-white/5 group">
                  <td className="px-10 py-6">
                    <p className="font-bold text-white text-sm tracking-tight">{user.email}</p>
                  </td>
                  <td className="px-10 py-6">
                    <span className={`btn-pill py-1 !text-[9px] ${
                      user.plan !== 'free' ? 'btn-pill-active shadow-lg shadow-[#6c4ef2]/20' : 'btn-pill-inactive !border-zinc-800'
                    }`}>
                      {user.plan}
                    </span>
                  </td>
                  <td className="px-10 py-6 text-[11px] font-black uppercase tracking-widest text-zinc-600">
                    {user.role}
                  </td>
                  <td className="px-10 py-6 text-right">
                    <span className="font-black text-white">${getYield(user.plan)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {users.length === 0 && (
          <div className="text-center py-32 opacity-20 grayscale">
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Zero Recurring Revenue Registry</p>
          </div>
        )}
      </div>
    </div>
  );
}
