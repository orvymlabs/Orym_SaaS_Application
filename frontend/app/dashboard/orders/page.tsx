"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { useTheme } from "@/lib/useTheme";
import { api } from "@/lib/api";

// Define a type for the order structure
interface Order {
  id: number;
  customer_name: string;
  phone: string;
  product_name: string;
  quantity: number;
  address: string;
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
        <div className={`rounded-[2rem] border overflow-hidden ${isDark ? "bg-[#090909] border-zinc-800" : "bg-white border-slate-200"}`}>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className={`${isDark ? "bg-zinc-900" : "bg-slate-50"}`}>
                <tr>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Order ID</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Customer</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Phone</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Product</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Qty</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Address</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Status</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Date</th>
                  <th scope="col" className={`px-6 py-3 text-left text-xs font-bold uppercase tracking-wider ${isDark ? "text-zinc-400" : "text-slate-600"}`}>Actions</th>
                </tr>
              </thead>
              <tbody className={`divide-y ${isDark ? "bg-black divide-zinc-800" : "bg-white divide-slate-100"}`}>
                {orders.map((order) => (
                  <tr key={order.id} className={`${isDark ? "hover:bg-zinc-900/50" : "hover:bg-slate-50"}`}>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDark ? "text-zinc-300" : "text-slate-900"}`}>#{order.id}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? "text-zinc-300" : "text-slate-700"}`}>{order.customer_name}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>{order.phone}</td>
                    <td className={`px-6 py-4 text-sm ${isDark ? "text-zinc-300" : "text-slate-700"}`}>{order.product_name}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? "text-zinc-300" : "text-slate-700"}`}>{order.quantity}</td>
                    <td className={`px-6 py-4 text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>{order.address}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        order.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                        order.status === 'Completed' ? 'bg-green-100 text-green-800' :
                        order.status === 'Cancelled' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDark ? "text-zinc-400" : "text-slate-600"}`}>{new Date(order.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      {order.status !== 'Completed' && (
                        <button
                          onClick={() => handleComplete(order.id)}
                          className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-xs font-semibold"
                        >
                          Complete
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(order.id)}
                        className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
