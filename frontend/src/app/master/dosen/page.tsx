"use client";

import React, { useCallback, useEffect, useState } from "react";
import { CalendarClock, Plus, Save, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Lecturer, SlotCoord, StudyProgram } from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";

export default function DosenMasterPage() {
  const { activePeriod } = usePeriod();
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [programs, setPrograms] = useState<StudyProgram[]>([]);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const [nidn, setNidn] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [homeProgId, setHomeProgId] = useState<number | "">("");
  const [maxSksDay, setMaxSksDay] = useState(6);
  const [maxDaysWeek, setMaxDaysWeek] = useState(5);

  const [editingLec, setEditingLec] = useState<Lecturer | null>(null);
  const [unavail, setUnavail] = useState<SlotCoord[]>([]);
  const [pref, setPref] = useState<SlotCoord[]>([]);
  const [savingAvail, setSavingAvail] = useState(false);

  const loadData = useCallback(async () => {
    const [lList, pList] = await Promise.all([api.listLecturers(), api.listPrograms()]);
    setLecturers(lList);
    setPrograms(pList);
    if (pList.length > 0 && homeProgId === "") setHomeProgId(pList[0].id);
  }, [homeProgId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrMsg(null);
    try {
      await api.createLecturer({
        nidn: nidn.trim(),
        name: name.trim(),
        email: email.trim() || null,
        home_program_id: homeProgId ? Number(homeProgId) : null,
        max_sks_per_day: maxSksDay,
        max_days_per_week: maxDaysWeek,
        unavailable_slots: [],
        preferred_slots: [],
      });
      setNidn("");
      setName("");
      setEmail("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal menambah dosen");
    }
  };

  const openAvailability = (lec: Lecturer) => {
    setEditingLec(lec);
    setUnavail(lec.unavailable_slots || []);
    setPref(lec.preferred_slots || []);
  };

  const cycleSlotState = (day: string, slot: number) => {
    const isUnavail = unavail.some((s) => s.day === day && s.slot === slot);
    const isPref = pref.some((s) => s.day === day && s.slot === slot);

    if (!isUnavail && !isPref) {
      setUnavail((prev) => [...prev, { day, slot }]);
    } else if (isUnavail) {
      setUnavail((prev) => prev.filter((s) => !(s.day === day && s.slot === slot)));
      setPref((prev) => [...prev, { day, slot }]);
    } else {
      setPref((prev) => prev.filter((s) => !(s.day === day && s.slot === slot)));
    }
  };

  const saveAvailability = async () => {
    if (!editingLec) return;
    setSavingAvail(true);
    try {
      await api.updateLecturer(editingLec.id, {
        unavailable_slots: unavail,
        preferred_slots: pref,
      });
      setEditingLec(null);
      await loadData();
    } finally {
      setSavingAvail(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Master Dosen & Ketersediaan</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola batas beban SKS harian, hari mengajar per minggu, jam berhalangan, dan preferensi waktu dosen.
        </p>
      </div>

      {errMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {errMsg}
        </div>
      )}

      <form
        onSubmit={(e) => void handleCreate(e)}
        className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
      >
        <h2 className="font-semibold text-slate-900">Tambah Dosen</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-slate-600">NIDN</span>
            <input
              type="text"
              required
              placeholder="0410018801"
              value={nidn}
              onChange={(e) => setNidn(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block sm:col-span-2">
            <span className="text-xs font-medium text-slate-600">Nama Lengkap & Gelar</span>
            <input
              type="text"
              required
              placeholder="Dr. Budi Hartono, M.Kom."
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Home Prodi</span>
            <select
              value={homeProgId}
              onChange={(e) =>
                setHomeProgId(e.target.value ? Number(e.target.value) : "")
              }
              className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              <option value="">Umum / Lintas</option>
              {programs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code} — {p.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Maks SKS/Hari</span>
            <input
              type="number"
              min={1}
              max={16}
              value={maxSksDay}
              onChange={(e) => setMaxSksDay(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Maks Hari/Mgg</span>
            <input
              type="number"
              min={1}
              max={5}
              value={maxDaysWeek}
              onChange={(e) => setMaxDaysWeek(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="email"
            placeholder="Email dosen (opsional)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="sm:w-72 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            Simpan Dosen
          </button>
        </div>
      </form>

      {/* Lecturers Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">NIDN</th>
                <th className="py-3 px-4">Nama Dosen</th>
                <th className="py-3 px-4">Home Prodi</th>
                <th className="py-3 px-4 text-center">Batas Beban</th>
                <th className="py-3 px-4">Ketersediaan</th>
                <th className="py-3 px-4 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {lecturers.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono text-xs text-slate-600">{l.nidn}</td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900">{l.name}</div>
                    {l.email && <div className="text-xs text-slate-400">{l.email}</div>}
                  </td>
                  <td className="py-3 px-4 text-slate-600">{l.program_name || "Umum"}</td>
                  <td className="py-3 px-4 text-center text-xs">
                    <span className="px-2 py-0.5 rounded bg-slate-100 font-medium">
                      {l.max_sks_per_day} slot/hari · {l.max_days_per_week} hari/mgg
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => openAvailability(l)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-100 cursor-pointer"
                    >
                      <CalendarClock className="h-3.5 w-3.5 text-blue-600" />
                      Atur Slot ({l.unavailable_slots.length} blokir,{" "}
                      {l.preferred_slots.length} pref)
                    </button>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={async () => {
                        await api.deleteLecturer(l.id);
                        await loadData();
                      }}
                      className="p-1.5 text-slate-400 hover:text-rose-600 cursor-pointer"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Availability Matrix Modal */}
      {editingLec && activePeriod && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Ketersediaan & Preferensi: {editingLec.name}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Klik sel untuk mengubah status: Putih (Tersedia) → Merah (Berhalangan) → Hijau (Preferensi).
                </p>
              </div>
              <button
                onClick={() => setEditingLec(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="overflow-auto flex-1 border border-slate-200 rounded-xl">
              <table className="w-full text-xs border-collapse">
                <thead className="bg-slate-50 sticky top-0">
                  <tr>
                    <th className="py-2 px-3 text-left text-slate-600">Slot</th>
                    {activePeriod.days.map((d) => (
                      <th key={d} className="py-2 px-2 text-center font-semibold text-slate-700">
                        {d}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {activePeriod.time_slots.map((s) => (
                    <tr key={s.index} className="border-t border-slate-100">
                      <td className="py-1.5 px-3 font-medium text-slate-600 whitespace-nowrap">
                        #{s.index} {s.label}
                      </td>
                      {activePeriod.days.map((d) => {
                        const isU = unavail.some((x) => x.day === d && x.slot === s.index);
                        const isP = pref.some((x) => x.day === d && x.slot === s.index);
                        return (
                          <td key={`${d}-${s.index}`} className="p-1 text-center">
                            <button
                              type="button"
                              onClick={() => cycleSlotState(d, s.index)}
                              className={`w-full py-1.5 rounded font-semibold transition-colors cursor-pointer ${
                                isU
                                  ? "bg-rose-500 text-white"
                                  : isP
                                  ? "bg-emerald-500 text-white"
                                  : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                              }`}
                            >
                              {isU ? "Blokir" : isP ? "Pref" : "OK"}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => setEditingLec(null)}
                className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700"
              >
                Batal
              </button>
              <button
                type="button"
                disabled={savingAvail}
                onClick={() => void saveAvailability()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
              >
                <Save className="h-4 w-4" />
                {savingAvail ? "Menyimpan..." : "Simpan Ketersediaan"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
