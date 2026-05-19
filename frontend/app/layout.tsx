import type { Metadata } from "next";
import { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "ORVYM NEXUS | Live Conversation AI",
  description: "ORVYM NEXUS - Live Conversation AI platform for automated sales and support.",
  icons: {
    icon: [
      { url: '/logo.png', sizes: '32x32', type: 'image/png' },
      { url: '/logo.png', sizes: '192x192', type: 'image/png' },
      { url: '/logo.png', sizes: '512x512', type: 'image/png' },
    ],
    shortcut: '/logo.png',
    apple: '/logo.png',
  },
  appleWebApp: {
    capable: true,
    title: 'ORVYM NEXUS',
  },
}

export default function RootLayout({
  children,
}: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          // Prevent theme flicker: apply saved theme before paint
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("theme")||"dark";document.documentElement.classList.toggle("dark",t==="dark");}catch(e){}})();`,
          }}
        />
      </head>
      <body
        className="min-h-screen antialiased bg-white text-slate-900 transition-colors duration-300 dark:bg-[#050505] dark:text-slate-100"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
