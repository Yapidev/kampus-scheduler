"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Download,
  FileSpreadsheet,
  FileText,
  Loader2,
  Sparkles,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  Lecturer,
  Room,
  ScheduleEntry,
  StudentClass,
  StudyProgram,
} from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";
import { TimetableGrid, type ViewMode } from "@/components/TimetableGrid";

export default function JadwalPage() {
  const { activePeriod } = usePeriod();
  const [mode, setMode] = useState<ViewMode>("matrix");
  const [programs, setPrograms] = useState<StudyProgram[]>([]);
  const [classes, setClasses] = useState<StudentClass[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [allEntries, setAllEntries] = useState<ScheduleEntry[]>([]);

  const [selectedProgramId, setSelectedProgramId] = useState<number | "">("");
  const [selectedClassId, setSelectedClassId] = useState<number | "">("");
  const [selectedLecturerId, setSelectedLecturerId] = useState<number | "">("");
  const [selectedRoomId, setSelectedRoomId] = useState<number | "">("");
  const [selectedDay, setSelectedDay] = useState<string>("Senin");

  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!activePeriod) return;
    setLoading(true);
    try {
      const [progs, clsList, lecList, roomList, sched] = await Promise.all([
        api.listPrograms(),
        api.listClasses(activePeriod.id),
        api.listLecturers(),
        api.listRooms(),
        api.listSchedule({ period_id: activePeriod.id }),
      ]);
      setPrograms(progs);
      setClasses(clsList);
      setLecturers(lecList);
      setRooms(roomList);
      setAllEntries(sched);

      if (clsList.length > 0 && selectedClassId === "") setSelectedClassId(clsList[0].id);
      if (lecList.length > 0 && selectedLecturerId === "") setSelectedLecturerId(lecList[0].id);
      if (roomList.length > 0 && selectedRoomId === "") setSelectedRoomId(roomList[0].id);
      if (activePeriod.days.length > 0 && !activePeriod.days.includes(selectedDay)) {
        setSelectedDay(activePeriod.days[0]);
      }
    } finally {
      setLoading(false);
    }
  }, [activePeriod, selectedClassId, selectedLecturerId, selectedRoomId, selectedDay]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredEntries = useMemo(() => {
    if (mode === "class") {
      if (selectedClassId !== "") {
        return allEntries.filter(
          (e) =>
            e.class_id === selectedClassId ||
            e.extra_class_ids.includes(Number(selectedClassId))
        );
      }
      if (selectedProgramId !== "") {
        return allEntries.filter((e) => e.program_id === selectedProgramId);
      }
    }
    if (mode === "lecturer" && selectedLecturerId !== "") {
      return allEntries.filter(
        (e) =>
          e.lecturer_id === selectedLecturerId ||
          e.co_lecturer_id === selectedLecturerId
      );
    }
    if (mode === "room" && selectedRoomId !== "") {
      return allEntries.filter((e) => e.room_id === selectedRoomId);
    }
    return allEntries;
  }, [
    allEntries,
    mode,
    selectedClassId,
    selectedProgramId,
    selectedLecturerId,
    selectedRoomId,
  ]);

  const exportFilter = useMemo(() => {
    if (!activePeriod) return {};
    const base: Record<string, number> = { period_id: activePeriod.id };
    if (mode === "class") {
      if (selectedClassId !== "") base.class_id = Number(selectedClassId);
      else if (selectedProgramId !== "") base.program_id = Number(selectedProgramId);
    } else if (mode === "lecturer" && selectedLecturerId !== "") {
      base.lecturer_id = Number(selectedLecturerId);
    } else if (mode === "room" && selectedRoomId !== "") {
      base.room_id = Number(selectedRoomId);
    }
    return base;
  }, [
    activePeriod,
    mode,
    selectedClassId,
    selectedProgramId,
    selectedLecturerId,
    selectedRoomId,
  ]);

  const handleClearUnlocked = async () => {
    if (!activePeriod) return;
    if (!confirm("Hapus seluruh jadwal yang tidak dikunci pada periode ini?")) return;
    await api.clearSchedule(activePeriod.id, false);
    await loadData();
  };

  if (!activePeriod) {
    return <div className="p-6 text-slate-500">Memuat periode akademik...</div>;
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Grid Jadwal Interaktif & Drag-and-Drop
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Seret kartu mata kuliah ke slot lain untuk penyesuaian manual — sistem mendeteksi bentrok & efisiensi kursi secara real-time.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <a
            href={api.exportUrl("pdf", exportFilter)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <FileText className="h-3.5 w-3.5 text-rose-600" />
            Export PDF
          </a>
          <a
            href={api.exportUrl("xlsx", exportFilter)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
            Export Excel
          </a>
          <a
            href={api.exportUrl("ics", exportFilter)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Calendar className="h-3.5 w-3.5 text-blue-600" />
            Export iCal (.ics)
          </a>
          <button
            onClick={() => void handleClearUnlocked()}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-rose-200 bg-rose-50 text-xs font-semibold text-rose-700 hover:bg-rose-100 cursor-pointer"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Reset Draft
          </button>
        </div>
      </div>

      {/* View Switcher & Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="inline-flex flex-wrap rounded-lg bg-slate-100 p-1 gap-1">
          {(
            [
              ["matrix", "Matriks Semua Ruangan"],
              ["class", "Per Kelas / Prodi"],
              ["lecturer", "Per Dosen"],
              ["room", "Per Ruangan"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setMode(id)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                mode === id
                  ? "bg-white text-blue-700 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {mode === "matrix" && (
            <select
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium bg-white"
            >
              {activePeriod.days.map((d) => (
                <option key={d} value={d}>
                  Hari: {d}
                </option>
              ))}
            </select>
          )}

          {mode === "class" && (
            <>
              <select
                value={selectedProgramId}
                onChange={(e) => {
                  const val = e.target.value ? Number(e.target.value) : "";
                  setSelectedProgramId(val);
                  setSelectedClassId("");
                }}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm bg-white"
              >
                <option value="">Semua Prodi</option>
                {programs.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code} — {p.name}
                  </option>
                ))}
              </select>
              <select
                value={selectedClassId}
                onChange={(e) =>
                  setSelectedClassId(e.target.value ? Number(e.target.value) : "")
                }
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium bg-white"
              >
                <option value="">Semua Kelas</option>
                {classes
                  .filter(
                    (c) =>
                      selectedProgramId === "" || c.program_id === selectedProgramId
                  )
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} ({c.shift}, {c.student_count} mhs)
                    </option>
                  ))}
              </select>
            </>
          )}

          {mode === "lecturer" && (
            <select
              value={selectedLecturerId}
              onChange={(e) =>
                setSelectedLecturerId(e.target.value ? Number(e.target.value) : "")
              }
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium bg-white"
            >
              {lecturers.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          )}

          {mode === "room" && (
            <select
              value={selectedRoomId}
              onChange={(e) =>
                setSelectedRoomId(e.target.value ? Number(e.target.value) : "")
              }
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium bg-white"
            >
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.code} — {r.name} ({r.capacity} krs)
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-500 gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Memuat jadwal...</span>
        </div>
      ) : allEntries.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center space-y-3">
          <Download className="h-8 w-8 text-slate-300 mx-auto" />
          <div className="font-semibold text-slate-800">
            Belum ada jadwal tersimpan pada periode ini
          </div>
          <p className="text-sm text-slate-500">
            Jalankan generator otomatis terlebih dahulu untuk mengisi jadwal optimal.
          </p>
          <Link
            href="/generate"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700"
          >
            <Sparkles className="h-4 w-4" />
            Buka Halaman Generate Otomatis
          </Link>
        </div>
      ) : (
        <TimetableGrid
          period={activePeriod}
          mode={mode}
          entries={filteredEntries}
          allEntries={allEntries}
          rooms={rooms}
          selectedDayForMatrix={selectedDay}
          onUpdated={loadData}
        />
      )}
    </div>
  );
}
