"use client";
import React from 'react';
import Link from 'next/link';

interface LeadsTableProps {
  leads: any[];
  isDark?: boolean;
}

export default function LeadsTable({ leads, isDark }: LeadsTableProps) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <h3 className={`text-[10px] font-bold uppercase tracking-[0.12em] mb-1 ${isDark ? 'text-violet-400' : 'text-violet-600'}`}>CRM Core</h3>
          <h3 className="text-base font-bold tracking-tight">Recent Leads</h3>
        </div>
        <Link className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-[0.1em] transition-all duration-200 no-underline ${
          isDark
            ? 'bg-white/[0.03] text-zinc-400 border border-white/[0.06] hover:text-violet-300 hover:border-violet-500/20'
            : 'bg-slate-50 text-slate-600 border border-slate-200 hover:text-violet-600 hover:border-violet-200'
        }`} href="/dashboard/leads">
          View Repository
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="10" height="10">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </Link>
      </div>

      <div className="leads-table-container">
        <table className="leads-table">
          <thead>
            <tr>
              <th>Identified User</th>
              <th>Phone</th>
              <th>Primary Intent</th>
              <th>Status</th>
              <th>Last Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {leads.length > 0 ? (
              leads.slice(0, 5).map((lead) => (
                <tr key={lead.id} className="transition-all">
                  <td>
                    <div className="lead-name-cell">
                      <div className="lead-avatar" style={{ background: 'linear-gradient(135deg,#6c4ef2,#a78bfa)' }}>
                        {lead.name?.charAt(0) || 'A'}
                      </div>
                      <span className="font-bold text-xs">{lead.name || 'Anonymous'}</span>
                    </div>
                  </td>
                  <td className="font-mono text-[11px] opacity-60">{lead.phone}</td>
                  <td className="text-[11px] font-medium opacity-70">"{lead.last_message || 'No data'}"</td>
                  <td>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      lead.context?.interest_level === 'high'
                        ? isDark ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                        : isDark ? 'bg-zinc-800 text-zinc-500 border border-zinc-700' : 'bg-slate-100 text-slate-500 border border-slate-200'
                    }`}>
                      {lead.context?.interest_level === 'high' ? 'High Potential' : 'Qualified'}
                    </span>
                  </td>
                  <td className="text-[10px] font-bold uppercase tracking-wider opacity-40">{new Date(lead.created_at).toLocaleDateString()}</td>
                  <td>
                    <button className={`p-1.5 rounded-lg transition-all ${
                      isDark ? 'text-zinc-600 hover:text-emerald-400 hover:bg-emerald-500/10' : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'
                    }`}>
                      <svg viewBox="0 0 24 24" fill="#25d366" width="14" height="14">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="text-center py-20">
                  <div className={`text-[11px] font-bold uppercase tracking-[0.15em] ${isDark ? 'text-zinc-700' : 'text-slate-400'}`}>
                    No leads yet
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
