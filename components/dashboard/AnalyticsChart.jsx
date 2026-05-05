"use client";
import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

interface AnalyticsChartProps {
  isDark?: boolean;
}

export default function AnalyticsChart({ isDark }: AnalyticsChartProps) {
  const chartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = chartRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const newChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: ['12 May', '13 May', '14 May', '15 May', '16 May', '17 May', '18 May'],
            datasets: [
              {
                label: 'Messages',
                data: [280, 320, 310, 410, 380, 460, 430],
                borderColor: '#6c4ef2',
                backgroundColor: 'rgba(108,78,242,0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#6c4ef2',
              },
              {
                label: 'Leads',
                data: [100, 130, 120, 160, 140, 190, 175],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.06)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#10b981',
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'white',
                titleColor: '#0f172a',
                bodyColor: '#64748b',
                borderColor: '#e8eaf0',
                borderWidth: 1,
                padding: 10,
                boxPadding: 4,
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, color: '#94a3b8' },
                border: { display: false },
              },
              y: {
                grid: { color: '#f0f2f8' },
                ticks: { font: { size: 10 }, color: '#94a3b8', maxTicksLimit: 6 },
                border: { display: false },
                beginAtZero: true,
                max: 500,
              }
            },
            interaction: { mode: 'index', intersect: false },
          }
        });
        return () => newChart.destroy();
      }
    }
  }, []);

  return (
    <div className="card">
      <div className="card-header" style={{ paddingBottom: 0 }}>
        <div className="card-title">
          <h3>Conversation Analytics</h3>
          <p>Track performance and analyze conversations</p>
        </div>
        <div style={{ background: '#f4f5f9', borderRadius: '8px', padding: '5px 10px', fontSize: '12px', fontWeight: '600', color: '#374151', display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
          Last 7 Days
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </div>
      </div>

      <div className="analytics-filters">
        <div className="filter-tabs">
          <button className="filter-tab active">Messages</button>
          <button className="filter-tab">Leads</button>
          <button className="filter-tab">Conversions</button>
        </div>
        <div className="legend">
          <div className="legend-item"><div className="legend-dot" style={{ background: '#6c4ef2' }}></div>Messages</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#10b981' }}></div>Leads</div>
        </div>
      </div>

      <div className="chart-area">
        <div className="chart-wrap">
          <canvas ref={chartRef} id="analyticsChart"></canvas>
        </div>
        <div className="insights-panel">
          <h4>Insights</h4>
          <div className="insight-item">
            <div className="insight-icon purple">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
            </div>
            <div className="insight-text">
              <div className="label">Peak Activity</div>
              <div className="value" style={{ color: '#6c4ef2' }}>Friday 6PM</div>
              <div className="sub">+32% more messages</div>
            </div>
          </div>
          <div className="insight-item">
            <div className="insight-icon green">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
            </div>
            <div className="insight-text">
              <div className="label">Top Intent</div>
              <div className="value" style={{ color: '#10b981' }}>Pricing Inquiry</div>
              <div className="sub">32% of all queries</div>
            </div>
          </div>
          <div className="insight-item">
            <div className="insight-icon red">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><line x1="23" y1="18" x2="17" y2="12" /><line x1="17" y1="18" x2="23" y2="12" /></svg>
            </div>
            <div className="insight-text">
              <div className="label">Drop-off Point</div>
              <div className="value" style={{ color: '#ef4444' }}>Step 2 (Menu)</div>
              <div className="sub">24% users drop here</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
