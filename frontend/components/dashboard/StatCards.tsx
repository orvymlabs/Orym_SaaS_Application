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

  // Icon colors based on theme
  const purpleIconColor = isDark ? '#a78bfa' : '#6c4ef2';
  const blueIconColor = isDark ? '#60a5fa' : '#3b82f6';
  const greenIconColor = isDark ? '#4ade80' : '#10b981';

  return (
    <div className="stat-row">
      {/* WhatsApp Messages Sent (Purple) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke={purpleIconColor} strokeWidth="2" width="20" height="20">
              <path d="M12 2a10 10 0 110 20 10 10 0 010-20zm0 6v4l3 3" />
            </svg>
          </div>
          <canvas ref={chartRefs[0]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Messages Sent</div>
          <h3>{messagesCount.split('/')[0]}</h3>
        </div>
        <div className="stat-change">
          Limit: {messagesCount.split('/')[1] || '200'}
        </div>
      </div>

      {/* Total Contacts / Active Leads (Blue) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke={blueIconColor} strokeWidth="2" width="20" height="20">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
          </div>
          <canvas ref={chartRefs[1]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Active Leads</div>
          <h3>{contactsCount}</h3>
        </div>
        <div className="stat-change">
          Total Contacts
        </div>
      </div>

      {/* AI Requests / AI Responses (Green) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke={greenIconColor} strokeWidth="2" width="20" height="20">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
            </svg>
          </div>
          <canvas ref={chartRefs[2]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">AI Responses</div>
          <h3>{aiRequestsCount.split('/')[0]}</h3>
        </div>
        <div className="stat-change">
          Limit: {aiRequestsCount.split('/')[1] || '200'}
        </div>
      </div>
    </div>
  );
}
