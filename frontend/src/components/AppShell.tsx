"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  Building2,
  CalendarDays,
  GraduationCap,
  Menu,
  Sparkles,
  Users,
  X,
  CheckCircle2,
  FileEdit,
  Settings2,
} from "lucide-react";
import { usePeriod } from "./PeriodContext";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard Efisiensi", icon: BarChart3 },
  { href: "/generate", label: "Generate Otomatis", icon: Sparkles },
  { href: "/jadwal", label: "Jadwal & Drag-Drop", icon: CalendarDays },
  { href: "/master/akademik", label: "Akademik & Prodi", icon: Settings2 },
  { href: "/master/ruangan", label: "Gedung & Ruangan", icon: Building2 },
  { href: "/master/dosen", label: "Dosen & Ketersediaan", icon: Users },
  { href: "/master/kelas-matkul", label: "Kelas, MK & Plotting", icon: BookOpen },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { periods, activePeriod, selectPeriod, refreshPeriods, error } = usePeriod();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [toggling, setToggling] = useState(false);

  const handleTogglePublish = async () => {
    if (!activePeriod || toggling) return;
    setToggling(true);
    try {
      await api.togglePublishPeriod(activePeriod.id);
      await refreshPeriods();
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900">
      {/* Sidebar Desktop */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 bg-slate-900 text-slate-100 border-r border-slate-800">
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm">
            <GraduationCap className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-bold tracking-tight text-sm text-white">CampusFlow</div>
            <div className="text-[11px] text-slate-400">Optimasi Jadwal & Ruang</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800 text-xs text-slate-400">
          <div className="font-medium text-slate-300">Mesin Optimasi</div>
          <div className="mt-0.5">OR-Tools CP-SAT Solver</div>
          <div className="text-[11px] text-slate-500 mt-1">
            Best-Fit Kapasitas & Anti-Gap Ruangan
          </div>
        </div>
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/60"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative w-64 bg-slate-900 text-slate-100 flex flex-col z-10">
            <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
              <div className="flex items-center gap-2 font-bold text-white">
                <GraduationCap className="h-5 w-5 text-blue-400" />
                CampusFlow
              </div>
              <button
                onClick={() => setMobileOpen(false)}
                className="p-1 text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="p-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active =
                  item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                      active
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:bg-slate-800"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100"
              aria-label="Buka Menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="text-sm font-medium text-slate-500 hidden sm:block">
              Sistem Penjadwalan Mata Kuliah Kampus
            </div>
          </div>

          <div className="flex items-center gap-3">
            {activePeriod && (
              <>
                <select
                  aria-label="Pilih Periode Akademik"
                  value={activePeriod.id}
                  onChange={(e) => void selectPeriod(Number(e.target.value))}
                  className="text-sm font-medium bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {periods.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.semester_type})
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => void handleTogglePublish()}
                  disabled={toggling}
                  title="Klik untuk ubah status Draft / Published"
                  className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border transition-colors cursor-pointer ${
                    activePeriod.status === "published"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                      : "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
                  }`}
                >
                  {activePeriod.status === "published" ? (
                    <>
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Published
                    </>
                  ) : (
                    <>
                      <FileEdit className="h-3.5 w-3.5" />
                      Draft
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </header>

        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
            Koneksi Backend Bermasalah: {error}. Pastikan API FastAPI berjalan di port 8000.
          </div>
        )}

        <main className="flex-1 p-4 sm:p-6 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
