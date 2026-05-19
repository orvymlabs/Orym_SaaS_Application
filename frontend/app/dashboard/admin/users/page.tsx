"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut, apiDelete, apiPatch } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ui";

interface Plan {
  id: number;
  plan_name: string;
}

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  plan: string;
  created_at: string;
  bot?: { status: boolean };
}

export default function UserManagementPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRole, setFilterRole] = useState<string>("all");
  const [filterPlan, setFilterPlan] = useState<string>("all");
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const { showToast, ToastContainer } = useToast();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "user",
    plan: "free",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [u, p] = await Promise.all([
        apiGet<User[]>("/api/admin/users"),
        apiGet<Plan[]>("/api/admin/plans")
      ]);
      setUsers(u);
      setPlans(p);
    } catch (err: any) {
      showToast(err.message || "Failed to fetch data", "error");
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesRole = filterRole === "all" || user.role === filterRole;
    const matchesPlan = filterPlan === "all" || user.plan === filterPlan;
    return matchesSearch && matchesRole && matchesPlan;
  });

  const openCreateModal = () => {
    setEditingUser(null);
    setFormData({ email: "", password: "", full_name: "", role: "user", plan: plans[0]?.plan_name || "free" });
    setShowModal(true);
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      password: "",
      full_name: user.full_name || "",
      role: user.role,
      plan: user.plan,
    });
    setShowModal(true);
  };

  const handleSubmit = async () => {
    try {
      if (editingUser) {
        // Refactored to use general admin update if possible, or stay with specific one
        await apiPut(`/api/auth/admin/update-user/${editingUser.id}`, {
          email: formData.email,
          full_name: formData.full_name,
          role: formData.role,
          plan: formData.plan,
        });
        showToast("User updated successfully", "success");
      } else {
        if (!formData.password) {
          showToast("Password is required", "error");
          return;
        }
        await apiPost("/api/auth/admin/create-user", formData);
        showToast("User created successfully", "success");
      }
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Operation failed", "error");
    }
  };

  const deleteUser = async (userId: number) => {
    if (!confirm("Are you sure? This will delete all user data.")) return;
    try {
      await apiDelete(`/api/admin/users/${userId}`);
      showToast("User deleted successfully", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to delete user", "error");
    }
  };

  const toggleBotStatus = async (userId: number) => {
    try {
      await apiPut(`/api/admin/users/${userId}/suspend`, {});
      showToast("Bot status updated", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to update status", "error");
    }
  };

  const updatePlan = async (userId: number, newPlan: string) => {
    try {
      await apiPut(`/api/admin/users/${userId}/plan?plan_name=${newPlan}`, {});
      showToast(`User plan updated to ${newPlan}`, "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to update plan", "error");
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">User Management</h1>
          <p className="text-zinc-500 font-medium mt-1">Manage platform users, roles, and service tiers</p>
        </div>
        <button
          onClick={openCreateModal}
          className="btn-primary"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
          Add New User
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#090909] p-6 rounded-[2.5rem] border border-zinc-800 shadow-2xl">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="sm:col-span-2">
            <div className="search-input-wrapper">
              <svg className="search-input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search by email or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input-field !py-2.5 !text-xs"
              />
            </div>
          </div>
          <select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            className="select-field !py-2.5 !text-xs"
          >
            <option value="all">All Roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
            <option value="super_admin">Super Admin</option>
          </select>
          <select
            value={filterPlan}
            onChange={(e) => setFilterPlan(e.target.value)}
            className="select-field !py-2.5 !text-xs"
          >
            <option value="all">All Plans</option>
            {plans.map(p => (
              <option key={p.id} value={p.plan_name}>{p.plan_name.charAt(0).toUpperCase() + p.plan_name.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-zinc-500 animate-pulse font-black uppercase tracking-widest text-[10px]">Loading User Registry...</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-black/20 border-b border-zinc-800">
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">User Credential</th>
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Service Tier</th>
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Auth Level</th>
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em] text-center">Bot Sync</th>
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em]">Join Date</th>
                  <th className="px-8 py-6 text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em] text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {filteredUsers.map(user => (
                  <tr key={user.id} className="transition-all hover:bg-white/5 group">
                    <td className="px-8 py-6">
                      <div>
                        <p className="font-black text-white text-sm tracking-tight">{user.email}</p>
                        {user.full_name && <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 mt-1">{user.full_name}</p>}
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <select
                        value={user.plan}
                        onChange={(e) => updatePlan(user.id, e.target.value)}
                        className={`btn-pill py-1 !text-[9px] !bg-transparent focus:ring-0 cursor-pointer ${
                          user.plan !== 'free' ? '!text-violet-400 !border-violet-500/30' : '!text-zinc-500 !border-zinc-800'
                        }`}
                      >
                        {plans.map(p => (
                          <option key={p.id} value={p.plan_name}>{p.plan_name.charAt(0).toUpperCase() + p.plan_name.slice(1)}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-8 py-6">
                      <span className={`btn-pill py-1 !text-[9px] border-none ${
                        user.role === 'super_admin' ? 'bg-amber-500 text-white' :
                        user.role === 'admin' ? 'bg-emerald-500 text-white' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-8 py-6 text-center">
                      <button
                        onClick={() => toggleBotStatus(user.id)}
                        className={`btn-pill py-1 !text-[9px] border-none shadow-lg ${
                          user.bot?.status !== false
                            ? 'bg-emerald-500 text-white shadow-emerald-500/20'
                            : 'bg-rose-500 text-white shadow-rose-500/20'
                        }`}
                      >
                        {user.bot?.status !== false ? 'Live' : 'Offline'}
                      </button>
                    </td>
                    <td className="px-8 py-6 text-[11px] font-black uppercase tracking-widest text-zinc-600">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-8 py-6 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => router.push(`/dashboard/admin/users/view?id=${user.id}`)}
                          className="btn-icon"
                          title="Detailed View"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => openEditModal(user)}
                          className="btn-icon text-slate-400 hover:text-slate-500"
                          title="Modify Record"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => deleteUser(user.id)}
                          className="btn-icon text-rose-500 hover:text-rose-600"
                          title="Purge Data"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && filteredUsers.length === 0 && (
          <div className="text-center py-32 opacity-30">
            <p className="text-[10px] font-black uppercase tracking-[0.4em]">No Records Matching Parameters</p>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-6">
          <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
              <h3 className="text-xl font-black text-white tracking-tight">{editingUser ? "Modify User Record" : "Onboard New User"}</h3>
              <button onClick={() => setShowModal(false)} className="btn-icon">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-10 space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Email Identifier</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="user@enterprise.com"
                />
              </div>
              {!editingUser && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Initial Auth Key</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="input-field"
                    placeholder="Create secure access key..."
                  />
                </div>
              )}
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Full Identity</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input-field"
                  placeholder="Official Name..."
                />
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Nexus Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="select-field"
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                    <option value="super_admin">Super Admin</option>
                  </select>
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Service Tier</label>
                  <select
                    value={formData.plan}
                    onChange={(e) => setFormData({ ...formData, plan: e.target.value })}
                    className="select-field"
                  >
                    {plans.map(p => (
                      <option key={p.id} value={p.plan_name}>{p.plan_name.charAt(0).toUpperCase() + p.plan_name.slice(1)}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="px-10 py-8 border-t border-zinc-800 flex gap-4 bg-zinc-900/50">
              <button
                onClick={() => setShowModal(false)}
                className="btn-secondary flex-1"
              >
                Abort
              </button>
              <button
                onClick={handleSubmit}
                className="btn-primary flex-1"
              >
                {editingUser ? "Sync Changes" : "Commit Onboarding"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
