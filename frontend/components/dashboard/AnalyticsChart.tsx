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
        const tooltipBg = isDark ? '#1a1b2e' : 'white';
        const tooltipTitleColor = isDark ? '#ffffff' : '#0f172a';
        const tooltipBodyColor = isDark ? '#94a3b8' : '#64748b';
        const tooltipBorderColor = isDark ? '#2a2b3d' : '#e8eaf0';

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
                backgroundColor: tooltipBg,
                titleColor: tooltipTitleColor,
                bodyColor: tooltipBodyColor,
                borderColor: tooltipBorderColor,
                borderWidth: 1,
                padding: 10,
                boxPadding: 4,
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, color: isDark ? '#94a3b8' : '#64748b' },
                border: { display: false },
              },
              y: {
                grid: { color: isDark ? '#2a2b3d' : '#f0f2f8' },
                ticks: { font: { size: 10 }, color: isDark ? '#94a3b8' : '#64748b', maxTicksLimit: 6 },
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
  }, [isDark]);

  const peakDay = "Friday";
  const peakTime = "6PM";
  const topIntent = "Pricing Inquiry";
  const dropOffPoint = "Step 2 (Menu)";

  return (
    <div className="card">
      <div className="card-header" style={{ paddingBottom: 0 }}>
        <div className="card-title">
          <h3 className="font-black uppercase tracking-widest text-[10px] text-[#6c4ef2] mb-1">Performance Neural</h3>
          <h3 className="text-lg font-black tracking-tight">Conversation Analytics</h3>
        </div>
        <button className="btn-pill btn-pill-inactive !text-[9px] border-none bg-zinc-100 dark:bg-zinc-900 !px-3">
          Last 7 Days
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="10" height="10" className="ml-1"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </button>
      </div>

      <div className="analytics-filters">
        <div className="flex gap-2 p-1.5 rounded-xl bg-slate-50 dark:bg-zinc-900/50">
          <button className="btn-pill btn-pill-active !py-1 !px-4">Messages</button>
          <button className="btn-pill btn-pill-inactive !py-1 !px-4 border-none">Leads</button>
        </div>
        <div className="legend ml-auto">
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
            <div className="insight-dot" style={{ background: '#6c4ef2' }}></div>
            <div className="insight-text">
              <div className="label">Peak Activity</div>
              <div className="value">{peakDay} {peakTime}</div>
              <div className="sub">+32% intensity</div>
            </div>
          </div>

          <div className="insight-item">
            <div className="insight-dot" style={{ background: '#f59e0b' }}></div>
            <div className="insight-text">
              <div className="label">Top Intent</div>
              <div className="value">{topIntent}</div>
              <div className="sub">32% of total volume</div>
            </div>
          </div>

          <div className="insight-item">
            <div className="insight-dot" style={{ background: '#ef4444' }}></div>
            <div className="insight-text">
              <div className="label">Drop-off</div>
              <div className="value">{dropOffPoint}</div>
              <div className="sub">24% friction rate</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
