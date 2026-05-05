"use client";
import React from 'react';
import Link from 'next/link';

interface RightColumnProps {
  messagesCount: string;
  aiRequestsCount: string;
  bot?: any;
  usage?: any;
  isDark?: boolean;
}

export default function RightColumn({ messagesCount, aiRequestsCount, bot, usage, isDark }: RightColumnProps) {
  // Extract values for progress bars
  const [msgSent, msgLimit] = messagesCount.split('/').map(s => parseInt(s.replace(/,/g, '')) || 0);
  const msgPercent = msgLimit > 0 ? (msgSent / msgLimit) * 100 : 0;
  
  // WhatsApp Engine Data
  const whatsappStatus = bot?.status ? "Connected" : "Offline";
  const connectedNumber = bot?.phone_number || "+92 300 1234567";

  // Automation flows from existing system templates
  const automationFlows = [
    { id: 'greeting', name: "Welcome Greeting", status: "Active" },
    { id: 'menu', name: "Main Menu", status: "Active" },
    { id: 'order', name: "Order Form", status: bot?.mode === 'default' ? "Active" : "Inactive" },
    { id: 'ai', name: "AI Brain", status: bot?.mode === 'ai' ? "Active" : "Inactive" }
  ];

  const activeCount = automationFlows.filter(f => f.status === "Active").length;

  return (
    <div className="col-right">
      {/* WHATSAPP ENGINE */}
      <div className="card">
        <div className="usage-header">
          <div className="usage-title">
            <svg viewBox="0 0 24 24" fill="#25d366" width="20" height="20" className="w-5 h-5 flex-shrink-0">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884"></path>
            </svg>
            <h3>WhatsApp Engine</h3>
          </div>
          <span className={`btn-pill py-1 !text-[9px] ${bot?.status ? 'btn-pill-active' : 'btn-pill-inactive'}`}>{whatsappStatus}</span>
        </div>

        <div className="usage-stats">
          <div className="usage-stat-row">
            <span className="usage-stat-key">Connected Number</span>
            <span className="usage-stat-val">
              {connectedNumber}
              <button className="btn-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path></svg>
              </button>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">API Health</span>
            <span className="usage-stat-val">
              <span className="badge badge-success !rounded-full !px-3">Grade A ●</span>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">Last Sync</span>
            <span className="usage-stat-val">
              Just now
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12" className="text-[#6c4ef2]"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">Message Quota</span>
            <div className="w-full">
              <div className="flex justify-between items-center mb-1">
                <span className="usage-stat-val">{messagesCount}</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${Math.min(msgPercent, 100)}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AUTOMATION ENGINE */}
      <div className="card">
        <div className="usage-header">
          <div className="usage-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="#6c4ef2" stroke-width="2" className="w-5 h-5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <h3>Automation Engine</h3>
          </div>
          <span className="btn-pill btn-pill-active py-1 !text-[9px]">{activeCount} Active</span>
        </div>

        <div className="automation-list">
          {automationFlows.map(flow => (
            <div key={flow.id} className="automation-item">
              <div className="automation-info">
                <h4>{flow.name}</h4>
                <p>{flow.status}</p>
              </div>
              <div className={`insight-dot ${flow.status === 'Active' ? 'bg-green-500' : 'bg-zinc-500'}`}></div>
            </div>
          ))}
        </div>

        <Link href="/dashboard/settings" className="btn-primary m-4 !py-2.5 !text-[11px] uppercase tracking-widest">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Manage Automations
        </Link>
      </div>
    </div>
  );
}
