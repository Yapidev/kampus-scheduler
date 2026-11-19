"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  History,
  Lock,
  RefreshCw,
  Sliders,
  Sparkles,
} from "lucide-react";
import { ApiError, api } from "@/lib/api";
import type {
  GenerateResponse,
  OptimizationWeights,
  PreflightReport,
  ScheduleRunSummary,
} from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";

type PresetType = "balanced" | "best_fit" | "compact_rooms" | "custom";

const PRESETS: Array<{
  id: PresetType;
  title: string;
  desc: string;
  weights: OptimizationWeights;
}> = [
  {
    id: "balanced",
    title: "Seimbang (Direkomendasikan)",
    desc: "Keseimbangan optimal antara Best-Fit kapasitas kursi, minimasi gap waktu ruangan, dan perpindahan gedung.",
    weights: { w_seat: 10, w_gap: 80, w_pack: 40, w_building: 25, w_pref: 15 },
  },
  {
    id: "best_fit",
    title: "Prioritas Best-Fit Kapasitas",
    desc: "Memaksa kelas kecil masuk ke ruang kecil agar ruang berkapasitas besar selalu hemat dan efisien.",
    weights: { w_seat: 28, w_gap: 45, w_pack: 20, w_building: 15, w_pref: 10 },
  },
  {
    id: "compact_rooms",
    title: "Pemadatan Ruangan & Anti-Gap",
    desc: "Memadatkan kelas secara berurutan pada ruangan aktif dan menghilangkan jam kosong menganggur.",
    weights: { w_seat: 8, w_gap: 150, w_pack: 110, w_building: 25, w_pref: 10 },
  },
  {
    id: "custom",
    title: "Kustom Bobot Optimasi",
    desc: "Atur sendiri prioritas matematis fungsi objektif OR-Tools CP-SAT sesuai kebijakan kampus.",
    weights: { w_seat: 15, w_gap: 90, w_pack: 50, w_building: 25, w_pref: 15 },
  },
];

