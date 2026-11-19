import type { Metadata } from "next";
import "./globals.css";
import { PeriodProvider } from "@/components/PeriodContext";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "CampusFlow — Penjadwalan Kuliah & Optimasi Efisiensi Ruangan",
  description:
    "Aplikasi web penjadwalan mata kuliah kampus otomatis dengan mesin optimasi efisiensi ruangan berbasis OR-Tools CP-SAT.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body>
        <PeriodProvider>
          <AppShell>{children}</AppShell>
        </PeriodProvider>
      </body>
    </html>
  );
}
