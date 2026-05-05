"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";

interface Message {
  id: number;
  sender: "user" | "bot";
  message: string;
  timestamp: string;
}

export default function SandboxPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [botInfo, setBotInfo] = useState<any>(null);
  const [integrations, setIntegrations] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isDark } = useTheme();

  useEffect(() => {
    Promise.all([
      api("/api/bots/me").catch(() => null),
      api("/api/integrations/me").catch(() => null),
    ]).then(([bot, integ]) => {
      setBotInfo(bot);
      setIntegrations(integ);
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setLoading(true);

    const tempUserMsg: Message = {
      id: Date.now(),
      sender: "user",
      message: userMsg,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await api("/api/bots/test-chat", {
        method: "POST",
        body: JSON.stringify({ message: userMsg }),
      });

      const botMsg: Message = {
        id: Date.now() + 1,
        sender: "bot",
        message: response.reply || "No response generated",
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: Date.now() + 1,
        sender: "bot",
        message: `Error: ${err.message || "Failed to connect to ORVYM engine"}.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  if (!botInfo) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className={`w-16 h-16 border-4 border-t-white rounded-full animate-spin mx-auto mb-4 ${isDark ? "border-zinc-800" : "border-slate-200"}`}></div>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-black uppercase tracking-widest text-[10px]`}>Initializing Sandbox...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col space-y-8 max-w-5xl mx-auto animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className={`text-4xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Sandbox</h1>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-1 font-medium`}>Simulate neural responses before live deployment.</p>
        </div>

        <div className="flex gap-2">
          <div className={`px-4 py-2.5 rounded-2xl border ${isDark ? "bg-[#090909] border-zinc-800 shadow-xl" : "bg-white border-slate-200 shadow-sm"} flex items-center gap-3`}>
            <span className={`text-[10px] font-black uppercase tracking-widest ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Mode:</span>
            <span className={`btn-pill btn-pill-active py-1 px-3`}>{botInfo.mode}</span>
          </div>
          <div className={`px-4 py-2.5 rounded-2xl border ${isDark ? "bg-[#090909] border-zinc-800 shadow-xl" : "bg-white border-slate-200 shadow-sm"} flex items-center gap-3`}>
            <span className={`w-2 h-2 rounded-full ${botInfo.status ? "bg-emerald-500 animate-pulse" : "bg-zinc-800"}`}></span>
            <span className={`text-[10px] font-black uppercase tracking-widest ${botInfo.status ? (isDark ? "text-emerald-400" : "text-emerald-600") : "text-zinc-600"}`}>
              {botInfo.status ? "Live" : "Offline"}
            </span>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className={`flex-1 rounded-[3rem] border shadow-2xl flex flex-col overflow-hidden ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200"}`}>
        {/* Chat Header */}
        <div className={`px-8 py-6 border-b flex items-center justify-between ${isDark ? "border-zinc-800 bg-zinc-900/50" : "border-slate-100 bg-slate-50/50"}`}>
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-xl ${isDark ? "bg-white text-black" : "bg-slate-500 text-white"}`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
            </div>
            <div>
              <h2 className={`font-black text-sm uppercase tracking-widest ${isDark ? "text-white" : "text-slate-900"}`}>Neural Test Field</h2>
              <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Direct Logic Debugging</p>
            </div>
          </div>
          <button
            onClick={handleClearChat}
            className="btn-icon"
            title="Clear Chat Log"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            <span className="text-[10px] font-black uppercase tracking-widest ml-2">Clear Log</span>
          </button>
        </div>

        {/* Messages Area */}
        <div className={`flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar ${isDark ? "bg-black" : "bg-slate-50/20"}`}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-30">
              <div className={`w-24 h-24 rounded-[2.5rem] flex items-center justify-center ${isDark ? "bg-zinc-900" : "bg-slate-50"}`}>
                <svg className={`w-12 h-12 ${isDark ? "text-zinc-700" : "text-slate-200"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
              </div>
              <div className="space-y-2">
                <p className={`text-[10px] font-black uppercase tracking-[0.4em] ${isDark ? "text-white" : "text-slate-900"}`}>Void</p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-500`}
            >
              <div className={`flex items-end gap-4 max-w-[85%] ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}>
                {msg.sender === "bot" && (
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-2xl ${isDark ? "bg-white text-black" : "bg-slate-500 text-white"}`}>
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1v-1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM7.5 13A2.5 2.5 0 005 15.5 2.5 2.5 0 007.5 18 2.5 2.5 0 0010 15.5 2.5 2.5 0 007.5 13zm9 0a2.5 2.5 0 00-2.5 2.5 2.5 2.5 0 002.5 2.5 2.5 2.5 0 002.5-2.5 2.5 2.5 0 00-2.5-2.5z"/>
                    </svg>
                  </div>
                )}
                <div className="space-y-2">
                  <div
                    className={`px-8 py-5 rounded-[2rem] text-sm font-medium leading-relaxed shadow-2xl ${
                      msg.sender === "user"
                        ? `${isDark ? "bg-zinc-900 text-white border border-zinc-800" : "bg-slate-500 text-white"} rounded-br-none`
                        : `${isDark ? "bg-white text-black" : "bg-white border border-slate-100 text-slate-700"} rounded-bl-none`
                    }`}
                  >
                    {msg.message}
                  </div>
                  <p className={`text-[9px] font-black uppercase tracking-widest px-4 ${msg.sender === "user" ? "text-right" : "text-left"} ${isDark ? "text-zinc-700" : "text-slate-400"}`}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start animate-in fade-in duration-300">
              <div className="flex items-end gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-xl ${isDark ? "bg-white text-black" : "bg-slate-500 text-white"}`}>
                  <svg className="w-5 h-5 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1v-1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
                  </svg>
                </div>
                <div className={`px-6 py-4 rounded-[1.5rem] rounded-bl-none shadow-2xl ${isDark ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-slate-100"}`}>
                  <div className="flex gap-2">
                    <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className={`p-8 border-t ${isDark ? "bg-zinc-900/50 border-zinc-800" : "bg-white border-slate-100"}`}>
          <div className="flex gap-4 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type a message to test your bot..."
              disabled={loading}
              className="input-field flex-1"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="btn-primary px-10"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
