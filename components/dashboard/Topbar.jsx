:root {
  --bg-dark: #0d0e14; /* Default dark background for elements like cards in dark mode */
  --bg-sidebar: #10111a;
  --bg-card: #ffffff; /* Default card background (light mode) */
  --bg-card-hover: #f8f8fc;
  --accent-purple: #6c4ef2;
  --accent-purple-light: #8b6ff5;
  --accent-purple-dim: #ede9fe;
  --accent-green: #10b981;
  --accent-orange: #f59e0b;
  --accent-red: #ef4444;
  --text-dark: #0f172a; /* Default text color (light mode) */
  --text-muted: #64748b; /* Muted text color (light mode) */
  --text-light: #94a3b8; /* Light text color, used in dark mode */
  --border: #e8eaf0; /* Default border color (light mode) */
  --sidebar-text: #a0aec0;
  --sidebar-active: #ffffff;
  --whatsapp: #25d366;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
  --radius: 14px;
  --radius-sm: 8px;
  --radius-xs: 6px;

  /* Specific theme variables as per instructions */
  --bg-content-light: #f0f2f8; /* Light mode dashboard content background */
  --bg-card-light: #ffffff; /* Light mode cards background */
  --text-dark-light: #0f172a; /* Light mode primary text */
  --text-muted-light: #64748b; /* Light mode muted text */
  --border-light: #e8eaf0; /* Light mode borders */
}

/* DARK MODE VARIABLES */
:root.dark {
  --bg-dark: #0d0e14; /* Dark mode dashboard content background */
  --bg-card: #1a1b2e; /* Dark mode cards background */
  --text-dark: #ffffff; /* Dark mode primary text */
  --text-muted: #94a3b8; /* Dark mode muted text */
  --border: #2a2b3d; /* Dark mode borders */
  --bg-card-hover: #2a2b3d; /* Card hover background */

  /* Accent colors for dark mode */
  --accent-purple: #a78bfa;
  --accent-purple-light: #8b6ff5;
  --accent-purple-dim: #312e81; /* Darker dim purple */
  --accent-green: #4ade80;
  --accent-orange: #f59e0b;
  --accent-red: #f87171;
  --sidebar-active: #ffffff;
  --sidebar-text: #94a3b8;

  --shadow-sm: 0 1px 3px rgba(255,255,255,0.06), 0 1px 2px rgba(255,255,255,0.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.2); /* Darker shadow for dark mode */
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.2);
}


/* TOPBAR */
.topbar {
  background: var(--bg-card); /* Use card background */
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  height: 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
  position: sticky; top: 0; z-index: 50;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-left h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-dark);
}

.topbar-left p {
  font-size: 12.5px;
  color: var(--text-muted);
  margin-top: 1px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Theme Toggle Button - Styles should adapt based on 'dark' class on body/html */
.theme-toggle-btn {
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 9px;
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.theme-toggle-btn:hover { background: var(--bg-card-hover); }
.theme-toggle-btn svg { width: 18px; height: 18px; color: var(--text-muted); }

.wa-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f0fdf4; /* Default green background for light mode */
  border: 1px solid #bbf7d0;
  border-radius: 20px;
  padding: 5px 12px 5px 8px;
  font-size: 12.5px;
  font-weight: 600;
  color: #166534;
  cursor: pointer;
}

.wa-chip.offline {
  background: #fef2f2; /* Default red background for offline */
  border: 1px solid #fecaca;
  color: #991b1b;
}

/* Theme specific wa-chip background */
.dark .wa-chip {
  background: rgba(167, 139, 250, 0.15); /* Use theme accent purple */
  border-color: var(--accent-purple-light);
  color: var(--accent-purple);
}
.dark .wa-chip.offline {
  background: rgba(252, 165, 165, 0.15); /* Use theme accent red */
  border-color: var(--accent-red);
  color: var(--accent-red);
}

.wa-dot { width: 7px; height: 7px; background: var(--whatsapp); border-radius: 50%; }
.wa-dot.offline { background: var(--accent-red); }

.notif-btn {
  position: relative;
  width: 36px; height: 36px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.notif-btn:hover { background: var(--bg-card-hover); }
.notif-btn svg { width: 17px; height: 17px; color: var(--text-muted); }

.notif-badge {
  position: absolute;
  top: -4px; right: -4px;
  background: #ef4444;
  color: white;
  font-size: 9px;
  font-weight: 700;
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid var(--bg-card); /* Adjust border color for theme */
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border: 1px solid var(--border);
  border-radius: 22px;
  background: var(--bg-card);
  transition: all 0.2s;
}

.user-chip:hover { background: var(--bg-card-hover); }

.user-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  object-fit: cover;
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-purple-light));
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 12px; font-weight: 700;
}

.user-info h4 { font-size: 12.5px; font-weight: 700; color: var(--text-dark); }
.user-info p { font-size: 10px; color: var(--accent-purple); font-weight: 600; }

/* MOBILE MENU BUTTON */
.mobile-menu-btn {
  display: none; /* Hidden by default, shown on smaller screens */
  width: 36px; height: 36px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 9px;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.mobile-menu-btn:hover { background: var(--bg-card-hover); }
.mobile-menu-btn svg { width: 18px; height: 18px; color: var(--text-muted); }

/* MEDIA QUERIES FOR TOPBAR */
@media (max-width: 900px) {
  .mobile-menu-btn { display: flex; } /* Show on smaller screens */
}
