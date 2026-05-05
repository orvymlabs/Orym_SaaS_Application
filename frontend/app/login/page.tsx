"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { apiPost, apiGet } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    // Force dark mode for auth pages
    document.documentElement.classList.add("dark");
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await apiPost("/api/auth/login", { email, password });
      
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("refreshToken", res.refresh_token);

      const user = await apiGet("/api/auth/me");
      
      if (user.role === "admin" || user.role === "super_admin") {
        router.push("/dashboard/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 font-sans bg-[#050505] text-white selection:bg-blue-500/30">
      <div className="w-full max-w-[450px] space-y-10 py-8">
        <div className="text-center space-y-6">
          <div className="inline-flex flex-col items-center gap-4">
            <div className="inline-flex p-5 rounded-[2rem] transform hover:scale-[1.03] transition-transform duration-300 border bg-zinc-900/50 border-zinc-800 shadow-2xl shadow-black">
              <Logo variant="text" theme="dark" className="h-9 sm:h-10 w-auto object-contain" fallbackText="ORVYM NEXUS" />
            </div>
            <div className="space-y-1">
              <h1 className="text-3xl sm:text-4xl font-black tracking-tighter platform-name text-white">ORVYM NEXUS</h1>
              <p className="text-[10px] font-bold uppercase tracking-[0.3em] ml-1 text-zinc-500">Live Conversation AI</p>
            </div>
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white/90">Welcome back</h2>
            <p className="text-zinc-500 text-sm mt-2 font-medium">Access your professional bot dashboard</p>
          </div>
        </div>

        <div className="border rounded-[2.5rem] p-8 sm:p-12 shadow-2xl relative overflow-hidden bg-zinc-900/40 border-zinc-800 shadow-black">
          <form onSubmit={handleLogin} className="space-y-8 relative z-10">
            {error && (
              <div className="border text-xs font-bold p-4 rounded-2xl text-center bg-rose-500/10 border-rose-500/20 text-rose-300">
                {error}
              </div>
            )}

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest ml-1 text-zinc-500">Email Address</label>
                <input
                  type="email"
                  placeholder="Enter your work email..."
                  className="input-field"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-3 relative">
                <label className="text-[10px] font-black uppercase tracking-widest ml-1 text-zinc-500">Secure Password</label>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password..."
                  className="input-field"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute bottom-4 right-6 text-zinc-600 hover:text-white transition-colors"
                >
                  {showPassword ? "👁️‍G" : "👁️"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full !py-4 shadow-xl"
            >
              {loading ? "Authorizing..." : "Log In to Nexus"}
            </button>
          </form>

          <div className="mt-10 relative z-10 text-center border-t border-white/5 pt-8">
            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">
              New to Orvym?{" "}
              <Link href="/signup" className="text-white hover:underline ml-1">Create Account</Link>
            </p>
          </div>
        </div>

        <div className="text-center pt-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-800">
            Powered by{" "}
            <a href="https://orvym.com" target="_blank" rel="noopener noreferrer" className="text-blue-500/80 hover:text-blue-400 transition-colors">
              ORVYM LABS
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
