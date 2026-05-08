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
  const { isDark } = useTheme();

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
  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>Orders</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} mt-2`}>Manage customer orders from WhatsApp</p>
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
                  <h3 className={`text-lg font-bold ${isDark ? "text-white" : "text-slate-900"}`}>Order #{order.id}</h3>
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
                  <label className={`text-xs font-bold uppercase tracking-wide ${isDark ? "text-zinc-600" : "text-slate-400"}`}>Order Details</label>
                  {order.order_details ? (
                    <pre className={`mt-2 p-4 rounded-xl text-sm whitespace-pre-wrap font-mono ${isDark ? "bg-black text-zinc-300" : "bg-slate-50 text-slate-700"}`}>
                      {order.order_details}
                    </pre>
                  ) : (
                    <div className={`mt-2 p-4 rounded-xl text-sm ${isDark ? "bg-black text-zinc-500 border border-zinc-800" : "bg-slate-50 text-slate-400 border border-slate-200"}`}>
                      <p className="italic">No order details available for this order.</p>
                      <p className="text-xs mt-1">This order was created before the order form feature was implemented.</p>
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
