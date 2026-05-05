"use client";
import { useState } from "react";
import { useToast } from "@/components/ui";
import { api } from "@/lib/api"; // Added import for api

export default function AdminSettingsPage() {
  const { showToast, ToastContainer } = useToast();
  const [settings, setSettings] = useState({
    platformName: "ORVYN",
    maintenanceMode: false,
    allowRegistrations: true,
    defaultPlan: "starter",
  });
  const [saving, setSaving] = useState(false); // Added saving state

  const handleSave = async () => {
    setSaving(true);
    try {
      // Assume the backend endpoint is /api/admin/settings for PATCH requests
      await api("/api/admin/settings", {
        method: "PATCH",
        body: JSON.stringify(settings),
      });
      showToast("Settings saved successfully", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <ToastContainer />

      <div>
        <h1 className="text-4xl font-black text-white tracking-tighter">System Logic</h1>
        <p className="text-zinc-500 font-medium mt-1">Configure global platform-wide behaviors and protocols</p>
      </div>

      {/* Platform Settings */}
      <div className="bg-[#090909] rounded-[3rem] border border-zinc-800 shadow-2xl p-10 space-y-10">
        <h3 className="text-xl font-black text-white tracking-tight uppercase tracking-widest text-xs opacity-50">Global Configuration</h3>
        
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

          <div className="flex items-center justify-between p-8 bg-black rounded-[2rem] border border-zinc-800">
            <div>
              <p className="text-white font-black uppercase tracking-tight text-sm">Maintenance Protocol</p>
              <p className="text-xs text-zinc-500 mt-1 font-medium">Disable platform access for scheduled maintenance cycles</p>
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
              <p className="text-xs text-zinc-500 mt-1 font-medium">Toggle availability of new account onboardings</p>
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

          <div className="space-y-3">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-1">Default Provisioning Tier</label>
            <select
              value={settings.defaultPlan}
              onChange={(e) => setSettings({ ...settings, defaultPlan: e.target.value })}
              className="select-field"
            >
              <option value="starter">Starter Service ($1/mo)</option>
              <option value="growth">Growth Service ($3/mo)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={saving} // Disable button while saving
          className={`btn-primary min-w-[240px] !py-4 ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {saving ? 'Saving...' : 'Commit Configuration'}
        </button>
      </div>
    </div>
  );
}