export default function GeneratePage() {
  const { activePeriod } = usePeriod();
  const [preset, setPreset] = useState<PresetType>("balanced");
  const [weights, setWeights] = useState<OptimizationWeights>(PRESETS[0].weights);
  const [timeLimit, setTimeLimit] = useState<number>(15);
  const [respectLocked, setRespectLocked] = useState<boolean>(true);

  const [preflight, setPreflight] = useState<PreflightReport | null>(null);
  const [runs, setRuns] = useState<ScheduleRunSummary[]>([]);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadContext = useCallback(async () => {
    if (!activePeriod) return;
    setLoadingAudit(true);
    try {
      const [pf, rList] = await Promise.all([
        api.preflight(activePeriod.id, respectLocked),
        api.listRuns(activePeriod.id),
      ]);
      setPreflight(pf);
      setRuns(rList);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Gagal memeriksa kelayakan data");
    } finally {
      setLoadingAudit(false);
    }
  }, [activePeriod, respectLocked]);

  useEffect(() => {
    void loadContext();
  }, [loadContext]);

  const handleSelectPreset = (pId: PresetType) => {
    setPreset(pId);
    const found = PRESETS.find((x) => x.id === pId);
    if (found && pId !== "custom") {
      setWeights(found.weights);
    }
  };

  const handleGenerate = async () => {
    if (!activePeriod) return;
    setGenerating(true);
    setErrorMsg(null);
    setResult(null);
    try {
      const res = await api.generateSchedule({
        period_id: activePeriod.id,
        preset,
        weights: preset === "custom" ? weights : undefined,
        time_limit_seconds: timeLimit,
        respect_locked: respectLocked,
      });
      setResult(res);
      await loadContext();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Terjadi kesalahan saat menjalankan solver.");
      }
    } finally {
      setGenerating(false);
    }
  };

  if (!activePeriod) {
    return <div className="p-6 text-[#5f6368]">Memuat periode akademik...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-[24px] font-normal text-[#202124]">
            Generate Jadwal Otomatis
          </h1>
          <p className="text-sm text-[#5f6368] mt-1">
            Susun jadwal Senin–Jumat (08:00–16:20) bebas bentrok sekaligus memaksimalkan efisiensi ruangan.
          </p>
        </div>
        <button
          onClick={() => void loadContext()}
          disabled={loadingAudit}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-full border border-[#dadce0] bg-white text-sm font-medium text-[#1a73e8] hover:bg-[#f6fafe] cursor-pointer"
        >
          <RefreshCw className={`h-4 w-4 ${loadingAudit ? "animate-spin" : ""}`} />
          Refresh Pre-flight Audit
        </button>
      </div>

      {/* Pre-flight Audit Status */}
      {preflight && (
        <div
          className={`rounded-xl border p-5 ${
            preflight.feasible
              ? "bg-[#e6f4ea] border-[#ceead6]"
              : "bg-[#fce8e6] border-[#fad2cf]"
          }`}
        >
          <div className="flex items-start gap-3">
            {preflight.feasible ? (
              <CheckCircle2 className="h-5 w-5 text-[#137333] mt-0.5 shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-[#c5221f] mt-0.5 shrink-0" />
            )}
            <div>
              <h2 className="font-medium text-[#202124]">
                {preflight.feasible
                  ? "Pre-flight Audit Lolos — Data Siap Dijadwalkan"
                  : "Pre-flight Audit Menemukan Masalah Kelayakan"}
              </h2>
              <p className="text-xs text-[#5f6368] mt-0.5">
                {preflight.total_sessions} sesi pertemuan ({preflight.total_required_slots} slot
                kebutuhan) vs {preflight.total_available_room_slots} total kapasitas slot ruangan
                aktif.
              </p>
            </div>
          </div>

          {preflight.issues.length > 0 && (
            <div className="mt-4 space-y-2">
              {preflight.issues.map((issue, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-2 text-xs p-2.5 rounded-lg border ${
                    issue.severity === "error"
                      ? "bg-white border-[#fad2cf] text-[#c5221f]"
                      : "bg-[#fef7e0] border-[#feefc3] text-[#b06000]"
                  }`}
                >
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-medium">[{issue.category}]</span> {issue.message}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Strategy Preset & Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#dadce0] p-5 space-y-4">
          <div className="flex items-center gap-2 font-medium text-[#202124]">
            <Sliders className="h-4 w-4 text-[#1a73e8]" />
            Strategi Optimasi Efisiensi Ruangan
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {PRESETS.map((p) => {
              const selected = preset === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectPreset(p.id)}
                  className={`text-left p-4 rounded-xl border transition-colors cursor-pointer ${
                    selected
                      ? "border-[#1a73e8] bg-[#e8f0fe]/60"
                      : "border-[#dadce0] hover:bg-[#f8f9fa] bg-white"
                  }`}
                >
                  <div
                    className={`font-medium text-sm ${
                      selected ? "text-[#1967d2]" : "text-[#202124]"
                    }`}
                  >
                    {p.title}
                  </div>
                  <p className="text-xs text-[#5f6368] mt-1 leading-relaxed">{p.desc}</p>
                </button>
              );
            })}
          </div>

          {preset === "custom" && (
            <div className="p-4 rounded-xl bg-[#f8f9fa] border border-[#e8eaed] space-y-3">
              <div className="text-xs font-medium text-[#5f6368]">
                Pengaturan Bobot Penalti / Bonus Solver
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {(
                  [
                    ["w_seat", "Bobot Best-Fit Kursi (Seat Waste)"],
                    ["w_gap", "Bobot Anti-Gap Ruangan (Idle Hole)"],
                    ["w_pack", "Bobot Konsolidasi Ruang Aktif"],
                    ["w_building", "Bobot Minimasi Pindah Gedung"],
                    ["w_pref", "Bonus Preferensi Waktu Dosen"],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} className="block">
                    <div className="flex justify-between text-xs font-medium text-[#202124] mb-1">
                      <span>{label}</span>
                      <span className="text-[#1a73e8]">{weights[key]}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={200}
                      value={weights[key]}
                      onChange={(e) =>
                        setWeights((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                      }
                      className="w-full accent-[#1a73e8]"
                    />
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Execution Box */}
        <div className="bg-white rounded-xl border border-[#dadce0] p-5 flex flex-col justify-between space-y-5">
          <div className="space-y-4">
            <div className="flex items-center gap-2 font-medium text-[#202124]">
              <Cpu className="h-4 w-4 text-[#1a73e8]" />
              Parameter Eksekusi
            </div>

            <label className="block">
              <span className="text-xs font-medium text-[#5f6368]">
                Batas Waktu Solver (detik)
              </span>
              <input
                type="number"
                min={2}
                max={120}
                value={timeLimit}
                onChange={(e) => setTimeLimit(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-[#dadce0] px-3 py-2 text-sm focus:outline-none focus:border-[#1a73e8]"
              />
              <span className="text-[11px] text-[#5f6368] mt-1 block">
                Waktu lebih lama membantu solver mencari efisiensi lebih tinggi.
              </span>
            </label>

            <label className="flex items-start gap-2.5 p-3 rounded-lg bg-[#f8f9fa] border border-[#e8eaed] cursor-pointer">
              <input
                type="checkbox"
                checked={respectLocked}
                onChange={(e) => setRespectLocked(e.target.checked)}
                className="mt-0.5 rounded accent-[#1a73e8]"
              />
              <div>
                <div className="text-xs font-medium text-[#202124] flex items-center gap-1">
                  <Lock className="h-3.5 w-3.5 text-[#5f6368]" />
                  Pertahankan Jadwal Terkunci
                </div>
                <div className="text-[11px] text-[#5f6368] mt-0.5">
                  Sesi yang dikunci manual tetap dipertahankan saat generate ulang.
                </div>
              </div>
            </label>
          </div>

          <button
            type="button"
            onClick={() => void handleGenerate()}
            disabled={generating || (preflight !== null && !preflight.feasible)}
            className="w-full inline-flex items-center justify-center gap-2 h-10 px-5 rounded-full bg-[#1a73e8] hover:bg-[#1765cc] text-white font-medium text-sm disabled:opacity-50 cursor-pointer transition-shadow hover:shadow-sm"
          >
            <Sparkles className={`h-4 w-4 ${generating ? "animate-spin" : ""}`} />
            {generating ? "Mengoptimalkan Jadwal..." : "Generate Jadwal Otomatis"}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-sm">
          {errorMsg}
        </div>
      )}

      {/* Result Banner */}
      {result && (
        <div className="bg-white rounded-xl border-2 border-[#188038] p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[#137333] bg-[#e6f4ea] px-2.5 py-0.5 rounded-full">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Generate Berhasil ({result.status})
              </div>
              <h3 className="text-lg font-medium text-[#202124] mt-1.5">
                {result.entries.length} Sesi Mata Kuliah Terjadwal dalam {result.solve_time_ms} ms
              </h3>
            </div>
            <div className="flex items-center gap-2.5">
              <Link
                href="/"
                className="h-9 inline-flex items-center px-4 rounded-full border border-[#dadce0] text-sm font-medium text-[#1a73e8] hover:bg-[#f6fafe]"
              >
                Lihat Dashboard
              </Link>
              <Link
                href="/jadwal"
                className="h-9 inline-flex items-center gap-1.5 px-4 rounded-full bg-[#188038] hover:bg-[#137333] text-white text-sm font-medium"
              >
                Buka Grid Jadwal
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div className="p-3 rounded-lg bg-[#f8f9fa] border border-[#e8eaed]">
              <div className="text-xs text-[#5f6368]">Skor Efisiensi Ruang</div>
              <div className="text-xl font-medium text-[#1a73e8]">
                {result.efficiency.efficiency_score}%
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#f8f9fa] border border-[#e8eaed]">
              <div className="text-xs text-[#5f6368]">Seat Fill (Best-Fit)</div>
              <div className="text-xl font-medium text-[#137333]">
                {result.efficiency.seat_fill_efficiency_pct}%
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#f8f9fa] border border-[#e8eaed]">
              <div className="text-xs text-[#5f6368]">Utilisasi Waktu Ruang</div>
              <div className="text-xl font-medium text-[#202124]">
                {result.efficiency.room_time_utilization_pct}%
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#f8f9fa] border border-[#e8eaed]">
              <div className="text-xs text-[#5f6368]">Idle Gap Ruangan</div>
              <div className="text-xl font-medium text-[#202124]">
                {result.efficiency.idle_gap_count} slot
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Run History */}
      <div className="bg-white rounded-xl border border-[#dadce0] overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[#dadce0] flex items-center gap-2 font-medium text-[#202124] text-sm">
          <History className="h-4 w-4 text-[#5f6368]" />
          Riwayat Eksekusi Optimasi
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-[#f8f9fa] text-xs font-medium text-[#5f6368] border-b border-[#dadce0]">
              <tr>
                <th className="py-2.5 px-4">Run #</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Preset</th>
                <th className="py-2.5 px-4 text-right">Sesi</th>
                <th className="py-2.5 px-4 text-right">Skor Efisiensi</th>
                <th className="py-2.5 px-4 text-right">Seat Fill</th>
                <th className="py-2.5 px-4 text-right">Idle Gap</th>
                <th className="py-2.5 px-4 text-right">Durasi Solver</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8eaed]">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-[#5f6368] text-xs">
                    Belum ada riwayat generate pada periode ini.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.id} className="hover:bg-[#f8f9fa]">
                    <td className="py-2.5 px-4 font-medium text-[#202124]">#{r.id}</td>
                    <td className="py-2.5 px-4">
                      <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-[#e6f4ea] text-[#137333]">
                        {r.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-[#5f6368]">{r.preset}</td>
                    <td className="py-2.5 px-4 text-right">{r.total_sessions}</td>
                    <td className="py-2.5 px-4 text-right font-medium text-[#1a73e8]">
                      {r.efficiency_score}%
                    </td>
                    <td className="py-2.5 px-4 text-right">{r.seat_fill_efficiency}%</td>
                    <td className="py-2.5 px-4 text-right">{r.idle_gap_count}</td>
                    <td className="py-2.5 px-4 text-right text-[#5f6368]">
                      {r.solve_time_ms} ms
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
