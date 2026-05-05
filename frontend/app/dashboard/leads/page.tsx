"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const { isDark } = useTheme();

  useEffect(() => {
    api("/api/leads?limit=100")
      .then(setLeads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const getInterestBadge = (interestLevel: string, requestedContact: boolean) => {
    if (requestedContact) {
      return (
        <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wide rounded-full ${isDark ? "bg-red-500/20 text-red-400" : "bg-red-100 text-red-700"}`}>
          🔥 Urgent: Follow-up
        </span>
      );
    }
    if (interestLevel === "high") {
      return (
        <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wide rounded-full ${isDark ? "bg-white text-black" : "bg-orange-100 text-orange-700"}`}>
          High Potential
        </span>
      );
    }
    if (interestLevel === "medium") {
      return (
        <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wide rounded-full ${isDark ? "bg-zinc-800 text-zinc-400" : "bg-slate-100 text-slate-700"}`}>
          Engaged
        </span>
      );
    }
    return (
      <span className={`px-3 py-1 text-[10px] font-black uppercase tracking-wide rounded-full ${isDark ? "bg-zinc-900 text-zinc-600" : "bg-slate-100 text-slate-500"}`}>
        Qualified
      </span>
    );
  };

  const handleExport = () => {
    const csvContent = "data:text/csv;charset=utf-8,"
      + "Name,Phone,Engagement,Last Message,Updated\n"
      + leads.map(l => `"${l.name || 'Unknown'}","${l.phone}","${l.interest_level}","${l.last_message?.replace(/"/g, '""') || ''}","${l.updated_at}"`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "orvym-nexus-leads.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDelete = async (leadId: number, leadName: string) => {
    if (!confirm(`Are you sure you want to delete lead "${leadName || 'Unknown'}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await api(`/api/leads/${leadId}`, { method: "DELETE" });
      setLeads(leads.filter(l => l.id !== leadId));
      alert("Lead deleted successfully");
    } catch (error) {
      console.error("Failed to delete lead:", error);
      alert("Failed to delete lead. Please try again.");
    }
  };

  const filteredLeads = leads.filter(lead => 
    (lead.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
     lead.phone?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className={`text-4xl font-black tracking-tighter mb-2 ${isDark ? "text-white" : "text-slate-900"}`}>Leads</h1>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-medium`}>Manage potential customer inquiries and engagement levels.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="search-input-wrapper w-64">
            <svg className="search-input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            <input 
              type="text" 
              placeholder="Search contacts..." 
              className="search-input-field !py-2.5 !text-xs"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button onClick={handleExport} className="btn-secondary !py-2.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            Export
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-24">
          <div className={`w-12 h-12 border-4 rounded-full animate-spin ${isDark ? "border-zinc-800" : "border-slate-100"}`} style={{ borderTopColor: isDark ? 'white' : 'black' }} />
        </div>
      ) : (
        <div className={`rounded-[2.5rem] border overflow-hidden ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-xl shadow-slate-200/50"}`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className={`${isDark ? "bg-zinc-900/50" : "bg-slate-50/50"} border-b ${isDark ? "border-zinc-800" : "border-slate-100"}`}>
                <tr>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Engagement</th>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Name</th>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Phone</th>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Last Message</th>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Updated</th>
                  <th className={`px-8 py-6 text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Actions</th>
                </tr>
              </thead>
              <tbody className={`divide-y ${isDark ? "divide-zinc-800" : "divide-slate-100"}`}>
                {filteredLeads
                  .map((lead) => (
                  <tr key={lead.id} className={`transition-all duration-300 ${isDark ? "hover:bg-white/5" : "hover:bg-slate-50"}`}>
                    <td className="px-8 py-6">
                      {getInterestBadge(lead.interest_level, lead.requested_contact)}
                    </td>
                    <td className={`px-8 py-6 font-black text-sm ${isDark ? "text-white" : "text-slate-900"}`}>{lead.name || "Unknown"}</td>
                    <td className={`px-8 py-6 font-mono text-[11px] ${isDark ? "text-zinc-400" : "text-slate-600"}`}>{lead.phone}</td>
                    <td className={`px-8 py-6 max-w-xs truncate font-medium text-sm ${isDark ? "text-zinc-300" : "text-slate-600"}`}>{lead.last_message}</td>
                    <td className={`px-8 py-6 text-[10px] font-black uppercase tracking-wider ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                      {lead.updated_at ? new Date(lead.updated_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-8 py-6">
                      <button
                        onClick={() => handleDelete(lead.id, lead.name)}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${isDark ? "bg-red-500/10 text-red-400 hover:bg-red-500/20" : "bg-red-50 text-red-600 hover:bg-red-100"}`}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredLeads.length === 0 && (
            <div className={`text-center py-32 font-bold ${isDark ? "text-zinc-800" : "text-slate-400"}`}>
              <svg className={`w-24 h-24 mx-auto mb-6 ${isDark ? "text-zinc-900" : "text-slate-100"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
              No leads detected.<br/>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] mt-2 block">Matches will appear here.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
