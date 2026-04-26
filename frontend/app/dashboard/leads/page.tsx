"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/leads")
      .then(setLeads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-12 max-w-7xl mx-auto">
      <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">Leads</h1>
      <p className="text-slate-500 font-medium mb-8">Manage your customer contacts.</p>
      
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Name</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Phone</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Lead Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {leads
                .filter(lead => {
                  const msg = lead.last_message?.toLowerCase() || "";
                  const ignore = ['hi', 'hello', 'hey', 'oaky', 'ok', 'yes', 'thanks', 'thank you'];
                  return msg && !ignore.includes(msg) && msg.length > 3;
                })
                .map((lead) => (
                <tr key={lead.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-8 py-6 font-bold text-slate-900">{lead.name || "Unknown"}</td>
                  <td className="px-8 py-6 font-mono text-slate-600">{lead.phone}</td>
                  <td className="px-8 py-6 text-slate-600">{lead.last_message}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {leads.length === 0 && (
            <div className="text-center py-20 text-slate-400 font-bold">No leads found yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
