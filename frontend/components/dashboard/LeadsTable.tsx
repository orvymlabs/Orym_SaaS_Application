"use client";
import React from 'react';
import Link from 'next/link';

interface LeadsTableProps {
  leads: any[];
  isDark?: boolean;
}

export default function LeadsTable({ leads, isDark }: LeadsTableProps) {
  return (
    <div className="card shadow-2xl">
      <div className="leads-header p-8 border-b dark:border-zinc-800 flex items-center justify-between">
        <div className="card-title">
          <h3 className="font-black uppercase tracking-widest text-[10px] text-[#6c4ef2] mb-1">CRM Core</h3>
          <h3 className="text-xl font-black tracking-tight">Recent Leads</h3>
        </div>
        <Link className="btn-secondary !py-2 !px-4 !text-[10px] uppercase tracking-widest" href="/dashboard/leads">
          View Repository
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12" className="ml-2">
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
                <tr key={lead.id} className="transition-all hover:bg-zinc-50 dark:hover:bg-zinc-900/40">
                  <td>
                    <div className="lead-name-cell">
                      <div className="lead-avatar" style={{ background: 'linear-gradient(135deg,#6c4ef2,#a78bfa)' }}>
                        {lead.name?.charAt(0) || 'A'}
                      </div>
                      <span className="font-black text-xs uppercase tracking-tight">{lead.name || 'Anonymous'}</span>
                    </div>
                  </td>
                  <td className="font-mono text-[11px] opacity-70">{lead.phone}</td>
                  <td className="text-xs font-medium opacity-80 italic">"{lead.last_message || 'No data'}"</td>
                  <td>
                    <span className={`badge ${lead.context?.interest_level === 'high' ? 'badge-success' : 'bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-400'}`}>
                      {lead.context?.interest_level === 'high' ? 'High Potential' : 'Qualified'}
                    </span>
                  </td>
                  <td className="text-[10px] font-bold uppercase tracking-wide opacity-50">{new Date(lead.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="action-btns">
                      <button className="btn-icon">
                        <svg viewBox="0 0 24 24" fill="#25d366" width="16" height="16">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="text-center py-24 font-black uppercase tracking-widest text-[10px] opacity-30">Void Leads</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
