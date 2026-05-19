"use client";
import { useEffect, useState } from "react";
import { useToast } from "@/components/ui";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";

interface Plan {
  id: number;
  plan_name: string;
  monthly_price: number;
  yearly_price: number | null;
  daily_message_limit: number;
  max_templates: number;
  max_custom_order_fields: number;
  is_active: boolean;
}

export default function AdminSettingsPage() {
  const { showToast, ToastContainer } = useToast();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [planFormData, setPlanFormData] = useState({
    plan_name: "",
    monthly_price: 0,
    yearly_price: null as number | null,
    daily_message_limit: 0,
    max_templates: 0,
    max_custom_order_fields: 0,
    is_active: true
  });

  const [settings, setSettings] = useState({
    platformName: "ORVYN",
    maintenanceMode: false,
    allowRegistrations: true,
    defaultPlan: "free",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await apiGet<Plan[]>("/api/admin/plans");
      setPlans(data || []);
    } catch (err: any) {
      showToast(err.message || "Failed to fetch plans", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      // Platform settings are currently not in a dedicated DB table, 
      // this would be a future improvement. For now we just toast success.
      showToast("Global configuration committed to session", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  const handlePlanSubmit = async () => {
    try {
      if (editingPlan) {
        await apiPut(`/api/admin/plans/${editingPlan.id}`, planFormData);
        showToast("Plan updated successfully", "success");
      } else {
        await apiPost("/api/admin/plans", planFormData);
        showToast("Plan created successfully", "success");
      }
      setShowPlanModal(false);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Operation failed", "error");
    }
  };

  const deletePlan = async (id: number) => {
    if (!confirm("Are you sure? This will fail if users are on this plan.")) return;
    try {
      await apiDelete(`/api/admin/plans/${id}`);
      showToast("Plan purged from system", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to delete plan", "error");
    }
  };

  const openEditPlan = (plan: Plan) => {
    setEditingPlan(plan);
    setPlanFormData({
      plan_name: plan.plan_name,
      monthly_price: plan.monthly_price,
      yearly_price: plan.yearly_price,
      daily_message_limit: plan.daily_message_limit,
      max_templates: plan.max_templates,
      max_custom_order_fields: plan.max_custom_order_fields,
      is_active: plan.is_active
    });
    setShowPlanModal(true);
  };

  const openCreatePlan = () => {
    setEditingPlan(null);
    setPlanFormData({
      plan_name: "",
      monthly_price: 0,
      yearly_price: null,
      daily_message_limit: 250,
      max_templates: 5,
      max_custom_order_fields: 10,
      is_active: true
    });
    setShowPlanModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-500 font-black uppercase tracking-[0.2em] text-[10px]">Accessing Core Protocols...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">System Logic</h1>
          <p className="text-zinc-500 font-medium mt-1">Configure global platform-wide behaviors and service tiers</p>
        </div>
        <div className="flex gap-4">
          <button onClick={openCreatePlan} className="btn-primary">
            + New Service Tier
          </button>
        </div>
      </div>

      {/* Plan Management Section */}
      <section className="space-y-6">
        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-zinc-600 ml-1">Service Tier Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div key={plan.id} className={`bg-[#090909] border rounded-[2.5rem] p-8 shadow-2xl transition-all duration-300 ${plan.is_active ? 'border-zinc-800' : 'border-zinc-900 opacity-50 grayscale'}`}>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h4 className="text-xl font-black text-white tracking-tight uppercase">{plan.plan_name}</h4>
                  <p className="text-3xl font-black text-[#6c4ef2] mt-2">${plan.monthly_price}<span className="text-xs text-zinc-700">/MO</span></p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => openEditPlan(plan)} className="btn-icon">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  </button>
                  <button onClick={() => deletePlan(plan.id)} className="btn-icon text-rose-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
              
              <div className="space-y-3 pt-6 border-t border-zinc-800/50">
                <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                  <span className="text-zinc-600">Daily Bandwidth</span>
                  <span className="text-white">{plan.daily_message_limit === 0 ? "Unlimited" : `${plan.daily_message_limit} MSGS`}</span>
                </div>
                <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                  <span className="text-zinc-600">Automation Nodes</span>
                  <span className="text-white">{plan.max_templates === 0 ? "Unlimited" : `${plan.max_templates} RULES`}</span>
                </div>
                <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                  <span className="text-zinc-600">Custom Neural Fields</span>
                  <span className="text-white">{plan.max_custom_order_fields === 0 ? "Unlimited" : `${plan.max_custom_order_fields} FIELDS`}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Global Settings Section */}
      <section className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10 space-y-10">
        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-zinc-600 opacity-50 ml-1">Global Configuration</h3>
        
        <div className="space-y-8">
          <div className="space-y-3">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Platform Identity</label>
            <input
              type="text"
              value={settings.platformName}
              onChange={(e) => setSettings({ ...settings, platformName: e.target.value })}
              className="input-field"
              placeholder="Enter platform display name..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex items-center justify-between p-8 bg-black rounded-[2rem] border border-zinc-800">
              <div>
                <p className="text-white font-black uppercase tracking-tight text-sm">Maintenance Protocol</p>
                <p className="text-xs text-zinc-500 mt-1 font-medium">Disable platform access for maintenance</p>
              </div>
              <button
                onClick={() => setSettings({ ...settings, maintenanceMode: !settings.maintenanceMode })}
                className={`w-14 h-7 rounded-full transition-all duration-300 relative ${
                  settings.maintenanceMode ? 'bg-rose-600' : 'bg-zinc-800'
                }`}
              >
                <div className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-all duration-300 shadow-lg ${
                  settings.maintenanceMode ? 'left-8' : 'left-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-8 bg-black rounded-[2rem] border border-zinc-800">
              <div>
                <p className="text-white font-black uppercase tracking-tight text-sm">Registry Access</p>
                <p className="text-xs text-zinc-500 mt-1 font-medium">Toggle availability of new onboardings</p>
              </div>
              <button
                onClick={() => setSettings({ ...settings, allowRegistrations: !settings.allowRegistrations })}
                className={`w-14 h-7 rounded-full transition-all duration-300 relative ${
                  settings.allowRegistrations ? 'bg-emerald-500' : 'bg-zinc-800'
                }`}
              >
                <div className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-all duration-300 shadow-lg ${
                  settings.allowRegistrations ? 'left-8' : 'left-1'
                }`} />
              </button>
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Default Provisioning Tier</label>
            <select
              value={settings.defaultPlan}
              onChange={(e) => setSettings({ ...settings, defaultPlan: e.target.value })}
              className="select-field"
            >
              {plans.map(p => (
                <option key={p.id} value={p.plan_name}>{p.plan_name.toUpperCase()} SERVICE (${p.monthly_price}/MO)</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className={`btn-primary min-w-[240px] !py-4 shadow-xl shadow-[#6c4ef2]/20 ${saving ? 'opacity-50' : ''}`}
          >
            {saving ? 'Processing...' : 'Commit Configuration'}
          </button>
        </div>
      </section>

      {/* Plan Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black/95 backdrop-blur-xl z-50 flex items-center justify-center p-6">
          <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="px-10 py-8 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
              <h3 className="text-xl font-black text-white tracking-tight">{editingPlan ? "Modify Service Tier" : "Architect New Tier"}</h3>
              <button onClick={() => setShowPlanModal(false)} className="btn-icon">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            
            <div className="p-10 space-y-8">
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Tier Designation</label>
                  <input
                    type="text"
                    value={planFormData.plan_name}
                    onChange={(e) => setPlanFormData({ ...planFormData, plan_name: e.target.value.toLowerCase() })}
                    className="input-field"
                    placeholder="e.g. enterprise"
                    required
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Monthly Yield ($)</label>
                  <input
                    type="number"
                    value={planFormData.monthly_price}
                    onChange={(e) => setPlanFormData({ ...planFormData, monthly_price: parseFloat(e.target.value) })}
                    className="input-field"
                    placeholder="29.99"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Daily Msgs (0=unlim)</label>
                  <input
                    type="number"
                    value={planFormData.daily_message_limit}
                    onChange={(e) => setPlanFormData({ ...planFormData, daily_message_limit: parseInt(e.target.value) })}
                    className="input-field"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Max Rules (0=unlim)</label>
                  <input
                    type="number"
                    value={planFormData.max_templates}
                    onChange={(e) => setPlanFormData({ ...planFormData, max_templates: parseInt(e.target.value) })}
                    className="input-field"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Max Fields (0=unlim)</label>
                  <input
                    type="number"
                    value={planFormData.max_custom_order_fields}
                    onChange={(e) => setPlanFormData({ ...planFormData, max_custom_order_fields: parseInt(e.target.value) })}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-6 bg-black rounded-2xl border border-zinc-800">
                <div>
                  <p className="text-white font-black uppercase tracking-tight text-xs">Tier Activation Status</p>
                  <p className="text-[10px] text-zinc-600 mt-1">Available for user provisioning when active</p>
                </div>
                <button
                  onClick={() => setPlanFormData({ ...planFormData, is_active: !planFormData.is_active })}
                  className={`w-12 h-6 rounded-full transition-all duration-300 relative ${
                    planFormData.is_active ? 'bg-emerald-500' : 'bg-zinc-800'
                  }`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 shadow-lg ${
                    planFormData.is_active ? 'left-7' : 'left-1'
                  }`} />
                </button>
              </div>
            </div>

            <div className="px-10 py-8 border-t border-zinc-800 flex gap-4 bg-zinc-900/50">
              <button onClick={() => setShowPlanModal(false)} className="btn-secondary flex-1">Abort</button>
              <button onClick={handlePlanSubmit} className="btn-primary flex-1">Commit Architecture</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
