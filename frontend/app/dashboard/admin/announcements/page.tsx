"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";

interface Announcement {
  id: number;
  title: string;
  message: string;
  priority: "low" | "normal" | "high" | "urgent";
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
  created_by_email: string;
}

export default function AdminAnnouncementsPage() {
  const router = useRouter();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    message: "",
    priority: "normal",
    expires_at: "",
    recipients: "all",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const fetchAnnouncements = async () => {
    try {
      const data = await apiGet("/api/auth/admin/announcements");
      setAnnouncements(data || []);
    } catch (err) {
      console.error("Failed to fetch announcements:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      if (editingId) {
        await apiPut(`/api/auth/admin/announcements/${editingId}`, formData);
        setSuccess("Announcement updated successfully");
      } else {
        await apiPost("/api/admin/broadcast", formData);
        setSuccess("Broadcast deployed successfully");
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({ title: "", message: "", priority: "normal", expires_at: "", recipients: "all" });
      fetchAnnouncements();
    } catch (err: any) {
      setError(err.message || "Failed to save announcement");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (announcement: Announcement) => {
    setEditingId(announcement.id);
    setFormData({
      title: announcement.title,
      message: announcement.message,
      priority: announcement.priority,
      expires_at: announcement.expires_at ? new Date(announcement.expires_at).toISOString().slice(0, 16) : "",
      recipients: "all",
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this announcement?")) return;

    try {
      await apiDelete(`/api/auth/admin/announcements/${id}`);
      setSuccess("Announcement deleted successfully");
      fetchAnnouncements();
    } catch (err: any) {
      setError(err.message || "Failed to delete announcement");
    }
  };

  const handleToggleActive = async (announcement: Announcement) => {
    try {
      await apiPut(`/api/auth/admin/announcements/${announcement.id}`, {
        is_active: !announcement.is_active
      });
      fetchAnnouncements();
    } catch (err) {
      setError("Failed to update announcement");
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "urgent":
        return <span className="btn-pill bg-rose-500 text-white border-none shadow-lg shadow-rose-500/20">URGENT</span>;
      case "high":
        return <span className="btn-pill bg-orange-500 text-white border-none shadow-lg shadow-orange-500/20">HIGH</span>;
      case "normal":
        return <span className="btn-pill bg-[#6c4ef2] text-white border-none shadow-lg shadow-blue-500/20">NORMAL</span>;
      case "low":
        return <span className="btn-pill bg-zinc-800 text-zinc-400 border-none">LOW</span>;
      default:
        return <span className="btn-pill bg-zinc-800 text-zinc-400 border-none">{priority.toUpperCase()}</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Retrieving Global Broadcasts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">Global Broadcasts</h1>
          <p className="text-zinc-500 font-medium mt-1">Deploy platform-wide neural notifications</p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingId(null);
            setFormData({ title: "", message: "", priority: "normal", expires_at: "", recipients: "all" });
          }}
          className={showForm ? "btn-secondary" : "btn-primary"}
        >
          {showForm ? "Abort Operation" : "+ New Broadcast"}
        </button>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 px-8 py-5 rounded-2xl font-bold text-sm text-center animate-in zoom-in-95">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-8 py-5 rounded-2xl font-bold text-sm text-center animate-in zoom-in-95">
          {success}
        </div>
      )}

      {/* Create/Edit Form */}
      {showForm && (
        <div className="bg-[#090909] border border-zinc-800 rounded-[3rem] p-10 shadow-2xl animate-in slide-in-from-top-4 duration-300">
          <h2 className="text-xl font-black text-white tracking-tight mb-8">
            {editingId ? "Modify Neural Broadcast" : "Initialize New Broadcast"}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Target Recipients</label>
                <select
                  value={formData.recipients}
                  onChange={(e) => setFormData({ ...formData, recipients: e.target.value })}
                  className="select-field"
                >
                  <option value="all">All Users</option>
                  <option value="free">Free Plan Users</option>
                  <option value="starter">Starter Plan Users</option>
                  <option value="premium">Premium Plan Users</option>
                  <option value="specific">Specific User (Email)</option>
                </select>
              </div>
              {formData.recipients !== "all" && !["free", "starter", "premium"].includes(formData.recipients) && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Recipient Email</label>
                  <input
                    type="email"
                    value={formData.recipients === "specific" ? "" : formData.recipients}
                    onChange={(e) => setFormData({ ...formData, recipients: e.target.value })}
                    className="input-field"
                    placeholder="user@example.com"
                    required
                  />
                </div>
              )}
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Broadcast Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="input-field"
                placeholder="e.g. Nexus Core Maintenance Scheduled..."
                required
              />
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Message Payload</label>
              <textarea
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                rows={4}
                className="textarea-field"
                placeholder="Enter the broadcast message content..."
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Priority Protocol</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="select-field"
                >
                  <option value="low">Low Priority</option>
                  <option value="normal">Normal Operation</option>
                  <option value="high">High Priority</option>
                  <option value="urgent">Urgent Intervention</option>
                </select>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Expiry Timestamp (optional)</label>
                <input
                  type="datetime-local"
                  value={formData.expires_at}
                  onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
                  className="input-field"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="btn-primary w-full !py-4 shadow-xl shadow-[#6c4ef2]/20"
            >
              {saving ? "Processing..." : editingId ? "Commit Updates" : "Deploy Broadcast"}
            </button>
          </form>
        </div>
      )}

      {/* Announcements List */}
      <div className="space-y-6">
        {announcements.length === 0 ? (
          <div className="bg-[#090909] border border-zinc-800 rounded-[3rem] p-32 text-center opacity-30 shadow-2xl">
            <svg className="w-24 h-24 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">No Broadcasts Detected</p>
          </div>
        ) : (
          announcements.map((announcement) => (
            <div
              key={announcement.id}
              className={`bg-[#090909] border rounded-[2.5rem] p-8 transition-all duration-300 shadow-2xl ${
                announcement.is_active ? "border-zinc-800 shadow-black" : "border-zinc-900 opacity-50 grayscale shadow-none"
              }`}
            >
              <div className="flex flex-col lg:flex-row items-start justify-between gap-8">
                <div className="flex-1 space-y-4">
                  <div className="flex items-center gap-4 flex-wrap">
                    <h3 className="text-xl font-black text-white tracking-tight">{announcement.title}</h3>
                    {getPriorityBadge(announcement.priority)}
                    {!announcement.is_active && (
                      <span className="btn-pill bg-zinc-900 text-zinc-600 border-zinc-800">DORMANT</span>
                    )}
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed font-medium whitespace-pre-wrap">{announcement.message}</p>
                  <div className="flex items-center gap-5 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Operator:</span>
                      <span className="text-[10px] font-bold text-white">{announcement.created_by_email}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Created:</span>
                      <span className="text-[10px] font-bold text-white">{new Date(announcement.created_at).toLocaleDateString()}</span>
                    </div>
                    {announcement.expires_at && (
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Expiry:</span>
                        <span className="text-[10px] font-bold text-rose-400">{new Date(announcement.expires_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end lg:self-center">
                  <button
                    onClick={() => handleToggleActive(announcement)}
                    className={`btn-pill py-2 px-6 border-none shadow-lg ${
                      announcement.is_active
                        ? "bg-emerald-500 text-white shadow-emerald-500/20"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {announcement.is_active ? "LIVE" : "DORMANT"}
                  </button>
                  <button
                    onClick={() => handleEdit(announcement)}
                    className="btn-pill py-2 px-6 bg-white text-black border-none shadow-xl hover:bg-zinc-200"
                  >
                    MODIFY
                  </button>
                  <button
                    onClick={() => handleDelete(announcement.id)}
                    className="btn-pill py-2 px-6 bg-rose-500 text-white border-none shadow-lg shadow-rose-500/20 hover:bg-rose-600"
                  >
                    PURGE
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
