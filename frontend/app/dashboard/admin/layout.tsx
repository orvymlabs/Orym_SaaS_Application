"use client";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

const adminNavItems = [
  { href: "/dashboard/admin", label: "Dashboard", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
  )},
  { href: "/dashboard/admin/users", label: "User Registry", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
  )},
  { href: "/dashboard/admin/announcements", label: "Broadcasts", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/></svg>
  )},
  { href: "/dashboard/admin/revenue", label: "Financials", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
  )},
  { href: "/dashboard/admin/logs", label: "Audit Trails", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
  )},
  { href: "/dashboard/admin/settings", label: "Core Settings", icon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
  )},
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [userRole, setUserRole] = useState<string>("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    apiGet("/api/auth/me")
      .then(user => {
        setUserRole(user.role);
        if (user.role !== "admin" && user.role !== "super_admin") {
          router.push("/dashboard");
        }
      })
      .catch(() => {
        localStorage.removeItem("token");
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    router.push("/login");
  };

  if (!mounted) return null;
  if (userRole !== "admin" && userRole !== "super_admin") return null;

  return (
    <div className="flex h-screen bg-[#050505] text-white font-sans overflow-hidden">
      {/* Super Admin Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#090909] border-r border-zinc-800 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex flex-col h-full">
          {/* Brand Logo */}
          <div className="p-8 pb-6 flex items-center justify-between border-b border-zinc-900">
            <Link href="/dashboard/admin" className="flex items-center gap-4 group">
              <div className="bg-[#6c4ef2] p-3.5 rounded-2xl shadow-2xl shadow-[#6c4ef2]/20 group-hover:shadow-[#6c4ef2]/40 transition-all duration-300">
                <img src="/logo.png" alt="ORVYN" className="w-10 h-10 object-contain" />
              </div>
              <div>
                <span className="text-2xl font-black tracking-tighter text-white">ORVYM</span>
                <p className="text-[9px] font-bold text-[#8b6ff5] uppercase tracking-[0.2em] leading-none mt-1">
                  {userRole === "super_admin" ? "SUPER CORE" : "NEXUS ADMIN"}
                </p>
              </div>
            </Link>
            <button className="lg:hidden p-2 text-zinc-500 hover:text-white transition-colors" onClick={() => setIsSidebarOpen(false)}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          {/* Admin Badge */}
          <div className="px-6 py-8">
            <div className="bg-white/5 rounded-[2rem] p-5 border border-white/10 shadow-2xl">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-[#6c4ef2]/20 border border-[#6c4ef2]/40 flex items-center justify-center shadow-xl">
                  <svg className="w-6 h-6 text-[#8b6ff5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div>
                  <p className="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Master Auth</p>
                  <p className="text-sm font-black text-white">{userRole === "super_admin" ? "Super Core" : "Admin"}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Admin Navigation */}
          <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto">
            <p className="px-5 text-[10px] font-black text-zinc-700 uppercase tracking-[0.3em] mb-4">Command Center</p>
            {adminNavItems.map(item => {
              const active = pathname === item.href || (item.href !== "/dashboard/admin" && pathname?.startsWith(item.href));
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-3.5 px-5 py-4 rounded-2xl text-[13px] font-black tracking-tight transition-all duration-300 group ${
                    active
                      ? "bg-[#6c4ef2] text-white shadow-2xl shadow-[#6c4ef2]/30 scale-[1.02]"
                      : "text-zinc-500 hover:bg-white/5 hover:text-white"
                  }`}>
                  <span className={`${active ? "text-white scale-110" : "text-zinc-700 group-hover:text-[#8b6ff5] group-hover:scale-110 transition-transform duration-300"}`}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="p-6 mt-auto">
            <button onClick={handleLogout}
              className="btn-danger w-full !py-4 shadow-xl shadow-rose-500/10">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              TERMINATE SESSION
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-20 bg-black/60 backdrop-blur-xl border-b border-zinc-800/50 flex items-center justify-between px-10 z-40 sticky top-0">
          <div className="flex items-center gap-5">
            <button className="lg:hidden p-2 text-zinc-500 hover:text-white transition-colors" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"/></svg>
            </button>
            <h2 className="text-lg font-black text-white tracking-tighter uppercase tracking-widest text-xs opacity-50">
              {pathname === "/dashboard/admin" ? "Nexus Core Overview" : pathname?.split("/").pop()?.replace("-", " ")}
            </h2>
          </div>

          <div className="flex items-center gap-6">
            <div className="hidden sm:flex items-center gap-4 pl-6 border-l border-zinc-800/50">
              <div className="w-11 h-11 rounded-xl bg-white/5 border border-white/10 shadow-2xl overflow-hidden flex items-center justify-center p-2 transition-transform hover:scale-105">
                <img src="/logo.png" alt="Profile" className="w-full h-full object-contain" />
              </div>
              <div>
                <p className="text-xs font-black text-white tracking-tight uppercase">{userRole === "super_admin" ? "ROOT CORE" : "NEXUS ADMIN"}</p>
                <p className="text-[9px] text-[#8b6ff5] font-bold uppercase tracking-widest mt-0.5">{userRole === "super_admin" ? "FULL AUTHORITY" : "RESTRICTED ACCESS"}</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-10 relative custom-scrollbar">
          <div className="max-w-7xl mx-auto space-y-10 pb-12">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
