import type { Metadata } from "next";
import { Providers } from "./providers";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATLAS — Ad Intelligence System",
  description: "Autonomous ad intelligence, automation, and attribution",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0a] text-white antialiased">
        <Providers>
          <Sidebar />
          <Header />
          <main className="ml-56 mt-14 p-6 min-h-[calc(100vh-3.5rem)]">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
