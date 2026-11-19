"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Building2,
  CalendarDays,
  CheckCircle2,
  Gauge,
  Layers,
  Loader2,
  Sparkles,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { roomStatusBadge } from "@/lib/colors";
import type { EfficiencySummary } from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";

export default function DashboardPage() {
  const { activePeriod, loading: periodLoading } = usePeriod();
  const [eff, setEff] = useState<EfficiencySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [quickGenerating, setQuickGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    if (!activePeriod) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEfficiency(activePeriod.id);
      setEff(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat analitik");
    } finally {
      setLoading(false);
    }
  }, [activePeriod]);

  useEffect(() => {
    if (activePeriod) {
      void loadAnalytics();
    } else if (!periodLoading) {
      setLoading(false);
    }
  }, [activePeriod, periodLoading, loadAnalytics]);

  const handleQuickGenerate = async () => {
    if (!activePeriod) return;
    setQuickGenerating(true);
    setError(null);
    try {
      await api.generateSchedule({
        period_id: activePeriod.id,
        preset: "balanced",
        time_limit_seconds: 15,
        respect_locked: true,
      });
      await loadAnalytics();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal generate jadwal");
    } finally {
      setQuickGenerating(false);
    }
  };

  if (periodLoading || loading) {
    return (
      <div className="flex items-center justify-center h-64 text-[#5f6368] gap-2">
        <Loader2 className="h-5 w-5 animate-spin text-[#1a73e8]" />
        <span>Memuat dashboard efisiensi ruangan...</span>
      </div>
    );
  }

  if (!activePeriod || !eff) {
    return (
      <div className="bg-white rounded-xl border border-[#dadce0] p-8 text-center">
        <p className="text-[#5f6368]">Belum ada data periode akademik aktif.</p>
      </div>
    );
  }

  const maxHeat = Math.max(1, eff.total_rooms || 1);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-normal text-[#202124] tracking-tight">
            Dashboard Efisiensi Ruangan
          </h1>
          <p className="text-sm text-[#5f6368] mt-1">
            Ringkasan pemanfaatan kapasitas, kepadatan jadwal, dan distribusi ruangan periode{" "}
            <span className="font-medium text-[#202124]">{activePeriod.name}</span>.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link
            href="/jadwal"
            className="inline-flex items-center gap-2 h-9 px-4 rounded-full border border-[#dadce0] bg-white text-[#1a73e8] text-sm font-medium hover:bg-[#f6fafe] transition-colors"
          >
            <CalendarDays className="h-4 w-4" />
            Lihat Grid Jadwal
          </Link>
          <Link
            href="/generate"
            className="inline-flex items-center gap-2 h-9 px-5 rounded-full bg-[#1a73e8] text-white text-sm font-medium hover:bg-[#1765cc] transition-shadow hover:shadow-sm"
          >
            <Sparkles className="h-4 w-4" />
            Konfigurasi & Generate
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty Schedule Banner — Google Blue Soft Banner */}
      {eff.total_sessions === 0 && (
        <div className="rounded-xl bg-[#e8f0fe] border border-[#d2e3fc] p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[#1967d2] bg-white/80 px-2.5 py-0.5 rounded-full mb-2">
              <Sparkles className="h-3.5 w-3.5" />
              Jadwal Belum Dibuat
            </div>
            <h2 className="text-lg font-medium text-[#202124]">
              Siap Menghasilkan Jadwal Kampus Bebas Bentrok & Efisien?
            </h2>
            <p className="text-sm text-[#5f6368] mt-1 max-w-2xl">
              Data master kampus sudah tersedia ({eff.total_rooms} ruangan aktif). Jalankan solver
              untuk menyusun jadwal Senin–Jumat (08:00–16:20) dengan penempatan best-fit kapasitas.
            </p>
          </div>
          <button
            onClick={() => void handleQuickGenerate()}
            disabled={quickGenerating}
            className="inline-flex items-center gap-2 h-10 px-5 rounded-full bg-[#1a73e8] hover:bg-[#1765cc] text-white font-medium text-sm shrink-0 disabled:opacity-60 cursor-pointer transition-shadow hover:shadow-sm"
          >
            {quickGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Mengoptimalkan...
              </>
            ) : (
              <>
                Generate Cepat Sekarang
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-[#dadce0] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#5f6368]">Skor Efisiensi Ruang</span>
            <span className="h-8 w-8 rounded-full bg-[#e8f0fe] text-[#1a73e8] flex items-center justify-center">
              <Gauge className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-[28px] font-normal text-[#202124] leading-none">
              {eff.efficiency_score}%
            </span>
            {eff.run_status && (
              <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-[#e6f4ea] text-[#137333]">
                {eff.run_status}
              </span>
            )}
          </div>
          <p className="text-xs text-[#5f6368] mt-2.5">
            Kombinasi Best-Fit kursi, anti-gap, & konsolidasi ruang.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-[#dadce0] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#5f6368]">Seat Fill (Best-Fit)</span>
            <span className="h-8 w-8 rounded-full bg-[#e6f4ea] text-[#188038] flex items-center justify-center">
              <Users className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-[28px] font-normal text-[#202124] leading-none">
              {eff.seat_fill_efficiency_pct}%
            </span>
            <span className="text-xs text-[#5f6368]">
              {eff.total_seat_waste_slots} kursi-slot sisa
            </span>
          </div>
          <p className="text-xs text-[#5f6368] mt-2.5">
            Rasio mahasiswa terhadap kapasitas ruangan terpakai.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-[#dadce0] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#5f6368]">Utilisasi Waktu Ruang</span>
            <span className="h-8 w-8 rounded-full bg-[#f3e8fd] text-[#8e24aa] flex items-center justify-center">
              <Building2 className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-[28px] font-normal text-[#202124] leading-none">
              {eff.room_time_utilization_pct}%
            </span>
            <span className="text-xs text-[#5f6368]">
              {eff.active_rooms}/{eff.total_rooms} ruang aktif
            </span>
          </div>
          <p className="text-xs text-[#5f6368] mt-2.5">
            Total {eff.total_sessions} sesi pertemuan terjadwal.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-[#dadce0] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#5f6368]">Fragmentasi / Idle Gap</span>
            <span className="h-8 w-8 rounded-full bg-[#fef7e0] text-[#b06000] flex items-center justify-center">
              <Layers className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-[28px] font-normal text-[#202124] leading-none">
              {eff.idle_gap_count}
            </span>
            <span className="text-xs text-[#5f6368]">slot menganggur</span>
          </div>
          <p className="text-xs text-[#5f6368] mt-2.5">
            Celah kosong di antara kelas dalam blok yang sama.
          </p>
        </div>
      </div>

      {/* Building Utilization & Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-[#dadce0] p-5">
          <h3 className="text-base font-medium text-[#202124] flex items-center gap-2">
            <Building2 className="h-4 w-4 text-[#1a73e8]" />
            Efisiensi per Gedung
          </h3>
          <div className="mt-4 space-y-3">
            {eff.building_utilization.map((b) => (
              <div key={b.building_id} className="p-3.5 rounded-lg bg-[#f8f9fa] border border-[#e8eaed]">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="text-sm font-medium text-[#202124]">
                      {b.building_code} — {b.building_name}
                    </div>
                    <div className="text-xs text-[#5f6368] mt-0.5">
                      {b.room_count} ruang · {b.used_slots}/{b.available_slots} slot
                    </div>
                  </div>
                  <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-[#e8f0fe] text-[#1967d2]">
                    {b.seat_fill_efficiency_pct}% fill
                  </span>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="flex justify-between text-[11px] text-[#5f6368]">
                    <span>Utilisasi Waktu</span>
                    <span>{b.time_utilization_pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-[#e8eaed] overflow-hidden">
                    <div
                      className="h-full bg-[#1a73e8] rounded-full"
                      style={{ width: `${Math.min(100, b.time_utilization_pct)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Heatmap Hari x Slot */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#dadce0] p-5 overflow-x-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-medium text-[#202124] flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#1a73e8]" />
              Heatmap Okupansi Ruangan (Hari × Jam Slot)
            </h3>
            <span className="text-xs text-[#5f6368]">
              Jumlah ruangan aktif bersamaan
            </span>
          </div>

          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#dadce0]">
                <th className="text-left py-2 px-2 text-[#5f6368] font-medium">Jam / Slot</th>
                {activePeriod.days.map((d) => (
                  <th key={d} className="py-2 px-2 text-center text-[#5f6368] font-medium">
                    {d}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activePeriod.time_slots.map((slot) => (
                <React.Fragment key={slot.index}>
                  <tr className="border-t border-[#e8eaed]">
                    <td className="py-1.5 px-2 whitespace-nowrap text-[#5f6368]">
                      <span className="inline-block w-5 text-[#9aa0a6]">#{slot.index}</span>
                      {slot.label}
                    </td>
                    {activePeriod.days.map((d) => {
                      const isBlocked = activePeriod.blocked_slots.some(
                        (b) => b.day === d && b.slot === slot.index
                      );
                      const count = eff.heatmap[d]?.[slot.index] ?? 0;
                      const ratio = count / maxHeat;
                      let bg = "bg-[#f8f9fa] text-[#9aa0a6]";
                      if (isBlocked) {
                        bg = "bg-[#f1f3f4] text-[#80868b] italic";
                      } else if (count > 0) {
                        if (ratio >= 0.75) bg = "bg-[#1a73e8] text-white font-medium";
                        else if (ratio >= 0.45) bg = "bg-[#4285f4] text-white font-medium";
                        else if (ratio >= 0.2) bg = "bg-[#d2e3fc] text-[#174ea6] font-medium";
                        else bg = "bg-[#e8f0fe] text-[#1967d2]";
                      }
                      return (
                        <td key={`${d}-${slot.index}`} className="p-1 text-center">
                          <div className={`rounded-md py-1.5 px-1.5 ${bg}`}>
                            {isBlocked ? "Blokir" : count}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                  {slot.break_after_minutes >= 20 && (
                    <tr>
                      <td
                        colSpan={activePeriod.days.length + 1}
                        className="py-1 px-2 text-center text-[11px] font-medium bg-[#fef7e0] text-[#b06000] border-y border-[#feefc3]"
                      >
                        Istirahat ({slot.break_after_minutes} menit) —{" "}
                        {slot.break_after_label || "Jeda Blok"}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-Room Efficiency Breakdown Table */}
      <div className="bg-white rounded-xl border border-[#dadce0] overflow-hidden">
        <div className="px-5 py-4 border-b border-[#dadce0] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-base font-medium text-[#202124]">
              Rincian Efisiensi per Ruangan
            </h3>
            <p className="text-xs text-[#5f6368] mt-0.5">
              Kecocokan kapasitas kelas terhadap setiap ruangan dan deteksi ruang idle.
            </p>
          </div>
          {eff.solve_time_ms > 0 && (
            <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[#137333] bg-[#e6f4ea] px-3 py-1 rounded-full">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Dioptimalkan dalam {eff.solve_time_ms} ms ({eff.preset})
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-[#f8f9fa] text-[#5f6368] text-xs font-medium border-b border-[#dadce0]">
              <tr>
                <th className="py-3 px-4">Ruangan</th>
                <th className="py-3 px-4">Gedung & Tipe</th>
                <th className="py-3 px-4 text-right">Kapasitas</th>
                <th className="py-3 px-4 text-right">Sesi</th>
                <th className="py-3 px-4 w-44">Utilisasi Waktu</th>
                <th className="py-3 px-4 w-44">Seat Fill (Best-Fit)</th>
                <th className="py-3 px-4 text-right">Idle Gap</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8eaed]">
              {eff.rooms.map((rm) => (
                <tr key={rm.room_id} className="hover:bg-[#f8f9fa]">
                  <td className="py-3 px-4">
                    <div className="font-medium text-[#202124]">{rm.room_code}</div>
                    <div className="text-xs text-[#5f6368]">{rm.room_name}</div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-[#202124]">{rm.building_code}</div>
                    <div className="text-xs text-[#5f6368]">{rm.room_type}</div>
                  </td>
                  <td className="py-3 px-4 text-right text-[#202124]">
                    {rm.capacity} kursi
                  </td>
                  <td className="py-3 px-4 text-right text-[#5f6368]">
                    {rm.session_count} ({rm.used_slots} slot)
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-[#202124]">
                        {rm.time_utilization_pct}%
                      </span>
                      <span className="text-[#5f6368]">
                        {rm.used_slots}/{rm.available_slots}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[#e8eaed] overflow-hidden">
                      <div
                        className="h-full bg-[#1a73e8] rounded-full"
                        style={{ width: `${Math.min(100, rm.time_utilization_pct)}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-[#202124]">
                        {rm.avg_seat_fill_pct}%
                      </span>
                      <span className="text-[#5f6368]">
                        sisa {rm.total_seat_waste}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[#e8eaed] overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          rm.avg_seat_fill_pct >= 75
                            ? "bg-[#188038]"
                            : rm.avg_seat_fill_pct >= 55
                            ? "bg-[#f9ab00]"
                            : "bg-[#d93025]"
                        }`}
                        style={{ width: `${Math.min(100, rm.avg_seat_fill_pct)}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right text-[#202124]">
                    {rm.idle_gap_slots}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex text-xs font-medium px-2.5 py-0.5 rounded-full border ${roomStatusBadge(
                        rm.status
                      )}`}
                    >
                      {rm.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
