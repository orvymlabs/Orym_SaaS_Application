"use client";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { Logo } from "@/components/Logo";
import "@/components/dashboard/dashboard.css";

function PlanBadge() {
  const [plan, setPlan] = useState<string>("starter");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet("/api/auth/usage")
      .then(data => {
        if (data?.plan) setPlan(data.plan);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return null;

  return (
    <div className="px-4 pb-6">
      <Link href="/dashboard/subscription" className="block">
        <div className={`rounded-2xl p-4 border-2 transition-all hover:scale-[1.02] ${
          plan === 'starter'
            ? 'bg-amber-50/50 border-amber-200 hover:border-amber-300'
            : 'bg-emerald-50/50 border-emerald-200 hover:border-emerald-300'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Current Plan</p>
              <p className={`text-sm font-black uppercase tracking-wide ${
                plan === 'starter' ? 'text-amber-700' : 'text-emerald-700'
              }`}>
                {plan}
              </p>
            </div>
            {plan === 'starter' ? (
              <div className="btn-upgrade px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider">
                Upgrade
              </div>
            ) : (
              <div className="bg-emerald-500 text-white px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider shadow-lg shadow-emerald-500/20">
                Active
              </div>
            )}
          </div>
        </div>
      </Link>
    </div>
  );
}

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
  )},
  { href: "/dashboard/chats", label: "Chats", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
  )},
  { href: "/dashboard/leads", label: "Leads", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
  )},
  { href: "/dashboard/orders", label: "Orders", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg>
  )},
  { href: "/dashboard/test-chat", label: "Sandbox", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.673.337a4 4 0 01-2.586.346l-1.541-.308A1 1 0 017 13.82V18a2 2 0 002 2h3.014a3 3 0 012.121.879l1.07 1.07A1 1 0 0016.914 22h3.014a2 2 0 002-2v-4.572zM6 7a2 2 0 100-4 2 2 0 000 4z"/></svg>
  )},
  { href: "/dashboard/settings", label: "Bot Engine", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
  )},
  { href: "/dashboard/integrations", label: "Integrations", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
  )},
  { href: "/dashboard/Support", label: "Support", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
  )},
  { href: "/dashboard/subscription", label: "Plan & Billing", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>
  )},
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  
  // NEW: Bot Status and User Data
  const [botStatus, setBotStatus] = useState(false);
  const [userName, setUserName] = useState("User");

  useEffect(() => {
    setMounted(true);
    // Load theme from localStorage, default to dark
    const savedTheme = localStorage.getItem("theme") as "dark" | "light";
    if (savedTheme) {
      setTheme(savedTheme);
    }
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Fetch Bot Info
    apiGet("/api/bots/me").then(data => {
      if (data) {
        setBotStatus(data.status ?? false);
        setUserName(data.name || "User");
      }
    }).catch(error => { // Added error logging
      console.error("Failed to fetch bot info:", error);
      // Optionally, you could set default states or show a toast here if desired
      // setBotStatus(false); 
      // setUserName("Error");
    });
  }, []);

  useEffect(() => {
    if (mounted) {
      localStorage.setItem("theme", theme);
      document.documentElement.classList.toggle("dark", theme === "dark");
      window.dispatchEvent(new CustomEvent("theme-changed", { detail: { theme } }));
    }
  }, [theme, mounted]);

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    router.push("/login");
  };

  if (!mounted) return null;

  const isDark = theme === "dark";

  return (
    <div className={`flex h-screen font-sans overflow-hidden transition-colors duration-300 ${isDark ? "bg-[#050505] text-zinc-100" : "bg-[#F8FAFC] text-[#0F172A]"}`}>
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} ${isDark ? "bg-[#090909] border-r border-zinc-800" : "bg-white border-r border-[#F1F5F9]"}`}>
        <div className="flex flex-col h-full">
          {/* Brand Logo */}
          <div className="p-8 pb-6 flex items-center justify-between">
            <Link href="/dashboard" className="flex items-center gap-4 group">
              <div
                className={`p-4 rounded-2xl group-hover:scale-[1.03] transition-all duration-300 border ${
                  isDark
                    ? "bg-black border-zinc-800 shadow-xl shadow-black/40"
                    : "bg-white border-slate-200 shadow-xl shadow-slate-200/60"
                }`}
              >
                <Logo variant="symbol" theme={theme} className="w-16 h-16 object-contain" fallbackText="O" />
              </div>
              <div>
                <span className={`text-2xl font-bold tracking-tight platform-name ${isDark ? "text-white" : "text-[#0F172A]"}`}>ORVYM NEXUS</span>
                <p className={`text-[9px] font-bold uppercase tracking-wide leading-none mt-1 ${isDark ? "text-zinc-500" : "text-slate-600"}`}>Live Conversation AI</p>
              </div>
            </Link>
            <button className={`lg:hidden p-2 rounded-lg ${isDark ? "text-zinc-400 hover:bg-zinc-800" : "text-slate-500 hover:bg-slate-100"}`} onClick={() => setIsSidebarOpen(false)}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          {/* Plan Badge */}
          <PlanBadge />

          {/* Navigation */}
          <nav className="flex-1 px-4 py-8 space-y-1.5 overflow-y-auto">
            <p className={`px-5 text-[10px] font-bold uppercase tracking-wide mb-4 ${isDark ? "text-zinc-500" : "text-slate-400"}`}>Navigation</p>
            {navItems.map(item => {
              const active = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-3.5 px-5 py-3.5 rounded-2xl text-[14px] font-bold transition-all duration-200 group ${
                    active
                      ? isDark ? "bg-blue-600 text-white shadow-lg shadow-blue-900/30" : "bg-blue-600 text-white"
                      : isDark
                        ? "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                        : "text-slate-500 hover:bg-slate-50 hover:text-slate-600"
                  }`}>
                  <span className={`w-5 h-5 transition-transform duration-200 ${active ? "scale-110" : "group-hover:scale-110"}`}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="p-6 mt-auto">
            <div className={`rounded-2xl p-5 border ${isDark ? "bg-zinc-900/50 border-zinc-800" : "bg-slate-50 border-slate-100"}`}>
              <button onClick={handleLogout}
                className="btn-danger w-full">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign Out
              </button>
            </div>
            {/* ORVYM LABS Footer */}
            <div className="mt-6 text-center">
              <p className={`text-[10px] font-medium ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                Powered by{" "}
                <a href="https://orvym.com" target="_blank" rel="noopener noreferrer" className={`font-semibold hover:underline ${isDark ? "text-slate-500/80" : "text-slate-600"}`}>
                  ORVYM LABS
                </a>
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main App Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className={`h-20 backdrop-blur-xl flex items-center justify-between px-8 z-40 sticky top-0 transition-colors duration-300 ${
          isDark ? "bg-black/60 border-b border-zinc-800" : "bg-white/80 border-b border-[#F1F5F9]"
        }`}>
          <div className="flex items-center gap-4">
            <button className={`lg:hidden p-2 rounded-lg ${isDark ? "text-zinc-400 hover:bg-zinc-800" : "text-slate-500 hover:bg-slate-100"}`} onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"/></svg>
            </button>
            <h2 className={`text-lg font-bold tracking-tight capitalize ${isDark ? "text-white" : "text-slate-800"}`}>
              {pathname === "/dashboard" ? "Dashboard" : pathname?.split("/").pop()?.replace("-", " ")}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            {/* Moved elements: WA Chip, Notif, User */}
            <div className={`wa-chip ${!botStatus ? 'offline' : ''} hidden md:flex`}>
              <svg viewBox="0 0 24 24" fill={botStatus ? "#25d366" : "#ef4444"} width="15" height="15">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884" />
              </svg>
              <span>{botStatus ? "Connected" : "Offline"}</span>
            </div>

            <button className="notif-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" /></svg>
              <span className="notif-badge">3</span>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2.5 rounded-xl transition-all ${
                isDark
                  ? "bg-zinc-900 text-amber-300 hover:bg-zinc-800"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {isDark ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M14 12a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
              )}
            </button>

            <div className={`h-6 w-px ${isDark ? "bg-zinc-800" : "bg-slate-200"}`}></div>
            
            <div className="user-chip">
              <div className="user-avatar">{userName.charAt(0)}</div>
              <div className="user-info hidden lg:block text-left">
                <h4>{userName}</h4>
                <p>Founder Mode</p>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-7xl mx-auto space-y-8 pb-12">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
