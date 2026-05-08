"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiPost } from "@/lib/api";
import { Logo } from "@/components/Logo";

export default function SignupPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);

  useEffect(() => {
    // Force dark mode for auth pages
    document.documentElement.classList.add("dark");
  }, []);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreeTerms) {
      setError("You must agree to the Terms & Conditions to continue.");
      return;
    }
    setLoading(true);
    setError("");

    let retryCount = 0;
    const maxRetries = 2;

    while (retryCount <= maxRetries) {
      try {
        const res = await apiPost("/api/auth/signup", {
          full_name: fullName,
          email,
          password
        });
        localStorage.setItem("token", res.access_token);
        localStorage.setItem("refreshToken", res.refresh_token);
        router.push("/dashboard");
        return; // Success - exit the function
      } catch (err: any) {
        const isTimeoutError = err.message?.includes("timed out") || err.message?.includes("did not respond");

        if (isTimeoutError && retryCount < maxRetries) {
          retryCount++;
          setError(`Server is waking up... Retrying (${retryCount}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before retry
          continue;
        }

        // Final error - no more retries
        setError(err.message || "Something went wrong. Please try again.");
        break;
      }
    }

    setLoading(false);
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
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white/90">Get started</h2>
            <p className="text-zinc-500 text-sm mt-2 font-medium">Create your professional account to build your bot</p>
          </div>
        </div>

        <div className="border rounded-[2.5rem] p-8 sm:p-12 shadow-2xl relative overflow-hidden bg-zinc-900/40 border-zinc-800 shadow-black">
          <form onSubmit={handleSignup} className="space-y-8 relative z-10">
            {error && (
              <div className="border text-xs font-bold p-4 rounded-2xl text-center bg-rose-500/10 border-rose-500/20 text-rose-300">
                {error}
              </div>
            )}

            <div className="space-y-5">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest ml-1 text-zinc-500">Full Name</label>
                <input
                  type="text"
                  placeholder="Enter your full name (e.g. John Doe)"
                  className="input-field"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest ml-1 text-zinc-500">Email Address</label>
                <input
                  type="email"
                  placeholder="Enter your work email address..."
                  className="input-field"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2 relative">
                <label className="text-[10px] font-black uppercase tracking-widest ml-1 text-zinc-500">Create Password</label>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password..."
                  className="input-field pr-12"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute bottom-4 right-4 text-zinc-500 hover:text-zinc-300 transition-colors p-1"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-start gap-3 py-2">
              <input
                type="checkbox"
                id="agreeTerms"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-1 w-4 h-4 rounded cursor-pointer bg-black border-zinc-800 text-[#6c4ef2] focus:ring-[#6c4ef2]/20"
                required
              />
              <label htmlFor="agreeTerms" className="text-[11px] font-bold uppercase tracking-widest cursor-pointer leading-relaxed text-zinc-500">
                I agree to the{" "}
                <Link href="/terms" target="_blank" className="text-white hover:underline">Terms</Link>{" "}
                &{" "}
                <Link href="/privacy" target="_blank" className="text-white hover:underline">Privacy</Link>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading || !agreeTerms}
              className="btn-primary w-full !py-4 shadow-xl"
            >
              {loading ? "Processing..." : "Register Account"}
            </button>
          </form>

          <div className="mt-10 relative z-10 border-t border-white/5 pt-8 text-center">
            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">
              Already have an account?{" "}
              <Link href="/login" className="text-white hover:underline ml-1">Sign In</Link>
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
