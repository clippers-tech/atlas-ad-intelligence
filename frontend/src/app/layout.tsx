import type { Metadata } from "next";
import { Providers } from "./providers";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATLAS — Ad Intelligence System",
  description: "Autonomous ad intelligence, automation, and attribution for Meta Ads",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="h-screen overflow-hidden grid"
            style={{
              gridTemplateColumns: "var(--sidebar-width) 1fr",
              gridTemplateRows: "var(--header-height) 1fr",
            }}>
            <div className="row-span-2">
              <Sidebar />
            </div>
            <Header />
            <main className="overflow-y-auto p-6"
              style={{ overscrollBehavior: "contain" }}>
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
