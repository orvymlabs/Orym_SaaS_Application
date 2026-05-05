"use client";
import React from 'react';
import Image from 'next/image'; // Assuming Image is used for avatars/logos

// Placeholder for icons, assuming they might be imported or SVG components
const WAChatIcon = () => (
  <svg viewBox="0 0 24 24" fill="#25d366" width="20" height="20">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
  </svg>
);

const TrainingIcon = ({ icon, color, svg }) => (
  <div className="training-opt-icon" style={{ background: color }}>
    {svg}
  </div>
);

const QuickIcon = ({ icon, color, svg }) => (
  <div className={`quick-icon ${color}`} style={{ backgroundColor: color }}>
    {svg}
  </div>
);

const defaultInsights = [
  { label: "Peak Activity", value: "Friday 6PM", sub: "+32% more messages", color: "purple", valueColor: "#6c4ef2", icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>, iconBgColor: "#ede9fe" },
  { label: "Top Intent", value: "Pricing Inquiry", sub: "32% of all queries", color: "green", valueColor: "#10b981", icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>, iconBgColor: "#f0fdf4" },
  { label: "Drop-off Point", value: "Step 2 (Menu)", sub: "24% users drop here", color: "red", valueColor: "#ef4444", icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="23" y1="18" x2="17" y2="12"/><line x1="17" y1="18" x2="23" y2="12"/></svg>, iconBgColor: "#fef2f2" },
];

// Default SVG icons for Quick Actions
const quickActionIcons = {
  'Create Flow': <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>,
  'Broadcast Message': <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/></svg>,
  'Add IVR Menu': <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 8.81a19.79 19.79 0 01-3.07-8.63A2 2 0 012 0h3a2 2 0 012 1.72"/></svg>,
  'Train AI': <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  'View Conversations': <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>,
};

const quickActionColors = {
  'Create Flow': 'purple',
  'Broadcast Message': 'orange',
  'Add IVR Menu': 'red',
  'Train AI': 'blue',
  'View Conversations': 'green',
};

export default function RightColumn({
  whatsappStatus,
  whatsappNumber,
  whatsappQuota,
  aiTrainingOptions,
  quickActions,
  insightsData
}) {
  const isWhatsAppConnected = whatsappStatus === "Connected";
  const actualInsights = insightsData && insightsData.length > 0 ? insightsData : defaultInsights;

  return (
    <div className="col-right">
      {/* WHATSAPP ENGINE */}
      <div className="card">
        <div className="wa-engine-header">
          <div className="wa-engine-title">
            <WAChatIcon />
            <h3>WhatsApp Engine</h3>
          </div>
          <span className={`connected-chip ${isWhatsAppConnected ? '' : 'offline'}`}>
            {whatsappStatus || 'Disconnected'}
          </span>
        </div>

        <div className="wa-stats">
          <div className="wa-stat-row">
            <span className="wa-stat-key">Connected Number</span>
            <span className="wa-stat-val">
              {whatsappNumber || '+92 300 1234567'} {/* Placeholder */}
              <button className="copy-btn" onClick={() => navigator.clipboard.writeText(whatsappNumber || '+92 300 1234567')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              </button>
            </span>
          </div>
          <div className="wa-stat-row">
            <span className="wa-stat-key">Status</span>
            <span className="wa-stat-val"><span className={`verified-chip ${isWhatsAppConnected ? '' : 'offline'}`}>{isWhatsAppConnected ? '✓ Verified' : 'Unverified'}</span></span>
          </div>
          <div className="wa-stat-row">
            <span className="wa-stat-key">API Health</span>
            <span className="wa-stat-val"><span className="good-chip">Good ●</span></span>
          </div>
          <div className="wa-stat-row">
            <span className="wa-stat-key">Last Sync</span>
            <span className="wa-stat-val">2 mins ago {/* Placeholder */} <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12" style={{ color: '#6c4ef2' }}><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg></span>
          </div>
          <div className="wa-stat-row">
            <span className="wa-stat-key">Message Quota</span>
            <span className="wa-stat-val">
              {whatsappQuota?.sent || '1,240'} / {whatsappQuota?.limit || '5,000'}
              <span className="quota-bar"><span className="quota-fill" style={{ width: `${(whatsappQuota?.sent / whatsappQuota?.limit) * 100 || 25}%` }}></span></span>
            </span>
          </div>
        </div>

        <div className="wa-actions">
          <button className="btn-wa-primary">
            <svg viewBox="0 0 24 24" fill="#10b981" width="15" height="15"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/></svg>
            Connect New Number
          </button>
          <div className="wa-action-row">
            <button className="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              View Templates
            </button>
            <button className="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
              Message Logs
            </button>
          </div>
        </div>
      </div>

      {/* AI TRAINING */}
      <div className="card">
        <div className="ai-training-header">
          <div className="training-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <div>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: '14px', fontWeight: '700' }}>AI Training</h3>
            <p style={{ fontSize: '11px', color: '#64748b' }}>Improve AI with your business data</p>
          </div>
        </div>

        <div className="training-opts">
          {aiTrainingOptions && aiTrainingOptions.map((opt, index) => (
            <div key={index} className="training-opt">
              <TrainingIcon icon={opt.icon} color={opt.iconColor} svg={opt.svgIcon} />
              <h4>{opt.title}</h4>
              <p>{opt.description}</p>
            </div>
          ))}
        </div>

        <button className="btn-train">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Train AI Now
        </button>
      </div>

      {/* QUICK ACTIONS */}
      <div className="card">
        <div className="quick-header">
          <h3>Quick Actions</h3>
        </div>
        <div className="quick-grid">
          {quickActions && quickActions.map((action, index) => (
            <div key={index} className="quick-btn" style={action.style || {}}>
              <QuickIcon color={action.color} svg={action.svgIcon} />
              <span>{action.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
