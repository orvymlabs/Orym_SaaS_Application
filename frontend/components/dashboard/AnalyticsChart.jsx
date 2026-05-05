"use client";
import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function AnalyticsChart({ chartData, chartLabels, insights }) {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    if (chartRef.current && chartLabels && chartData) {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy(); // Destroy previous instance if it exists
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstanceRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: 'Messages',
              data: chartData.messages,
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
              data: chartData.leads,
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
              max: chartData.yMax || 500, // Use a dynamic max if possible
            }
          },
          interaction: { mode: 'index', intersect: false },
        }
      });
    }

    // Cleanup function to destroy chart instance
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [chartData, chartLabels, insights]); // Re-run effect if data changes

  return (
    <div className="card">
      <div className="card-header" style={{ paddingBottom: 0 }}>
        <div className="card-title">
          <h3>Conversation Analytics</h3>
          <p>Track performance and analyze conversations</p>
        </div>
        <div style={{ background: '#f4f5f9', borderRadius: '8px', padding: '5px 10px', fontSize: '12px', fontWeight: '600', color: '#374151', display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
          Last 7 Days {/* This should ideally be a dynamic selector */}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
      </div>

      <div className="analytics-filters">
        <div className="filter-tabs">
          {/* These filter tabs should ideally be interactive and control chart data */}
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
          <canvas ref={chartRef}></canvas>
        </div>
        <div className="insights-panel">
          <h4>Insights</h4>
          {insights && insights.map((insight, index) => (
            <div key={index} className="insight-item">
              <div className={`insight-icon ${insight.color || 'purple'}`} style={{ backgroundColor: insight.iconBgColor }}>
                {/* Render SVG icon based on insight.icon */}
                {insight.icon ? insight.icon : (
                  // Default icon if none provided
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  </svg>
                )}
              </div>
              <div className="insight-text">
                <div className="label">{insight.label}</div>
                <div className="value" style={{ color: insight.valueColor || '#6c4ef2' }}>{insight.value}</div>
                <div className="sub">{insight.sub}</div>
              </div>
            </div>
          ))}
          {/* If no insights prop is passed, render defaults */}
          {!insights && (
            <>
              <div className="insight-item">
                <div className="insight-icon purple">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <div className="insight-text">
                  <div className="label">Peak Activity</div>
                  <div className="value" style={{ color: '#6c4ef2' }}>Friday 6PM</div>
                  <div className="sub">+32% more messages</div>
                </div>
              </div>
              <div className="insight-item">
                <div className="insight-icon green">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                </div>
                <div className="insight-text">
                  <div className="label">Top Intent</div>
                  <div className="value" style={{ color: '#10b981' }}>Pricing Inquiry</div>
                  <div className="sub">32% of all queries</div>
                </div>
              </div>
              <div className="insight-item">
                <div className="insight-icon red">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="23" y1="18" x2="17" y2="12"/><line x1="17" y1="18" x2="23" y2="12"/></svg>
                </div>
                <div className="insight-text">
                  <div className="label">Drop-off Point</div>
                  <div className="value" style={{ color: '#ef4444' }}>Step 2 (Menu)</div>
                  <div className="sub">24% users drop here</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
