"use client";
import React from 'react';
import Link from 'next/link';

interface RightColumnProps {
  messagesCount: string;
  aiRequestsCount: string;
  bot?: any; // Added bot prop to access bot status, number, etc.
  usage?: any; // Added usage prop for quota info
  isDark?: boolean;
}

export default function RightColumn({ messagesCount, aiRequestsCount, bot, usage, isDark }: RightColumnProps) {
  // Extract values for progress bars
  const [msgSent, msgLimit] = messagesCount.split('/').map(s => parseInt(s.replace(/,/g, '')) || 0);
  const [aiSent, aiLimit] = aiRequestsCount.split('/').map(s => parseInt(s.replace(/,/g, '')) || 0);

  // WhatsApp Engine Data
  const whatsappStatus = bot?.status ? "WhatsApp Connected" : "WhatsApp Offline";
  const connectedNumber = bot?.phone_number || "+92 XXX XXX XXXX"; // Placeholder if not available

  // Theme-aware styles
  const cardStyle = isDark ? "bg-[#1a1b2e] border-zinc-800" : "bg-white border-slate-200 shadow-sm";
  const headerStyle = isDark ? "border-zinc-800" : "border-b border-slate-100";
  const textColorMuted = isDark ? "text-zinc-400" : "text-slate-500";
  const textColorLight = isDark ? "text-white" : "";
  const chipBg = isDark ? "bg-zinc-800/50 border-zinc-700" : ""; // Styling for connected/offline chips

  // Icon colors based on theme
  const purpleIconColor = isDark ? '#a78bfa' : '#6c4ef2';
  const greenIconColor = isDark ? '#4ade80' : '#10b981';
  const blueIconColor = isDark ? '#60a5fa' : '#3b82f6'; // For API Health

  // Function to handle copying text
  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // Optionally show a toast or confirmation
      console.log('Text copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  };

  return (
    <>
      {/* WHATSAPP ENGINE */}
      <div className={`card ${cardStyle}`}>
        <div className={`usage-header ${headerStyle}`}>
          <div className="usage-title">
            <svg viewBox="0 0 24 24" fill="#25d366" width="20" height="20" className="w-5 h-5 flex-shrink-0">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884"></path>
            </svg>
            <h3>WhatsApp Engine</h3>
          </div>
          {/* Using a span with specific styling for the green badge */}
          <span className={`status-badge ${isDark ? "bg-green-900/30 text-green-400 border-green-700" : "bg-green-100 text-green-700 border-green-200"} ${chipBg}`}>
            {whatsappStatus}
          </span>
        </div>

        <div className="usage-stats">
          <div className="usage-stat-row">
            <span className={`usage-stat-key ${textColorMuted}`}>Connected Number</span>
            <span className={`usage-stat-val ${textColorLight} flex items-center gap-1`}>
              {connectedNumber}
              <button className="copy-btn p-1 rounded-md hover:bg-gray-700/30" onClick={() => handleCopyText('+92 300 1234567')}>
                <svg viewBox="0 0 24 24" fill="none" stroke={isDark ? "#94a3b8" : "currentColor"} stroke-width="2" width="12" height="12">
                  <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                </svg>
              </button>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className={`usage-stat-key ${textColorMuted}`}>API Health</span>
            <span className={`usage-stat-val ${textColorMuted}`}>
              <span className={`status-badge ${isDark ? "bg-green-900/30 text-green-400 border-green-700" : "bg-green-100 text-green-700 border-green-200"}`}>
                Grade A ●
              </span>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className={`usage-stat-key ${textColorMuted}`}>Last Sync</span>
            <span className={`usage-stat-val ${textColorLight} flex items-center gap-1`}>
              Just now
              <svg viewBox="0 0 24 24" fill="none" stroke={isDark ? "#9ca3af" : "currentColor"} stroke-width="2" width="12" height="12">
                <path d="M1 4v6h6M23 20v-6h-6"/>
                <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/>
              </svg>
            </span>
          </div>
          <div className="usage-stat-row">
            <span className={`usage-stat-key ${textColorMuted}`}>Message Quota</span>
            <span className={`usage-stat-val ${textColorLight}`}>
              {messagesCount}
              <span className={`quota-bar ${isDark ? "bg-zinc-800" : "bg-slate-200"} `}>
                <span className={`quota-fill ${isDark ? "bg-white" : "bg-blue-600"}`} style={{ width: `${Math.min(msgPercent, 100)}%` }}></span>
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* AUTOMATION ENGINE */}
      <div className={`card ${cardStyle}`}>
        <div className={`usage-header ${headerStyle}`}>
          <div className="usage-title">
            <svg viewBox="0 0 24 24" fill="none" stroke={purpleIconColor} stroke-width="2" className="w-5 h-5 flex-shrink-0">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <h3>Automation Engine</h3>
          </div>
        </div>

        {/* NEW CONTENT AREA FOR DATA - removed the old training-opts section */}
        <div className="automation-content p-4"> {/* Added padding */}
          <div className="automation-stat flex justify-between items-center mb-4"> {/* Added margin-bottom */}
            <span className={textColorMuted}>Active Automations:</span>
            <span className={textColorLight}>{activeAutomationsCount}</span>
          </div>
          
          <div className="recent-rules"> {/* Added margin top from previous thought block */}
            <h4 className={`text-sm font-bold ${isDark ? "text-white" : "text-slate-900"} mb-2`}>Recent Rules</h4> {/* Ensure text color and add margin */}
            {recentAutomationRules.length > 0 ? (
              <ul className="list-disc list-inside mt-2 space-y-1"> {/* Added list styling and spacing */}
                {recentAutomationRules.map(rule => (
                  <li key={rule.id} className={`${isDark ? "text-zinc-300" : "text-slate-700"} text-xs`}>
                    {rule.name} ({rule.status})
                  </li>
                ))}
              </ul>
            ) : (
              <p className={`${textColorMuted} text-sm`}>No recent rules found.</p>
            )}
          </div>
        </div>
        {/* END NEW CONTENT AREA */}

        <Link href="/dashboard/automations" className={`btn-train ${isDark ? "bg-white text-black hover:bg-zinc-200" : "bg-purple-500 text-white hover:bg-purple-600"}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Manage Automations
        </Link>
      </div>
    </>
  );
}
