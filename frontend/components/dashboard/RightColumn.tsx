"use client";
import React from 'react';
import Link from 'next/link';

interface RightColumnProps {
  messagesCount: string;
  aiRequestsCount: string;
  bot?: any;
  usage?: any;
  isDark?: boolean;
  integrations?: any;
}

export default function RightColumn({ messagesCount, aiRequestsCount, bot, usage, isDark, integrations }: RightColumnProps) {
  const [msgSent, msgLimit] = messagesCount.split('/').map(s => parseInt(s.replace(/,/g, '')) || 0);
  const msgPercent = msgLimit > 0 ? (msgSent / msgLimit) * 100 : 0;

  const whatsappStatus = integrations?.whatsapp_number ? "Connected" : "Not Connected";
  const connectedNumber = integrations?.whatsapp_number || "Not Connected";
  const phoneNumberId = integrations?.phone_number_id || "Not Set";

  const getBotModeLabel = (mode: string) => {
    if (mode === "default") return "Customize Flow";
    if (mode === "predefined") return "Keyword Trigger";
    if (mode === "ai") return "Dynamic AI";
    return "Not Set";
  };

  const getBotModeDescription = (mode: string) => {
    if (mode === "default") return "Template-based responses with custom flows";
    if (mode === "predefined") return "Keyword-triggered automated replies";
    if (mode === "ai") return "AI-powered dynamic conversations";
    return "No mode configured";
  };

  const automationFlows = [
    {
      id: 'whatsapp',
      name: "WhatsApp Integration",
      status: integrations?.whatsapp_number ? "Active" : "Inactive",
      detail: integrations?.whatsapp_number ? `Connected: ${integrations.whatsapp_number}` : "Not connected"
    },
    {
      id: 'woocommerce',
      name: "WooCommerce Sync",
      status: integrations?.woocommerce_url ? "Active" : "Inactive",
      detail: integrations?.woocommerce_url ? "Store connected" : "Not configured"
    },
    {
      id: 'bot',
      name: "Bot Engine",
      status: bot?.status ? "Active" : "Inactive",
      detail: bot?.status ? "Responding to messages" : "Bot is offline"
    },
  ];

  const activeCount = automationFlows.filter(f => f.status === "Active").length;

  return (
    <div className="col-right">
      {/* WHATSAPP ENGINE */}
      <div className="card">
        <div className="usage-header">
          <div className="usage-title">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
              isDark ? 'bg-emerald-500/10' : 'bg-emerald-50'
            }`}>
              <svg viewBox="0 0 24 24" fill="#25d366" width="18" height="18">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884"></path>
              </svg>
            </div>
            <div>
              <h3>WhatsApp Engine</h3>
            </div>
          </div>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
            integrations?.whatsapp_number
              ? isDark ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
              : isDark ? 'bg-zinc-800 text-zinc-500 border border-zinc-700' : 'bg-slate-100 text-slate-500 border border-slate-200'
          }`}>{whatsappStatus}</span>
        </div>

        <div className="usage-stats">
          <div className="usage-stat-row">
            <span className="usage-stat-key">Connected Number</span>
            <span className="usage-stat-val">
              {connectedNumber}
              <button className={`inline-flex p-1 rounded transition-colors ${
                isDark ? 'text-zinc-600 hover:text-violet-400' : 'text-slate-400 hover:text-violet-600'
              }`}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path></svg>
              </button>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">Phone Number ID</span>
            <span className="usage-stat-val text-xs font-mono">
              {integrations?.phone_number_id ? integrations.phone_number_id.slice(0, 15) + '...' : 'Not Set'}
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">Bot Status</span>
            <span className="usage-stat-val">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                bot?.status
                  ? isDark ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15' : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                  : isDark ? 'bg-red-500/10 text-red-400 border border-red-500/15' : 'bg-red-50 text-red-600 border border-red-200'
              }`}>
                {bot?.status ? 'Active' : 'Inactive'}
              </span>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className="usage-stat-key">Message Quota</span>
            <div className="w-full">
              <div className="flex justify-between items-center mb-1.5">
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
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
              isDark ? 'bg-violet-500/10' : 'bg-violet-50'
            }`}>
              <svg viewBox="0 0 24 24" fill="none" stroke={isDark ? '#a78bfa' : '#6c4ef2'} strokeWidth="2" className="w-[18px] h-[18px]"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <div>
              <h3>Automation Engine</h3>
            </div>
          </div>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
            isDark ? 'bg-violet-500/10 text-violet-400 border border-violet-500/15' : 'bg-violet-50 text-violet-600 border border-violet-200'
          }`}>{activeCount} Active</span>
        </div>

        {/* Active Bot Mode */}
        <div className={`mx-4 mt-4 rounded-xl p-4 border transition-colors ${
          isDark
            ? 'bg-violet-500/[0.04] border-violet-500/10'
            : 'bg-violet-50/50 border-violet-200/50'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-[9px] font-bold uppercase tracking-[0.12em] ${isDark ? 'text-zinc-500' : 'text-slate-400'}`}>
              Active Bot Mode
            </span>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_6px_rgba(16,185,129,0.5)]"></div>
              <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-500">Live</span>
            </div>
          </div>
          <h4 className={`text-sm font-bold mb-0.5 ${isDark ? 'text-white' : 'text-slate-900'}`}>
            {getBotModeLabel(bot?.mode || "default")}
          </h4>
          <p className={`text-[11px] font-medium ${isDark ? 'text-zinc-500' : 'text-slate-400'}`}>
            {getBotModeDescription(bot?.mode || "default")}
          </p>
        </div>

        <div className="automation-list">
          {automationFlows.map(flow => (
            <div key={flow.id} className="automation-item">
              <div className="automation-info">
                <h4>{flow.name}</h4>
                <p className="text-[10px]">{flow.detail}</p>
              </div>
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${flow.status === 'Active' ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)]' : 'bg-zinc-600'}`}></div>
            </div>
          ))}
        </div>

        <Link href="/dashboard/settings" className={`mx-4 mb-4 flex items-center justify-center gap-2 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-[0.1em] transition-all duration-200 no-underline ${
          isDark
            ? 'bg-violet-500/10 text-violet-300 border border-violet-500/15 hover:bg-violet-500/15 hover:border-violet-500/25'
            : 'bg-violet-50 text-violet-700 border border-violet-200 hover:bg-violet-100 hover:border-violet-300'
        }`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Configure Bot Engine
        </Link>
      </div>
    </div>
  );
}
