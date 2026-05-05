"use client";
import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

// Define the props interface for StatCards
interface StatCardsProps {
  messagesCount: string; // e.g., "0/200"
  contactsCount: number; // e.g., 123
  aiRequestsCount: string; // e.g., "0/200"
  isDark?: boolean; // Not used in this component but kept for potential future use or context consistency
}

export default function StatCards({ messagesCount, contactsCount, aiRequestsCount, isDark }: StatCardsProps) {
  // Refs for the three sparkline canvases
  const chartRefs = [useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null), useRef<HTMLCanvasElement>(null)];

  useEffect(() => {
    // Data and colors for the sparkline charts, matching the new design mapping
    const sparklineConfig = [
      { data: [60, 80, 70, 90, 85, 100, 95, 110], color: '#6c4ef2', label: 'Messages Sent' }, // Purple for messages
      { data: [50, 60, 55, 75, 65, 80, 70, 85], color: '#3b82f6', label: 'Active Leads' }, // Blue for contacts/leads
      { data: [20, 30, 25, 40, 35, 50, 45, 55], color: '#10b981', label: 'AI Responses' }, // Green for AI requests
    ];

    const charts: Chart[] = [];

    sparklineConfig.forEach((config, index) => {
      const canvas = chartRefs[index].current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          // Create a new Chart instance for each canvas
          const newChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: config.data.map((_, i) => i), // Simple index-based labels
              datasets: [{
                data: config.data,
                borderColor: config.color,
                borderWidth: 1.5,
                fill: false, // No fill under the line
                tension: 0.4, // Smoothness of the line
                pointRadius: 0, // Hide data points
              }]
            },
            options: {
              // Chart.js options to make it a simple sparkline
              responsive: false, // Set false as we control size with canvas width/height
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }, // Hide legend
                tooltip: { enabled: false }  // Hide tooltips
              },
              scales: {
                x: { display: false }, // Hide X-axis
                y: { display: false }  // Hide Y-axis
              },
              animation: false, // Disable animation for sparklines
            }
          });
          charts.push(newChart);
        }
      }
    });

    // Cleanup function to destroy charts when component unmounts
    return () => {
      charts.forEach(chart => chart.destroy());
    };
  }, []); // Re-run effect only on mount

  // Parse limits for messages and AI requests
  const messageLimit = messagesCount.split('/')[1] || '200'; // Default to 200 if not specified
  const aiRequestLimit = aiRequestsCount.split('/')[1] || '200'; // Default to 200 if not specified

  return (
    <div className="stat-row">
      {/* Stat Card for Messages Sent (Purple) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a10 10 0 110 20 10 10 0 010-20zm0 6v4l3 3" />
            </svg>
          </div>
          <canvas ref={chartRefs[0]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Messages Sent</div>
          <h3>{messagesCount.split('/')[0]}</h3>
        </div>
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
          Limit: {messageLimit}
        </div>
      </div>

      {/* Stat Card for Active Leads (Blue) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
          </div>
          <canvas ref={chartRefs[1]} className="stat-mini-chart" width="70" height="30"></canvas>
        </div>
        <div>
          <div className="stat-label">Active Leads</div>
          <h3>{contactsCount}</h3>
        </div>
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
          Total Contacts
        </div>
      </div>

      {/* Stat Card for AI Responses (Green) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
          Limit: {aiRequestLimit}
        </div>
      </div>
    </div>
  );
}
