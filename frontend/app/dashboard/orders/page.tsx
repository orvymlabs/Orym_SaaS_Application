// frontend/app/dashboard/orders/page.tsx
"use client";

export default function OrdersPage() {
  return (
    <div className="p-12 max-w-7xl mx-auto">
      <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">Orders</h1>
      <p className="text-slate-500 font-medium mb-8">View and manage your orders.</p>
      
      <div className="bg-white rounded-[3rem] p-12 border border-slate-200 shadow-sm">
        <div className="text-center py-20 border-2 border-dashed border-slate-100 rounded-[2.5rem]">
          <div className="text-4xl mb-4">📦</div>
          <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">Order history coming soon!</p>
          <p className="text-slate-400 mt-2">This section will display user order details once integrated.</p>
        </div>
      </div>
    </div>
  );
}
