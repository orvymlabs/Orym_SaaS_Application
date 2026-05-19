"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface AuditLog {
  id: number;
  timestamp: string;
  user: string;
  action: string;
  target: string;
  details: any;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await apiGet("/api/admin/audit");
      setLogs(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Retrieving Neural Audit Trails...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">Audit Trails</h1>
          <p className="text-zinc-500 font-medium mt-1">Immutable record of administrative intelligence and actions</p>
        </div>
        <button
          onClick={fetchLogs}
          className="btn-primary"
        >
          Refresh Logs
        </button>
      </div>

      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden">
        <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
          <h3 className="text-xl font-black text-white tracking-tight">System Event Stream</h3>
          <span className="btn-pill btn-pill-inactive py-1 !text-[9px] border-zinc-700">{logs.length} EVENTS LOGGED</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-black/20">
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Timestamp</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Operator</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Action Protocol</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Target Entity</th>
                <th className="px-10 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {logs.map(log => (
                <tr key={log.id} className="transition-all hover:bg-white/5 group">
                  <td className="px-10 py-6">
                    <p className="text-[11px] font-black text-zinc-500 font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </td>
                  <td className="px-10 py-6">
                    <p className="font-bold text-white text-sm tracking-tight">{log.user}</p>
                  </td>
                  <td className="px-10 py-6">
                    <span className={`btn-pill py-1 !text-[9px] border-none ${
                      log.action.includes('delete') ? 'bg-rose-500 text-white' :
                      log.action.includes('create') ? 'bg-emerald-500 text-white' :
                      log.action.includes('update') ? 'bg-amber-500 text-white' :
                      'bg-zinc-800 text-zinc-400'
                    }`}>
                      {log.action.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-10 py-6">
                    <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">{log.target}</p>
                  </td>
                  <td className="px-10 py-6">
                    <div className="max-w-xs truncate overflow-hidden">
                      <pre className="text-[9px] text-zinc-600 font-mono">
                        {JSON.stringify(log.details)}
                      </pre>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {logs.length === 0 && (
          <div className="text-center py-32 opacity-20 grayscale">
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">Zero System Events Detected</p>
          </div>
        )}
      </div>
    </div>
  );
}
