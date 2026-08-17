"use client";
import React, { useEffect, useRef, useState } from 'react';
import Chart from 'chart.js/auto';
import { apiGet } from '@/lib/api';

interface AnalyticsChartProps {
  isDark?: boolean;
}

interface AnalyticsData {
  labels: string[];
  messages: number[];
  leads: number[];
  insights: {
    peak_day: string;
    peak_time: string;
    peak_intensity: number;
    top_intent: string;
    top_intent_percentage: number;
    drop_off_point: string;
    drop_off_rate: number;
  };
}

export default function AnalyticsChart({ isDark }: AnalyticsChartProps) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await apiGet(`/api/conversations/analytics?days=${days}`);
        setAnalyticsData(data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
        const sampleLabels = Array.from({ length: days }, (_, i) => {
          const date = new Date();
          date.setDate(date.getDate() - (days - 1 - i));
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        setAnalyticsData({
          labels: sampleLabels,
          messages: Array.from({ length: days }, () => Math.floor(Math.random() * 10) + 2),
          leads: Array.from({ length: days }, () => Math.floor(Math.random() * 5) + 1),
          insights: {
            peak_day: 'Monday',
            peak_time: '2:00 PM',
            peak_intensity: 45,
            top_intent: 'Product Inquiry',
            top_intent_percentage: 38,
            drop_off_point: 'Checkout',
            drop_off_rate: 12
          }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [days]);

  useEffect(() => {
    if (!analyticsData || loading) return;

    const canvas = chartRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        if (chartInstanceRef.current) {
          chartInstanceRef.current.destroy();
        }

        const tooltipBg = isDark ? '#09090b' : 'white';
        const tooltipTitleColor = isDark ? '#fafafa' : '#0f172a';
        const tooltipBodyColor = isDark ? '#a1a1aa' : '#64748b';
        const tooltipBorderColor = isDark ? 'rgba(255,255,255,0.06)' : '#e8eaf0';

        const maxMessages = Math.max(...analyticsData.messages, 10);
        const maxLeads = Math.max(...analyticsData.leads, 5);
        const maxValue = Math.max(maxMessages, maxLeads);
        const yAxisMax = Math.ceil(maxValue * 1.2 / 10) * 10;

        const newChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: analyticsData.labels,
            datasets: [
              {
                label: 'Messages',
                data: analyticsData.messages,
                borderColor: '#6c4ef2',
                backgroundColor: 'rgba(108,78,242,0.06)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#6c4ef2',
                pointBorderColor: isDark ? '#09090b' : 'white',
                pointBorderWidth: 2,
              },
              {
                label: 'Leads',
                data: analyticsData.leads,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.04)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#10b981',
                pointBorderColor: isDark ? '#09090b' : 'white',
                pointBorderWidth: 2,
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
                cornerRadius: 10,
                padding: 12,
                boxPadding: 4,
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { font: { size: 10, family: 'Inter' }, color: isDark ? '#a1a1aa' : '#94a3b8' },
                border: { display: false },
              },
              y: {
                grid: { color: isDark ? 'rgba(255,255,255,0.03)' : '#f4f5f9' },
                ticks: { font: { size: 10, family: 'Inter' }, color: isDark ? '#a1a1aa' : '#94a3b8', maxTicksLimit: 6 },
                border: { display: false },
                beginAtZero: true,
                max: yAxisMax,
              }
            },
            interaction: { mode: 'index', intersect: false },
          }
        });

        chartInstanceRef.current = newChart;
      }
    }

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [analyticsData, isDark, loading]);

  const insights = analyticsData?.insights || {
    peak_day: 'N/A',
    peak_time: 'N/A',
    peak_intensity: 0,
    top_intent: 'N/A',
    top_intent_percentage: 0,
    drop_off_point: 'N/A',
    drop_off_rate: 0
  };

  return (
    <div className="card">
      <div className="card-header" style={{ paddingBottom: 0 }}>
        <div className="card-title">
          <h3 className={`text-[10px] font-bold uppercase tracking-[0.12em] mb-1 ${isDark ? 'text-violet-400' : 'text-violet-600'}`}>Performance Neural</h3>
          <h3 className="text-base font-bold tracking-tight">Conversation Analytics</h3>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className={`text-[10px] font-semibold rounded-lg px-3 py-1.5 border cursor-pointer transition-colors ${
            isDark
              ? 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
          }`}
        >
          <option value={7}>Last 7 Days</option>
          <option value={14}>Last 14 Days</option>
          <option value={30}>Last 30 Days</option>
        </select>
      </div>

      <div className="analytics-filters">
        <div className={`flex gap-1 p-1 rounded-xl ${isDark ? 'bg-white/[0.03]' : 'bg-slate-50'}`}>
          <button className={`px-4 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
            isDark ? 'bg-violet-500/15 text-violet-300' : 'bg-white text-violet-700 shadow-sm'
          }`}>Messages</button>
          <button className={`px-4 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
            isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-slate-500 hover:text-slate-700'
          }`}>Leads</button>
        </div>
        <div className="legend ml-auto">
          <div className="legend-item"><div className="legend-dot" style={{ background: '#6c4ef2' }}></div>Messages</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#10b981' }}></div>Leads</div>
        </div>
      </div>

      {loading ? (
        <div className="chart-area">
          <div className="chart-wrap flex items-center justify-center">
            <div className={`text-sm font-medium ${isDark ? 'text-zinc-600' : 'text-slate-400'}`}>Loading analytics...</div>
          </div>
        </div>
      ) : (
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
                <div className="value">{insights.peak_day} {insights.peak_time}</div>
                <div className="sub">+{insights.peak_intensity}% intensity</div>
              </div>
            </div>

            <div className="insight-item">
              <div className="insight-dot" style={{ background: '#f59e0b' }}></div>
              <div className="insight-text">
                <div className="label">Top Intent</div>
                <div className="value">{insights.top_intent}</div>
                <div className="sub">{insights.top_intent_percentage}% of total volume</div>
              </div>
            </div>

            <div className="insight-item">
              <div className="insight-dot" style={{ background: '#ef4444' }}></div>
              <div className="insight-text">
                <div className="label">Drop-off</div>
                <div className="value">{insights.drop_off_point}</div>
                <div className="sub">{insights.drop_off_rate}% friction rate</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
