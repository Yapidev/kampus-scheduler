"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Plus, RotateCcw, Save, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Faculty, StudyProgram } from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";

export default function AkademikMasterPage() {
  const { activePeriod, refreshPeriods } = usePeriod();
  const [faculties, setFaculties] = useState<Faculty[]>([]);
  const [programs, setPrograms] = useState<StudyProgram[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  // Period Settings Form
  const [startTime, setStartTime] = useState("08:00");
  const [slotMinutes, setSlotMinutes] = useState(50);
  const [slotsPerDay, setSlotsPerDay] = useState(9);
  const [newPeriodName, setNewPeriodName] = useState("");
  const [newPeriodYear, setNewPeriodYear] = useState("2026/2027");
  const [newPeriodSem, setNewPeriodSem] = useState<"Ganjil" | "Genap" | "Pendek">("Genap");

  // Faculty & Program Forms
  const [facCode, setFacCode] = useState("");
  const [facName, setFacName] = useState("");
  const [progFacId, setProgFacId] = useState<number | "">("");
  const [progCode, setProgCode] = useState("");
  const [progName, setProgName] = useState("");
  const [progLevel, setProgLevel] = useState<"D3" | "D4" | "S1" | "S2" | "S3">("S1");

  const loadAll = useCallback(async () => {
    const [f, p] = await Promise.all([api.listFaculties(), api.listPrograms()]);
    setFaculties(f);
    setPrograms(p);
    if (f.length > 0 && progFacId === "") setProgFacId(f[0].id);
  }, [progFacId]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  useEffect(() => {
    if (activePeriod) {
      setStartTime(activePeriod.start_time);
      setSlotMinutes(activePeriod.slot_minutes);
      setSlotsPerDay(activePeriod.slots_per_day);
    }
  }, [activePeriod]);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePeriod) return;
    setMsg(null);
    setErrMsg(null);
    try {
      await api.updatePeriod(activePeriod.id, {
        start_time: startTime,
        slot_minutes: slotMinutes,
        slots_per_day: slotsPerDay,
      });
      await refreshPeriods();
      setMsg("Pengaturan jam & slot periode akademik berhasil disimpan.");
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal menyimpan pengaturan jam.");
    }
  };

  const handleCreatePeriod = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPeriodName.trim()) return;
    setMsg(null);
    setErrMsg(null);
    try {
      await api.createPeriod({
        name: newPeriodName.trim(),
        year: newPeriodYear,
        semester_type: newPeriodSem,
        is_active: true,
      });
      setNewPeriodName("");
      await refreshPeriods();
      setMsg("Periode akademik baru dibuat dan diaktifkan.");
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal membuat periode baru.");
    }
  };

  const handleResetSeed = async () => {
    if (!confirm("Isi ulang seluruh data contoh kampus? Data saat ini akan diganti.")) return;
    await api.resetSeed();
    await refreshPeriods();
    await loadAll();
    setMsg("Data contoh kampus berhasil di-reset.");
  };

  const handleAddFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facCode.trim() || !facName.trim()) return;
    await api.createFaculty({ code: facCode.trim(), name: facName.trim() });
    setFacCode("");
    setFacName("");
    await loadAll();
  };

  const handleAddProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!progFacId || !progCode.trim() || !progName.trim()) return;
    await api.createProgram({
      faculty_id: Number(progFacId),
      code: progCode.trim(),
      name: progName.trim(),
      degree_level: progLevel,
    });
    setProgCode("");
    setProgName("");
    await loadAll();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Master Akademik, Periode & Program Studi
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Atur struktur fakultas, prodi, tahun akademik, dan konfigurasi jam kuliah per slot.
          </p>
        </div>

        <button
          onClick={() => void handleResetSeed()}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset Data Contoh Kampus
        </button>
      </div>

      {msg && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm">
          {msg}
        </div>
      )}

      {errMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {errMsg}
        </div>
      )}

      <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex flex-wrap items-center justify-between gap-2">
        <div>
          <strong>Aturan Operasional Kampus:</strong> Perkuliahan hanya dilaksanakan pada hari{" "}
          <strong>Senin – Jumat</strong>, dimulai paling pagi pukul <strong>08:00</strong> dan
          berakhir paling lambat pukul <strong>16:20</strong>.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form
          onSubmit={(e) => void handleSaveSettings(e)}
          className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
        >
          <h2 className="font-semibold text-slate-900">
            Pengaturan Jam Kuliah ({activePeriod?.name})
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Jam Mulai</span>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Menit / SKS Slot</span>
              <input
                type="number"
                min={30}
                max={120}
                value={slotMinutes}
                onChange={(e) => setSlotMinutes(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Total Slot / Hari</span>
              <input
                type="number"
                min={1}
                max={20}
                value={slotsPerDay}
                onChange={(e) => setSlotsPerDay(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
          </div>

          {activePeriod && (
            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
              <div>
                <strong>Hari Aktif:</strong> {activePeriod.days.join(", ")}
              </div>
              <div>
                <strong>Slot Diblokir:</strong>{" "}
                {activePeriod.blocked_slots.length > 0
                  ? activePeriod.blocked_slots
                      .map((b) => `${b.day} Slot ${b.slot} (${b.reason})`)
                      .join("; ")
                  : "Tidak ada"}
              </div>
              <div className="pt-1 flex flex-wrap gap-1.5">
                {activePeriod.time_slots.map((ts) => (
                  <span
                    key={ts.index}
                    className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700"
                  >
                    #{ts.index} {ts.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
          >
            <Save className="h-4 w-4" />
            Simpan Pengaturan Jam
          </button>
        </form>

        <form
          onSubmit={(e) => void handleCreatePeriod(e)}
          className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
        >
          <h2 className="font-semibold text-slate-900">Tambah Tahun Akademik / Semester Baru</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label className="block sm:col-span-3">
              <span className="text-xs font-medium text-slate-600">Nama Periode</span>
              <input
                type="text"
                required
                placeholder="Contoh: 2026/2027 Genap"
                value={newPeriodName}
                onChange={(e) => setNewPeriodName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block sm:col-span-2">
              <span className="text-xs font-medium text-slate-600">Tahun Akademik</span>
              <input
                type="text"
                required
                value={newPeriodYear}
                onChange={(e) => setNewPeriodYear(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-slate-600">Semester</span>
              <select
                value={newPeriodSem}
                onChange={(e) =>
                  setNewPeriodSem(e.target.value as "Ganjil" | "Genap" | "Pendek")
                }
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="Ganjil">Ganjil</option>
                <option value="Genap">Genap</option>
                <option value="Pendek">Pendek</option>
              </select>
            </label>
          </div>
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            Buat & Aktifkan Periode
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <h2 className="font-semibold text-slate-900">Daftar Fakultas</h2>
          <form onSubmit={(e) => void handleAddFaculty(e)} className="flex gap-2">
            <input
              type="text"
              placeholder="Kode (FTI)"
              value={facCode}
              onChange={(e) => setFacCode(e.target.value)}
              className="w-28 rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            />
            <input
              type="text"
              placeholder="Nama Fakultas"
              value={facName}
              onChange={(e) => setFacName(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            />
            <button
              type="submit"
              className="px-3.5 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
            >
              Tambah
            </button>
          </form>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg">
            {faculties.map((f) => (
              <div key={f.id} className="px-3.5 py-2.5 flex items-center justify-between text-sm">
                <div>
                  <span className="font-bold text-slate-800 mr-2">{f.code}</span>
                  <span className="text-slate-600">{f.name}</span>
                </div>
                <button
                  onClick={async () => {
                    await api.deleteFaculty(f.id);
                    await loadAll();
                  }}
                  className="p-1 text-slate-400 hover:text-rose-600 cursor-pointer"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <h2 className="font-semibold text-slate-900">Daftar Program Studi</h2>
          <form
            onSubmit={(e) => void handleAddProgram(e)}
            className="grid grid-cols-1 sm:grid-cols-4 gap-2"
          >
            <select
              value={progFacId}
              onChange={(e) => setProgFacId(Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
            >
              {faculties.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.code}
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Kode (TI)"
              value={progCode}
              onChange={(e) => setProgCode(e.target.value)}
              className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
            />
            <input
              type="text"
              placeholder="Nama Prodi"
              value={progName}
              onChange={(e) => setProgName(e.target.value)}
              className="sm:col-span-2 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
            />
            <select
              value={progLevel}
              onChange={(e) =>
                setProgLevel(e.target.value as "D3" | "D4" | "S1" | "S2" | "S3")
              }
              className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
            >
              <option value="D3">D3</option>
              <option value="D4">D4</option>
              <option value="S1">S1</option>
              <option value="S2">S2</option>
              <option value="S3">S3</option>
            </select>
            <button
              type="submit"
              className="sm:col-span-3 px-3.5 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
            >
              Tambah Program Studi
            </button>
          </form>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg">
            {programs.map((p) => (
              <div key={p.id} className="px-3.5 py-2.5 flex items-center justify-between text-sm">
                <div>
                  <span className="font-bold text-slate-800 mr-2">
                    [{p.degree_level}] {p.code}
                  </span>
                  <span className="text-slate-700">{p.name}</span>
                  <span className="text-xs text-slate-400 ml-2">({p.faculty_name})</span>
                </div>
                <button
                  onClick={async () => {
                    await api.deleteProgram(p.id);
                    await loadAll();
                  }}
                  className="p-1 text-slate-400 hover:text-rose-600 cursor-pointer"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
