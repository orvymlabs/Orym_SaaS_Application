"use client";
import React from 'react';

interface LeadsTableProps {
  isDark?: boolean;
}

export default function LeadsTable({ isDark }: LeadsTableProps) {
  // Dummy data - replace with actual API fetched data
  const leads = [
    { id: 1, name: "Ali Khan", phone: "+92 300 1234567", query: "Pricing Inquiry", status: "new", time: "2 min ago" },
    { id: 2, name: "Sara Malik", phone: "+92 301 7654321", query: "Support", status: "contacted", time: "15 min ago" },
    { id: 3, name: "Usman Raza", phone: "+92 333 9876543", query: "Sales Question", status: "qualified", time: "1 hr ago" },
  ];

  return (
    <div className="card">
      <div className="leads-header">
        <div className="card-title">
          <h3>Recent Leads (CRM)</h3>
        </div>
        <a className="view-all" href="#">
          View All Leads
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="14" height="14">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </a>
      </div>

      <div className="leads-table-container">
        <table className="leads-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Query / Intent</th>
              <th>Status</th>
              <th>Time</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <div className="lead-name-cell">
                    <div className="lead-avatar" style={{ background: 'linear-gradient(135deg,#6c4ef2,#a78bfa)' }}>
                      {lead.name.charAt(0)}{lead.name.split(' ')[1]?.charAt(0) || ''}
                    </div>
                    {lead.name}
                  </div>
                </td>
                <td style={{ color: '#64748b' }}>{lead.phone}</td>
                <td>{lead.query}</td>
                <td>
                  <span className={`status-badge status-${lead.status}`}>
                    {lead.status.charAt(0).toUpperCase() + lead.status.slice(1)}
                  </span>
                </td>
                <td style={{ color: '#94a3b8' }}>{lead.time}</td>
                <td>
                  <div className="action-btns">
                    <button className="action-btn wa">
                      <svg viewBox="0 0 24 24" fill="#25d366" width="13" height="13">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
                      </svg>
                    </button>
                    <button className="action-btn">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                    </button>
                    <button className="action-btn">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /><circle cx="5" cy="12" r="1" /></svg>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
