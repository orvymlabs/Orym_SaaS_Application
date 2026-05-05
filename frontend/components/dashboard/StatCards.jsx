"use client";
import React from 'react';
import Chart from 'chart.js/auto'; // Assuming chart.js is available globally or imported this way
import { Line } from 'react-chartjs-2'; // For sparklines if needed

// Mock component for sparkline charts, as actual chart instantiation is complex in SSR/client components
const SparklineChart = ({ data, color }) => {
  // In a real React app, you'd use chart.js or a similar library here.
  // For now, we'll just render a placeholder or simple representation.
  // The original HTML used <canvas> elements with IDs like 'chart1', 'chart2', 'chart3'.
  // We'll map these to props for simplicity in this component.
  // The actual chart rendering logic will be handled by the parent or a specific chart component.
  return (
    <div style={{ width: '70px', height: '30px', backgroundColor: '#eee', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#aaa', fontSize: '10px' }}>
      Sparkline
    </div>
  );
};

export default function StatCards({ stats }) {
  const {
    aiResponsesCount,
    aiLimit,
    activeConversationsCount,
    conversationsLimit,
    leadsCaptured,
    automationRate,
    whatsappMessagesSent,
    whatsappLimit,
  } = stats || {};

  // Placeholder data for sparklines - actual data should come from props or state
  const sparklineData1 = [60, 80, 70, 90, 85, 100, 95, 110];
  const sparklineData2 = [50, 60, 55, 75, 65, 80, 70, 85];
  const sparklineData3 = [20, 30, 25, 40, 35, 50, 45, 55];

  // Mock data for donut chart - actual data should come from props or state
  const donutChartData = {
    datasets: [{
      data: [automationRate || 78, 100 - (automationRate || 78)],
      backgroundColor: ['#6c4ef2', '#ede9fe'],
      borderWidth: 0,
      hoverOffset: 0,
    }]
  };
  const donutChartCenterText = `${automationRate || 78}%`;

  return (
    <div className="stat-row">
      {/* Stat Card 1: AI Responses */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a10 10 0 110 20 10 10 0 010-20zm0 6v4l3 3"></path>
            </svg>
          </div>
          {/* Replace SparklineChart with actual Canvas if integrated */}
          <SparklineChart data={sparklineData1} color="#6c4ef2" />
        </div>
        <div>
          <div className="stat-label">AI Responses</div>
          <h3>{aiResponsesCount || 'N/A'}</h3>
        </div>
        {/* Placeholder for change percentage - logic to be added */}
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          {/* Placeholder percentage */}
          23% vs last 7 days
        </div>
      </div>

      {/* Stat Card 2: Active Conversations */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"></path>
            </svg>
          </div>
          <SparklineChart data={sparklineData2} color="#3b82f6" />
        </div>
        <div>
          <div className="stat-label">Active Conversations</div>
          <h3>{activeConversationsCount || 'N/A'}</h3>
        </div>
        {/* Placeholder for change percentage - logic to be added */}
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          {/* Placeholder percentage */}
          18% vs last 7 days
        </div>
      </div>

      {/* Stat Card 3: Leads Captured */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"></path>
            </svg>
          </div>
          <SparklineChart data={sparklineData3} color="#10b981" />
        </div>
        <div>
          <div className="stat-label">Leads Captured</div>
          <h3>{leadsCaptured || 'N/A'}</h3>
        </div>
        {/* Placeholder for change percentage - logic to be added */}
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          {/* Placeholder percentage */}
          12% vs last 7 days
        </div>
      </div>
      
      {/* Stat Card 4: WhatsApp Messaging (New requirement based on provided context) */}
      <div className="stat-card">
        <div className="stat-card-top">
          <div className="stat-icon purple"> {/* Using purple for consistency with other cards, or could be a new color */}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {/* WhatsApp icon or relevant icon */}
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
            </svg>
          </div>
          {/* Placeholder for sparkline - if the new design has one */}
          {/* <SparklineChart data={...} color="#6c4ef2" /> */}
          <div style={{ width: '70px', height: '30px' }}></div> {/* Placeholder div */}
        </div>
        <div>
          <div className="stat-label">WhatsApp Messages</div>
          <h3>{whatsappMessagesSent || '0'} / {whatsappLimit || '200'}</h3>
        </div>
        {/* Placeholder for change percentage - logic to be added */}
        <div className="stat-change up">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          {/* Placeholder percentage */}
          10% vs last 7 days
        </div>
      </div>
    </div>
  );
}
