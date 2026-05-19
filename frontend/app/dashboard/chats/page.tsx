"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";

export default function ConversationsPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [phones, setPhones] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPhone, setSelectedPhone] = useState<string>("");
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { isDark } = useTheme();

  // Fetch all conversations
  useEffect(() => {
    api("/api/chats?limit=200").then((data: any) => {
      setMessages(data);
      const unique = [...new Set(data.map((m: any) => m.phone_number))] as string[];
      setPhones(unique);
      if (unique.length > 0) setSelectedPhone(unique[0]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  // Fetch messages for selected phone
  useEffect(() => {
    if (selectedPhone) {
      api(`/api/chats?phone_number=${encodeURIComponent(selectedPhone)}&limit=100`).then((data: any) => {
        setChatMessages(data.reverse());
      }).catch(() => {});
    }
  }, [selectedPhone]);

  // Poll for new messages and seen status updates
  useEffect(() => {
    if (!selectedPhone) return;

    const pollInterval = setInterval(() => {
      api(`/api/chats?phone_number=${encodeURIComponent(selectedPhone)}&limit=100`)
        .then((data: any) => {
          // Check if there are new messages
          const lastMsg = chatMessages[chatMessages.length - 1];
          const newLastMsg = data[data.length - 1];

          if (data.length !== chatMessages.length ||
              (lastMsg && newLastMsg && lastMsg.id !== newLastMsg.id)) {
            setChatMessages(data.reverse());
          } else {
            // Update seen status for existing messages
            setChatMessages(prev => {
              const updated = [...prev];
              data.forEach((newMsg: any) => {
                const idx = updated.findIndex(m => m.id === newMsg.id);
                if (idx !== -1 && updated[idx].seen !== newMsg.seen) {
                  updated[idx] = { ...updated[idx], seen: newMsg.seen };
                }
              });
              return updated;
            });
          }
        })
        .catch(() => {});
    }, 3000); 

    return () => clearInterval(pollInterval);
  }, [selectedPhone, chatMessages]);

  const filteredPhones = phones.filter(p => p.toLowerCase().includes(searchQuery.toLowerCase()));

  if (loading) return <div className={`animate-pulse ${isDark ? "text-zinc-500" : "text-slate-500"}`}>Loading conversations...</div>;

  return (
    <div className="h-[calc(100vh-160px)] flex flex-col space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className={`text-3xl font-bold tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Chats</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} font-medium mt-1`}>Real-time log of bot-to-customer interactions.</p>
      </div>

      <div className="flex-1 flex gap-8 min-h-0">
        {/* Sidebar: Contacts */}
        <div className={`w-80 rounded-[2.5rem] border flex flex-col overflow-hidden shadow-2xl ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-slate-200/50"}`}>
          <div className={`p-6 border-b space-y-4 ${isDark ? "border-zinc-800 bg-zinc-900/50" : "border-slate-100 bg-slate-50/50"}`}>
            <h2 className="text-[10px] font-bold text-zinc-600 uppercase tracking-wide">Conversation History ({phones.length})</h2>
            <div className="search-input-wrapper">
              <svg className="search-input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <input 
                type="text" 
                placeholder="Search conversations, contacts..." 
                className="search-input-field !py-2 !text-xs"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {filteredPhones.map((phone, index) => (
              <button key={phone} onClick={() => setSelectedPhone(phone)}
                className={`w-full text-left p-6 border-b transition-all duration-300 group relative ${
                  isDark
                    ? (selectedPhone === phone ? "bg-white text-black border-white/10" : "hover:bg-zinc-900 border-zinc-800 text-zinc-500 hover:text-white")
                    : (selectedPhone === phone ? "bg-slate-50/50 border-slate-50 text-slate-600" : "hover:bg-slate-50 border-slate-50 text-slate-600")
                }`}>
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-[10px] transition-all duration-300 ${
                    selectedPhone === phone
                      ? `bg-black text-white`
                      : `${isDark ? "bg-zinc-800 text-zinc-500 group-hover:bg-zinc-700" : "bg-slate-100 text-slate-500"}`
                  }`}>
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-bold text-xs tracking-tight">{phone}</p>
                  </div>
                </div>
              </button>
            ))}
            {filteredPhones.length === 0 && (
              <div className="p-16 text-center space-y-4 opacity-30">
                <p className={`text-[10px] font-bold uppercase tracking-wide ${isDark ? "text-white" : "text-black"}`}>No matches found.</p>
              </div>
            )}
          </div>
        </div>

        {/* Chat Window */}
        <div className={`flex-1 rounded-[3rem] border shadow-2xl flex flex-col overflow-hidden relative ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-slate-200/50"}`}>
          {!selectedPhone ? (
            <div className="flex-1 flex flex-col items-center justify-center p-10 text-center space-y-6">
              <div className={`w-24 h-24 rounded-full flex items-center justify-center text-4xl shadow-2xl ${isDark ? "bg-zinc-800 text-white" : "bg-slate-50"}`}>💬</div>
              <div>
                <h2 className={`text-2xl font-bold tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Select a Chat</h2>
                <p className={`text-sm font-medium max-w-xs mt-2 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Select a contact from the list to view their full message history.</p>
              </div>
            </div>
          ) : (
            <>
              <div className={`p-8 border-b backdrop-blur-3xl flex items-center justify-between sticky top-0 z-10 ${isDark ? "border-zinc-800 bg-black/60" : "border-slate-100 bg-white/80"}`}>
                <div className="flex items-center gap-5">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-xs shadow-2xl ${isDark ? "bg-white text-black" : "bg-slate-900 text-white"}`}>
                    {filteredPhones.indexOf(selectedPhone) + 1}
                  </div>
                  <div>
                    <h2 className={`text-lg font-bold tracking-tight leading-tight ${isDark ? "text-white" : "text-slate-900"}`}>{selectedPhone}</h2>
                  </div>
                </div>
                <button className="btn-icon">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                </button>
              </div>

              <div className={`flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar ${isDark ? "bg-black" : "bg-slate-50/30"}`}>
                {chatMessages.map((m: any) => (
                  <div key={m.id} className={`flex flex-col ${m.sender === "user" ? "items-start" : "items-end"} group animate-in fade-in slide-in-from-bottom-2 duration-500`}>
                    <div className={`max-w-[75%] rounded-[2rem] px-8 py-5 shadow-2xl text-sm font-medium tracking-tight leading-relaxed ${
                      m.sender === "user"
                      ? `${isDark ? "bg-zinc-900 text-zinc-100 border border-zinc-800" : "bg-white text-slate-700 border border-slate-100"} rounded-bl-none`
                      : `bg-white text-black rounded-br-none ${isDark ? "shadow-white/5" : "shadow-blue-100"}`
                    }`}>
                      <p>{m.message}</p>
                    </div>
                    <div className="flex items-center gap-3 mt-3 px-3">
                      <p className={`text-[9px] font-bold uppercase tracking-wide ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                        {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      {m.sender === "bot" && (
                        <div className="flex items-center gap-1">
                          <span className={`text-[10px] font-bold uppercase tracking-wide flex items-center gap-0.5 ${m.seen ? "text-zinc-400" : "text-zinc-700"}`}>
                            {m.seen ? "READ" : "DELIVERED"}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {chatMessages.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-24 opacity-20">
                    <p className={`text-[10px] font-bold uppercase tracking-wide ${isDark ? "text-white" : "text-black"}`}>No messages</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
