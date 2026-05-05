"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export default function RevenuePage() {
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const fetchSubscriptions = async () => {
    setLoading(true);
    try {
      const data = await apiGet("/api/auth/admin/subscriptions");
      setSubscriptions(data.subscriptions || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const totalMRR = subscriptions.reduce((acc, sub) => {
    return acc + (sub.plan === "growth" ? 3 : 1);
  }, 0);

  const starterCount = subscriptions.filter(s => s.plan === "starter").length;
  const growthCount = subscriptions.filter(s => s.plan === "growth").length;

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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl shadow-black relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#10b981]/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-[#10b981]/10 transition-all" />
          <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Monthly Recurring Revenue</p>
          <p className="text-5xl font-black text-white mt-4 tracking-tighter">${totalMRR} <span className="text-xl text-zinc-700">/MO</span></p>
          <p className="text-[10px] font-bold text-zinc-500 mt-4">Total platform volume</p>
        </div>
        
        <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl shadow-black">
          <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">Starter Subscriptions</p>
          <p className="text-4xl font-black text-white mt-4">{starterCount}</p>
          <p className="text-[10px] font-bold text-amber-500 mt-4">${starterCount} in recurring yield</p>
        </div>

        <div className="bg-[#090909] p-8 rounded-[2.5rem] border border-zinc-800 shadow-2xl shadow-black">
          <p className="text-[10px] font-black text-[#6c4ef2] uppercase tracking-widest">Growth Subscriptions</p>
          <p className="text-4xl font-black text-white mt-4">{growthCount}</p>
          <p className="text-[10px] font-bold text-[#8b6ff5] mt-4">${growthCount * 3} in recurring yield</p>
        </div>
      </div>

      {/* Subscriptions Table */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden">
        <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
          <h3 className="text-xl font-black text-white tracking-tight">Subscription Registry</h3>
          <span className="btn-pill btn-pill-active py-1 !text-[9px] border-none shadow-lg shadow-[#6c4ef2]/20">{subscriptions.length} ENTRIES</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-black/20">
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Subscriber</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Service Tier</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">WA Bandwidth</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">AI Bandwidth</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em] text-right">Yield</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {subscriptions.map(sub => (
                <tr key={sub.user_id} className="transition-all hover:bg-white/5 group">
                  <td className="px-10 py-6">
                    <p className="font-bold text-white text-sm tracking-tight">{sub.email}</p>
                  </td>
                  <td className="px-10 py-6">
                    <span className={`btn-pill py-1 !text-[9px] ${
                      sub.plan === 'growth' ? 'btn-pill-active shadow-lg shadow-[#6c4ef2]/20' : 'btn-pill-inactive !border-zinc-800'
                    }`}>
                      {sub.plan}
                    </span>
                  </td>
                  <td className="px-10 py-6">
                    <div className="flex items-center gap-4">
                      <div className="flex-1 h-1.5 bg-zinc-900 rounded-full overflow-hidden max-w-[120px]">
                        <div
                          className="h-full bg-[#6c4ef2] transition-all duration-1000"
                          style={{ width: `${Math.min((sub.whatsapp_messages_sent / sub.whatsapp_limit) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-black text-zinc-600 uppercase">{sub.whatsapp_messages_sent}<span className="text-zinc-800 mx-1">/</span>{sub.whatsapp_limit}</span>
                    </div>
                  </td>
                  <td className="px-10 py-6">
                    <div className="flex items-center gap-4">
                      <div className="flex-1 h-1.5 bg-zinc-900 rounded-full overflow-hidden max-w-[120px]">
                        <div
                          className="h-full bg-emerald-500 transition-all duration-1000"
                          style={{ width: `${Math.min((sub.ai_requests_made / sub.ai_limit) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-black text-zinc-600 uppercase">{sub.ai_requests_made}<span className="text-zinc-800 mx-1">/</span>{sub.ai_limit}</span>
                    </div>
                  </td>
                  <td className="px-10 py-6 text-right">
                    <span className="font-black text-white">${sub.plan === "growth" ? 3 : 1}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {subscriptions.length === 0 && (
          <div className="text-center py-32 opacity-20 grayscale">
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Zero Recurring Revenue Registry</p>
          </div>
        )}
      </div>
    </div>
  );
}
