"use client";
import React from 'react';
import Link from 'next/link';

interface AutomationEngineProps {
  activeAutomationsCount: number;
  recentAutomationRules: { id: string; name: string; status: string }[]; // Example structure
  isDark?: boolean;
}

export default function AutomationEngine({ activeAutomationsCount, recentAutomationRules, isDark }: AutomationEngineProps) {
  // Theme-aware styles
  const cardStyle = isDark ? "bg-[#1a1b2e] border-zinc-800" : "bg-white border-slate-200 shadow-sm";
  const headerStyle = isDark ? "border-zinc-800" : "border-b border-slate-100";
  const textColorMuted = isDark ? "text-zinc-400" : "text-slate-500";
  const textColorLight = isDark ? "text-white" : "";
  const sectionBg = isDark ? "bg-[#1a1b2e]" : ""; // Background for the content area
  const buttonClasses = isDark ? "bg-white text-black hover:bg-zinc-200" : "bg-purple-500 text-white hover:bg-purple-600";

  // Icon colors based on theme
  const lightningIconColor = isDark ? '#a78bfa' : '#6c4ef2';

  // Placeholder for lightning icon
  const LightningIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke={lightningIconColor} stroke-width="2" className="w-5 h-5 flex-shrink-0">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );

  return (
    <div className={`card ${cardStyle}`}>
      <div className={`usage-header ${headerStyle}`}>
        <div className="usage-title">
          <LightningIcon />
          <h3>Automation Engine</h3>
        </div>
      </div>

      {/* NEW CONTENT AREA FOR DATA - removed the old training-opts section */}
      {/* Added padding and adjusted styling for the content area */}
      <div className={`automation-content p-4 ${isDark ? 'bg-[#1a1b2e]' : ''}`}> {/* Apply background */}
        <div className="automation-stat flex justify-between items-center mb-4"> {/* Added margin-bottom */}
          <span className={textColorMuted}>Active Automations:</span>
          <span className={textColorLight}>{activeAutomationsCount}</span>
        </div>
        
        <div className="recent-rules"> {/* Removed mt-4 as spacing is handled by mb-4 above */}
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
  );
}
