import type { Metadata } from "next";
import { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "orvym | Smart Bot",
  description: "orvym - Smart bot platform for automated sales and support.",
  icons: [
    { url: '/logo.png', sizes: '32x32', type: 'image/png' },
    { url: '/logo.png', sizes: '192x192', type: 'image/png' },
    { url: '/logo.png', sizes: '512x512', type: 'image/png' },
  ],
  appleWebApp: {
    capable: true,
    title: 'orvym | Smart Bot',
  },
}

export default function RootLayout({
  children,
}: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
