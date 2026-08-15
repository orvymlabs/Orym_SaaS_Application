"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";
import { api } from "@/lib/api";

// Define a type for the order structure
interface Order {
  id: number;
  phone: string;
  order_details: string;
  status: string;
  created_at: string; // ISO format string
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userPlan, setUserPlan] = useState<string>("free");
  const { isDark } = useTheme();

  useEffect(() => {
    // Fetch user plan
    api("/api/auth/me").then((userData) => {
      if (userData && userData.plan) {
        setUserPlan(userData.plan.toLowerCase());
      }
    }).catch(() => {});
  }, []);

  const fetchOrders = async () => {
    try {
      const data = await apiGet<Order[]>("/api/orders");
      console.log("📦 Orders API Response:", data);
      console.log("📦 Total orders received:", data.length);

      // Log each order's details
      data.forEach((order, index) => {
        console.log(`📦 Order #${order.id}:`, {
          phone: order.phone,
          status: order.status,
          order_details_length: order.order_details ? order.order_details.length : 0,
          order_details_preview: order.order_details ? order.order_details.substring(0, 50) : '[EMPTY]'
        });
      });

      setOrders(data);
      setError(null);
    } catch (err: any) {
      console.error("Failed to fetch orders:", err);
      setError(err.message || "Failed to load orders. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleComplete = async (orderId: number) => {
    try {
      await api(`/api/orders/${orderId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: "Completed" })
      });
      // Refresh orders list
      fetchOrders();
    } catch (err: any) {
      console.error("Failed to complete order:", err);
      alert("Failed to mark order as completed");
    }
  };

  const handleDelete = async (orderId: number) => {
    if (!confirm("Are you sure you want to delete this order?")) {
      return;
    }
    try {
      await api(`/api/orders/${orderId}`, {
        method: "DELETE"
      });
      // Refresh orders list
      fetchOrders();
    } catch (err: any) {
      console.error("Failed to delete order:", err);
      alert("Failed to delete order");
    }
  };

  /* ---------------- LOADING UI ---------------- */
  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-8 p-8">
          <div className="h-8 w-64 bg-slate-200 rounded-lg" />
          <div className="h-32 bg-slate-100 rounded-[2rem]" />
          <div className="h-32 bg-slate-100 rounded-[2rem]" />
          <div className="h-32 bg-slate-100 rounded-[2rem]" />
        </div>
      </div>
    );
  }

  /* ---------------- ERROR UI ---------------- */
  if (error) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-full min-h-[400px] text-red-500 font-semibold">
          {error}
        </div>
      </div>
    );
  }

  /* ---------------- MAIN UI ---------------- */

  // Check if order form is locked for FREE plan
  if (userPlan === "free") {
    return (
      <div className="space-y-6">
        <div>
          <h1 className={`text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Submissions</h1>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-2`}>Manage customer submissions from WhatsApp</p>
        </div>

        {/* Locked State for FREE Plan */}
        <div className={`rounded-[3rem] border-2 p-16 text-center ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
          <div className="max-w-md mx-auto space-y-6">
            {/* Lock Icon */}
            <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center ${isDark ? "bg-zinc-900" : "bg-slate-100"}`}>
              <svg className={`w-10 h-10 ${isDark ? "text-zinc-600" : "text-slate-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </div>

            {/* Title */}
            <div>
              <h2 className={`text-2xl font-bold ${isDark ? "text-white" : "text-slate-900"}`}>
                Submission Form Feature Locked
              </h2>
              <p className={`mt-3 text-sm ${isDark ? "text-zinc-500" : "text-slate-500"}`}>
                The submission form and submissions feature is available on STARTER and PREMIUM plans.
              </p>
            </div>

            {/* Features List */}
            <div className={`text-left p-6 rounded-2xl ${isDark ? "bg-black border border-zinc-800" : "bg-slate-50 border border-slate-200"}`}>
              <p className={`text-xs font-bold uppercase tracking-wide mb-3 ${isDark ? "text-zinc-600" : "text-slate-400"}`}>
                Unlock with STARTER or PREMIUM:
              </p>
              <ul className="space-y-2">
                <li className={`flex items-start gap-2 text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Collect customer submissions via WhatsApp</span>
                </li>
                <li className={`flex items-start gap-2 text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Manage submissions in dashboard</span>
                </li>
                <li className={`flex items-start gap-2 text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Track submission status and history</span>
                </li>
                <li className={`flex items-start gap-2 text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Automated submission confirmations</span>
                </li>
              </ul>
            </div>

            {/* Upgrade Button */}
            <a
              href="/dashboard/subscription"
              className={`inline-block px-8 py-4 rounded-2xl font-bold text-sm transition-all ${
                isDark
                  ? "bg-white text-black hover:bg-zinc-100"
                  : "bg-slate-900 text-white hover:bg-slate-800"
              }`}
            >
              Upgrade to Unlock Submission Form
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Submissions</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-2`}>Manage customer submissions from WhatsApp</p>
      </div>

      {orders.length === 0 ? (
        <div className={`rounded-[2rem] border p-12 text-center ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
          <p className={`${isDark ? "text-zinc-500" : "text-slate-500"}`}>No orders found yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className={`rounded-[2rem] border p-8 ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className={`text-lg font-bold ${isDark ? "text-white" : "text-slate-900"}`}>Submission #{order.id}</h3>
                  <p className={`text-sm mt-1 ${isDark ? "text-zinc-500" : "text-slate-500"}`}>
                    {new Date(order.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                    order.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                    order.status === 'Processing' ? 'bg-blue-100 text-blue-800' :
                    order.status === 'Completed' ? 'bg-green-100 text-green-800' :
                    order.status === 'Cancelled' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {order.status}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className={`text-xs font-bold uppercase tracking-wide ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Customer WhatsApp</label>
                  <p className={`mt-1 ${isDark ? "text-zinc-300" : "text-slate-700"}`}>{order.phone}</p>
                </div>

                <div>
                  <label className={`text-xs font-bold uppercase tracking-wide ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Submission Details</label>
                  {order.order_details ? (
                    <pre className={`mt-2 p-4 rounded-xl text-sm whitespace-pre-wrap font-mono ${isDark ? "bg-black text-zinc-300" : "bg-slate-50 text-slate-700"}`}>
                      {order.order_details}
                    </pre>
                  ) : (
                    <div className={`mt-2 p-4 rounded-xl text-sm ${isDark ? "bg-black text-zinc-500 border border-zinc-800" : "bg-slate-50 text-slate-400 border border-slate-200"}`}>
                      <p className="italic">No submission details available for this submission.</p>
                      <p className="text-xs mt-1">This submission was created before the form submission feature was implemented.</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                {order.status !== 'Completed' && (
                  <button
                    onClick={() => handleComplete(order.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors text-sm font-semibold"
                  >
                    Mark as Completed
                  </button>
                )}
                <button
                  onClick={() => handleDelete(order.id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors text-sm font-semibold"
                >
                  Delete Order
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
