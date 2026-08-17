"use client";
import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

interface StatCardsProps {
  messagesCount: string;
  contactsCount: number;
  aiRequestsCount: string;
  isDark?: boolean;
}

export default function StatCards({ messagesCount, contactsCount, aiRequestsCount, isDark }: StatCardsProps) {
  const chartRefs = [useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null)];

  useEffect(() => {
    const sparklineData = [
      { data: [60, 80, 70, 90, 85, 100, 95, 110], color: isDark ? '#a78bfa' : '#6c4ef2' },
      { data: [50, 60, 55, 75, 65, 80, 70, 85], color: isDark ? '#60a5fa' : '#3b82f6' },
      { data: [20, 30, 25, 40, 35, 50, 45, 55], color: isDark ? '#4ade80' : '#10b981' },
    ];

    const charts: Chart[] = [];

    sparklineData.forEach((item, index) => {
      const canvas = chartRefs[index].current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          const newChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: item.data.map((_, i) => i),
              datasets: [{
                data: item.data,
                borderColor: item.color,
                borderWidth: 1.5,
                fill: false,
                tension: 0.4,
                pointRadius: 0,
              }]
            },
            options: {
              responsive: false,
              maintainAspectRatio: false,
              plugins: { legend: { display: false }, tooltip: { enabled: false } },
              scales: { x: { display: false }, y: { display: false } },
              animation: false,
            }
          });
          charts.push(newChart);
        }
      }
    });

    return () => {
      charts.forEach(chart => chart.destroy());
    };
  }, [isDark]);

  const purpleIconColor = isDark ? '#a78bfa' : '#6c4ef2';
  const blueIconColor = isDark ? '#60a5fa' : '#3b82f6';
  const greenIconColor = isDark ? '#4ade80' : '#10b981';

  return (
    <div className="stat-row">
      {/* WhatsApp Messages Sent */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke={purpleIconColor} strokeWidth="2" width="20" height="20">
              <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <canvas ref={chartRefs[0]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Messages Sent</div>
          <h3>{typeof messagesCount === 'string' && messagesCount.includes('/') ? messagesCount.split('/')[0] : (typeof messagesCount === 'number' ? messagesCount : 'N/A')}</h3>
        </div>
      </div>

      {/* Active Leads */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke={blueIconColor} strokeWidth="2" width="20" height="20">
              <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 00-3-3.87" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M16 3.13a4 4 0 010 7.75" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <canvas ref={chartRefs[1]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Active Leads</div>
          <h3>{contactsCount}</h3>
        </div>
        <div className="stat-change">Total Contacts</div>
      </div>

      {/* AI Responses */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke={greenIconColor} strokeWidth="2" width="20" height="20">
              <path d="M12 2a4 4 0 014 4c0 1.95-1.4 3.58-3.25 3.93" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M8.56 9.8A4.002 4.002 0 0112 2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M12 6v6l3 3" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M22 12a10 10 0 11-20 0 10 10 0 0120 0z" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M16 16l2 2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M18 14l2 2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <canvas ref={chartRefs[2]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">AI Responses</div>
          <h3>{typeof aiRequestsCount === 'string' && aiRequestsCount.includes('/') ? aiRequestsCount.split('/')[0] : (typeof aiRequestsCount === 'number' ? aiRequestsCount : 'N/A')}</h3>
        </div>
      </div>
    </div>
  );
}
