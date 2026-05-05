"use client";
import { useEffect, useState } from "react";
import Topbar from '@/components/dashboard/Topbar';
import StatCards from '@/components/dashboard/StatCards';
import AnalyticsChart from '@/components/dashboard/AnalyticsChart';
import LeadsTable from '@/components/dashboard/LeadsTable';
import RightColumn from '@/components/dashboard/RightColumn';
import { useTheme } from '@/lib/useTheme';
import '@/components/dashboard/dashboard.css';

export default function DashboardPage() {
  const { isDark } = useTheme();

  // Legacy root dashboard page - updated for professional styling consistency
  const botStatus = true;

  return (
    <div className="main animate-in fade-in duration-700">
      <Topbar isDark={isDark} botStatus={botStatus} />

      <div className="dashboard-content">
        <div className="col-left">
          <StatCards 
            messagesCount="0/200" 
            contactsCount={0} 
            aiRequestsCount="0/200" 
            isDark={isDark} 
          />

          <AnalyticsChart isDark={isDark} />

          <LeadsTable leads={[]} isDark={isDark} />
        </div>

        <div className="col-right">
          <RightColumn 
            messagesCount="0/200" 
            aiRequestsCount="0/200" 
            isDark={isDark} 
          />
        </div>
      </div>
    </div>
  );
}
