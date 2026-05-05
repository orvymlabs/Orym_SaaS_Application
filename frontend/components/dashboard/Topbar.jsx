"use client";
import React from 'react';

export default function Topbar({ user, botStatus }) {
  const { name, avatar } = user || {};
  const isWhatsAppConnected = botStatus === "online"; // Assuming 'online' means connected and active

  return (
    <header className="topbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button className="mobile-menu-btn" onClick={() => {/* Logic to open sidebar */}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div className="topbar-left">
          <h1>Dashboard</h1>
          <p>Welcome back, {name || 'User'} 👋</p>
        </div>
      </div>
      <div className="topbar-right">
        <div className={`wa-chip ${isWhatsAppConnected ? 'connected' : 'disconnected'}`}>
          <svg viewBox="0 0 24 24" fill={isWhatsAppConnected ? "#25d366" : "#9ca3af"} width="15" height="15">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"></path>
          </svg>
          WhatsApp {isWhatsAppConnected ? 'Connected' : 'Disconnected'}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11" style={{ color: '#94a3b8' }}>
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
        <button className="notif-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"></path>
          </svg>
          <span className="notif-badge">3</span> {/* Placeholder for actual notification count */}
        </button>
        <div className="user-chip">
          <div className="user-avatar">{avatar || name?.charAt(0) || 'U'}</div>
          <div className="user-info">
            <h4>{name || 'User'}</h4>
            <p>Founder Mode</p> {/* Placeholder for dynamic user role */}
          </div>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12" style={{ color: '#94a3b8' }}>
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
      </div>
    </header>
  );
}
