"use client";

import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Lock,
  Move,
  Unlock,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { courseCardColor } from "@/lib/colors";
import type {
  AcademicPeriod,
  MoveValidationResponse,
  Room,
  ScheduleEntry,
} from "@/lib/types";

export type ViewMode = "class" | "lecturer" | "room" | "matrix";

interface TimetableGridProps {
  period: AcademicPeriod;
  mode: ViewMode;
  entries: ScheduleEntry[];
  allEntries: ScheduleEntry[];
  rooms: Room[];
  selectedDayForMatrix: string;
  selectedBuildingId?: number | "";
  onlyOccupiedRooms?: boolean;
  onUpdated: () => Promise<void>;
}

interface PendingMove {
  entry: ScheduleEntry;
  targetDay: string;
  targetSlot: number;
  targetRoomId: number;
  validation: MoveValidationResponse | null;
  checking: boolean;
}

const STANDARD_ROW_HEIGHT = 76;
const MATRIX_ROW_HEIGHT = 70;

export function TimetableGrid({
  period,
  mode,
  entries,
  allEntries,
  rooms,
  selectedDayForMatrix,
  selectedBuildingId = "",
  onlyOccupiedRooms = false,
  onUpdated,
}: TimetableGridProps) {
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [dragOverKey, setDragOverKey] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<ScheduleEntry | null>(null);
  const [pendingMove, setPendingMove] = useState<PendingMove | null>(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const draggingEntry = useMemo(
    () => allEntries.find((e) => e.id === draggingId) || null,
    [allEntries, draggingId]
  );

  const blockedSet = useMemo(() => {
    const s = new Set<string>();
    period.blocked_slots.forEach((b) => s.add(`${b.day}::${b.slot}`));
    return s;
  }, [period.blocked_slots]);

  const slotMetaByIdx = useMemo(() => {
    const m = new Map<number, (typeof period.time_slots)[number]>();
    period.time_slots.forEach((s) => m.set(s.index, s));
    return m;
  }, [period.time_slots]);

  const showToast = (type: "ok" | "err", text: string) => {
    setToast({ type, text });
    setTimeout(() => setToast(null), 4000);
  };

  const handleToggleLock = async (entry: ScheduleEntry, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.toggleLockEntry(entry.id);
      await onUpdated();
      showToast(
        "ok",
        entry.is_locked
          ? `Kunci jadwal ${entry.course_code} dibuka.`
          : `Jadwal ${entry.course_code} dikunci.`
      );
    } catch (err) {
      showToast("err", err instanceof Error ? err.message : "Gagal mengubah kunci");
    }
  };

  const openMoveDialog = async (
    entry: ScheduleEntry,
    targetDay: string,
    targetSlot: number,
    targetRoomId: number
  ) => {
    setPendingMove({
      entry,
      targetDay,
      targetSlot,
      targetRoomId,
      validation: null,
      checking: true,
    });
    try {
      const val = await api.validateMove({
        entry_id: entry.id,
        target_day: targetDay,
        target_start_slot: targetSlot,
        target_room_id: targetRoomId,
      });
      setPendingMove((prev) =>
        prev ? { ...prev, validation: val, checking: false } : null
      );
    } catch {
      setPendingMove((prev) => (prev ? { ...prev, checking: false } : null));
    }
  };

  const handleDropCell = async (
    targetDay: string,
    targetSlot: number,
    targetRoomId: number
  ) => {
    setDragOverKey(null);
    if (!draggingEntry) return;
    const entry = draggingEntry;
    setDraggingId(null);

    if (
      entry.day === targetDay &&
      entry.start_slot === targetSlot &&
      entry.room_id === targetRoomId
    ) {
      return;
    }

    try {
      const val = await api.validateMove({
        entry_id: entry.id,
        target_day: targetDay,
        target_start_slot: targetSlot,
        target_room_id: targetRoomId,
      });
      if (val.valid && val.warnings.length === 0) {
        await api.moveEntry(entry.id, {
          target_day: targetDay,
          target_start_slot: targetSlot,
          target_room_id: targetRoomId,
          lock_after_move: entry.is_locked,
        });
        await onUpdated();
        showToast(
          "ok",
          `${entry.course_code} dipindahkan ke ${targetDay} Slot ${targetSlot} (${val.projected_seat_fill_pct}% keterisian).`
        );
      } else {
        setPendingMove({
          entry,
          targetDay,
          targetSlot,
          targetRoomId,
          validation: val,
          checking: false,
        });
      }
    } catch (err) {
      showToast("err", err instanceof Error ? err.message : "Gagal memvalidasi perpindahan");
    }
  };

  const handleConfirmMove = async (lockAfter: boolean) => {
    if (!pendingMove) return;
    setSaving(true);
    try {
      await api.moveEntry(pendingMove.entry.id, {
        target_day: pendingMove.targetDay,
        target_start_slot: pendingMove.targetSlot,
        target_room_id: pendingMove.targetRoomId,
        lock_after_move: lockAfter,
      });
      setPendingMove(null);
      setSelectedEntry(null);
      await onUpdated();
      showToast("ok", "Jadwal berhasil diperbarui.");
    } catch (err) {
      showToast("err", err instanceof Error ? err.message : "Gagal menyimpan perpindahan");
    } finally {
      setSaving(false);
    }
  };

  const quickClientCanDrop = (day: string, startSlot: number): boolean => {
    if (!draggingEntry) return false;
    const first = slotMetaByIdx.get(startSlot);
    if (!first) return false;
    for (let i = 0; i < draggingEntry.duration_slots; i += 1) {
      const m = slotMetaByIdx.get(startSlot + i);
      if (!m || m.block_index !== first.block_index) return false;
      if (blockedSet.has(`${day}::${startSlot + i}`)) return false;
    }
    return true;
  };

  const renderEntryCard = (entry: ScheduleEntry, isMatrix = false, stretchPx?: number) => {
    const color = courseCardColor(entry.course_code);
    const clsLabel =
      entry.class_code +
      (entry.extra_class_codes.length > 0
        ? `+${entry.extra_class_codes.join("+")}`
        : "");
    const fillBadgeColor =
      entry.seat_fill_pct >= 75
        ? "bg-emerald-600/15 text-emerald-900"
        : entry.seat_fill_pct >= 55
        ? "bg-amber-600/15 text-amber-900"
        : "bg-rose-600/15 text-rose-900";

    return (
      <div
        draggable
        onDragStart={(e) => {
          setDraggingId(entry.id);
          e.dataTransfer.setData("text/plain", String(entry.id));
          e.dataTransfer.effectAllowed = "move";
        }}
        onDragEnd={() => {
          setDraggingId(null);
          setDragOverKey(null);
        }}
        onClick={() => setSelectedEntry(entry)}
        style={stretchPx ? { minHeight: `${stretchPx}px` } : undefined}
        className={`w-full h-full rounded-lg border p-2.5 cursor-grab active:cursor-grabbing shadow-2xs hover:shadow-md transition-all flex flex-col justify-between select-none overflow-hidden ${color} ${
          draggingId === entry.id ? "opacity-50" : ""
        }`}
      >
        <div className="min-w-0">
          <div className="flex items-start justify-between gap-1.5">
            <span className="font-bold text-[11px] leading-tight break-words">
              {entry.course_code} · {clsLabel}
            </span>
            <button
              type="button"
              onClick={(ev) => void handleToggleLock(entry, ev)}
              title={entry.is_locked ? "Terkunci (klik untuk buka)" : "Klik untuk kunci slot"}
              className="p-0.5 rounded hover:bg-black/10 shrink-0"
            >
              {entry.is_locked ? (
                <Lock className="h-3 w-3 text-slate-800" />
              ) : (
                <Unlock className="h-3 w-3 opacity-45" />
              )}
            </button>
          </div>
          {(!isMatrix || entry.duration_slots >= 2) && (
            <div className="text-[11px] font-medium mt-1 line-clamp-2 leading-snug">
              {entry.course_name}
            </div>
          )}
        </div>

        <div className="mt-2 pt-1.5 border-t border-black/10 text-[10px] space-y-1">
          {mode !== "lecturer" && (
            <div className="truncate font-medium opacity-90">{entry.lecturer_name}</div>
          )}
          <div className="flex items-center justify-between gap-1.5 flex-wrap">
            <span className="font-semibold whitespace-nowrap">
              {mode === "room" || isMatrix ? entry.time_range : entry.room_code}
            </span>
            <span
              className={`px-1.5 py-0.5 rounded text-[9.5px] font-bold whitespace-nowrap ${fillBadgeColor}`}
            >
              {entry.student_count}/{entry.room_capacity} ({Math.round(entry.seat_fill_pct)}%)
            </span>
          </div>
        </div>
      </div>
    );
  };

  const activeRooms = useMemo(() => rooms.filter((r) => r.is_active), [rooms]);

  const matrixRooms = useMemo(() => {
    const dayEntries = allEntries.filter((e) => e.day === selectedDayForMatrix);
    const occupiedRoomIds = new Set(dayEntries.map((e) => e.room_id));
    return activeRooms.filter((r) => {
      if (selectedBuildingId !== "" && r.building_id !== Number(selectedBuildingId)) {
        return false;
      }
      if (onlyOccupiedRooms && !occupiedRoomIds.has(r.id)) {
        return false;
      }
      return true;
    });
  }, [activeRooms, allEntries, selectedDayForMatrix, selectedBuildingId, onlyOccupiedRooms]);

  const renderStandardGrid = () => {
    const startMap = new Map<string, ScheduleEntry[]>();
    const coveredMap = new Set<string>();

    entries.forEach((e) => {
      const k = `${e.day}::${e.start_slot}`;
      const arr = startMap.get(k) || [];
      arr.push(e);
      startMap.set(k, arr);
      for (let off = 1; off < e.duration_slots; off += 1) {
        coveredMap.add(`${e.day}::${e.start_slot + off}`);
      }
    });

    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-x-auto">
        <table className="w-full border-collapse min-w-[820px] table-fixed">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="w-32 py-3 px-3 text-left text-xs font-semibold text-slate-600 uppercase">
                Jam / Slot
              </th>
              {period.days.map((day) => (
                <th
                  key={day}
                  className="py-3 px-2 text-center text-xs font-bold text-slate-800 uppercase border-l border-slate-200"
                >
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {period.time_slots.map((slot) => (
              <React.Fragment key={slot.index}>
                <tr className="border-t border-slate-200 h-[76px]">
                  <td className="py-2 px-3 align-top bg-slate-50/70">
                    <div className="text-xs font-bold text-slate-800">Slot {slot.index}</div>
                    <div className="text-[11px] text-slate-500">{slot.label}</div>
                  </td>
                  {period.days.map((day) => {
                    const cellKey = `${day}::${slot.index}`;
                    const starts = startMap.get(cellKey) || [];
                    const isCovered = coveredMap.has(cellKey);
                    const isBlocked = blockedSet.has(cellKey);

                    if (isCovered && entries.length <= 20 && starts.length === 0) {
                      return null;
                    }

                    const firstEntry = starts[0];
                    const rowSpan =
                      starts.length === 1 && entries.length <= 20
                        ? firstEntry.duration_slots
                        : 1;

                    const isDragOver = dragOverKey === cellKey;
                    const canHoverDrop = isDragOver && quickClientCanDrop(day, slot.index);
                    const tdHeight = rowSpan * STANDARD_ROW_HEIGHT;

                    return (
                      <td
                        key={cellKey}
                        rowSpan={rowSpan}
                        style={{ height: `${tdHeight}px` }}
                        onDragOver={(ev) => {
                          if (!draggingEntry || isBlocked) return;
                          ev.preventDefault();
                          setDragOverKey(cellKey);
                        }}
                        onDragLeave={() => {
                          if (dragOverKey === cellKey) setDragOverKey(null);
                        }}
                        onDrop={(ev) => {
                          ev.preventDefault();
                          if (!draggingEntry || isBlocked) return;
                          const targetRoomId =
                            mode === "room" && entries[0]
                              ? entries[0].room_id
                              : draggingEntry.room_id;
                          void handleDropCell(day, slot.index, targetRoomId);
                        }}
                        className={`p-1.5 border-l border-slate-200 align-top transition-colors ${
                          isBlocked
                            ? "bg-slate-100 text-center"
                            : isDragOver
                            ? canHoverDrop
                              ? "bg-emerald-50 ring-2 ring-inset ring-emerald-400"
                              : "bg-rose-50 ring-2 ring-inset ring-rose-400"
                            : "hover:bg-slate-50/60"
                        }`}
                      >
                        {isBlocked ? (
                          <div className="text-[11px] text-slate-400 italic py-4">
                            Diblokir
                          </div>
                        ) : starts.length > 0 ? (
                          <div className="space-y-1.5 h-full">
                            {starts.map((st) => (
                              <div key={st.id} className="h-full">
                                {renderEntryCard(
                                  st,
                                  false,
                                  starts.length === 1 ? tdHeight - 12 : undefined
                                )}
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </td>
                    );
                  })}
                </tr>

                {slot.break_after_minutes >= 20 && (
                  <tr>
                    <td
                      colSpan={period.days.length + 1}
                      className="py-1.5 px-3 text-center text-[11px] font-semibold bg-amber-50 text-amber-800 border-y border-amber-200"
                    >
                      {slot.break_after_label || "Istirahat"} ({slot.break_after_minutes} menit)
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderRoomMatrix = () => {
    const dayEntries = allEntries.filter((e) => e.day === selectedDayForMatrix);
    const startMap = new Map<string, ScheduleEntry>();
    const coveredSet = new Set<string>();
    const roomSlotsToday = new Map<number, number>();

    dayEntries.forEach((e) => {
      startMap.set(`${e.room_id}::${e.start_slot}`, e);
      roomSlotsToday.set(e.room_id, (roomSlotsToday.get(e.room_id) || 0) + e.duration_slots);
      for (let off = 1; off < e.duration_slots; off += 1) {
        coveredSet.add(`${e.room_id}::${e.start_slot + off}`);
      }
    });

    if (matrixRooms.length === 0) {
      return (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-sm text-slate-500">
          Tidak ada ruangan yang sesuai dengan filter pada hari {selectedDayForMatrix}.
        </div>
      );
    }

    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-x-auto">
        <table className="w-full border-collapse table-fixed">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="w-28 py-3 px-2.5 text-left text-xs font-semibold text-slate-600 uppercase sticky left-0 bg-slate-50 z-20 border-r border-slate-200">
                Slot ({selectedDayForMatrix})
              </th>
              {matrixRooms.map((r) => {
                const usedToday = roomSlotsToday.get(r.id) || 0;
                return (
                  <th
                    key={r.id}
                    className="py-2.5 px-2 text-center border-l border-slate-200 w-[166px]"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900">{r.code}</span>
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                          usedToday > 0
                            ? "bg-blue-50 text-blue-700"
                            : "bg-slate-100 text-slate-400"
                        }`}
                      >
                        {usedToday}/{period.time_slots.length}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-normal mt-0.5 truncate">
                      {r.room_type} · {r.capacity} krs
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {period.time_slots.map((slot) => (
              <React.Fragment key={slot.index}>
                <tr className="border-t border-slate-200 h-[70px]">
                  <td className="py-2 px-2.5 align-top bg-slate-50 sticky left-0 z-10 border-r border-slate-200">
                    <div className="text-xs font-bold text-slate-800">#{slot.index}</div>
                    <div className="text-[10px] text-slate-500 whitespace-nowrap">
                      {slot.label}
                    </div>
                  </td>
                  {matrixRooms.map((r) => {
                    const key = `${r.id}::${slot.index}`;
                    const entry = startMap.get(key);
                    const isCovered = coveredSet.has(key);
                    const isBlocked = blockedSet.has(`${selectedDayForMatrix}::${slot.index}`);

                    if (isCovered) return null;

                    const isDragOver = dragOverKey === key;
                    const canHoverDrop =
                      isDragOver && quickClientCanDrop(selectedDayForMatrix, slot.index);
                    const dur = entry ? entry.duration_slots : 1;
                    const tdHeight = dur * MATRIX_ROW_HEIGHT;

                    return (
                      <td
                        key={key}
                        rowSpan={dur}
                        style={{ height: `${tdHeight}px` }}
                        onDragOver={(ev) => {
                          if (!draggingEntry || isBlocked) return;
                          ev.preventDefault();
                          setDragOverKey(key);
                        }}
                        onDragLeave={() => {
                          if (dragOverKey === key) setDragOverKey(null);
                        }}
                        onDrop={(ev) => {
                          ev.preventDefault();
                          if (!draggingEntry || isBlocked) return;
                          void handleDropCell(selectedDayForMatrix, slot.index, r.id);
                        }}
                        className={`p-1.5 border-l border-slate-200 align-top ${
                          isBlocked
                            ? "bg-slate-100 text-center"
                            : isDragOver
                            ? canHoverDrop
                              ? "bg-emerald-50 ring-2 ring-inset ring-emerald-400"
                              : "bg-rose-50 ring-2 ring-inset ring-rose-400"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        {isBlocked ? (
                          <div className="text-[10px] text-slate-400 italic py-4">Blokir</div>
                        ) : entry ? (
                          renderEntryCard(entry, true, tdHeight - 12)
                        ) : null}
                      </td>
                    );
                  })}
                </tr>
                {slot.break_after_minutes >= 20 && (
                  <tr>
                    <td
                      colSpan={matrixRooms.length + 1}
                      className="py-1.5 px-3 text-center text-[11px] font-semibold bg-amber-50 text-amber-800 border-y border-amber-200"
                    >
                      {slot.break_after_label || "Istirahat"} ({slot.break_after_minutes} menit)
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {toast && (
        <div
          className={`fixed bottom-5 right-5 z-50 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium flex items-center gap-2 ${
            toast.type === "ok"
              ? "bg-emerald-900 text-white border-emerald-700"
              : "bg-rose-900 text-white border-rose-700"
          }`}
        >
          {toast.type === "ok" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-300" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-rose-300" />
          )}
          <span>{toast.text}</span>
        </div>
      )}

      {mode === "matrix" ? renderRoomMatrix() : renderStandardGrid()}

      {/* Detail Modal */}
      {selectedEntry && !pendingMove && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs font-bold text-blue-700 uppercase">
                  {selectedEntry.course_code} · {selectedEntry.program_name}
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-0.5">
                  {selectedEntry.course_name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div>
                <div className="text-xs text-slate-500">Kelas</div>
                <div className="font-semibold">
                  {selectedEntry.class_code}
                  {selectedEntry.extra_class_codes.length > 0
                    ? ` + ${selectedEntry.extra_class_codes.join(", ")}`
                    : ""}{" "}
                  ({selectedEntry.shift})
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Waktu</div>
                <div className="font-semibold">
                  {selectedEntry.day}, {selectedEntry.time_range} (Slot{" "}
                  {selectedEntry.start_slot}-
                  {selectedEntry.start_slot + selectedEntry.duration_slots - 1})
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Dosen Pengampu</div>
                <div className="font-semibold">
                  {selectedEntry.lecturer_name}
                  {selectedEntry.co_lecturer_name
                    ? ` & ${selectedEntry.co_lecturer_name}`
                    : ""}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Ruangan & Efisiensi</div>
                <div className="font-semibold">
                  {selectedEntry.room_code} ({selectedEntry.building_code}) ·{" "}
                  {selectedEntry.student_count}/{selectedEntry.room_capacity} mhs (
                  {selectedEntry.seat_fill_pct}%)
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
              <button
                type="button"
                onClick={() => void handleToggleLock(selectedEntry)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                {selectedEntry.is_locked ? (
                  <>
                    <Unlock className="h-4 w-4" /> Buka Kunci
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4" /> Kunci Slot Ini
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={() => {
                  const e = selectedEntry;
                  setSelectedEntry(null);
                  void openMoveDialog(e, e.day, e.start_slot, e.room_id);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
              >
                <Move className="h-4 w-4" />
                Pindah Waktu / Tukar Ruangan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Move & Conflict Validator Modal */}
      {pendingMove && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Validasi Perpindahan Jadwal
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {pendingMove.entry.course_code} — {pendingMove.entry.course_name} (
                  {pendingMove.entry.student_count} mahasiswa, {pendingMove.entry.duration_slots}{" "}
                  slot)
                </p>
              </div>
              <button
                onClick={() => setPendingMove(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <label className="block">
                <span className="text-xs font-medium text-slate-600">Hari</span>
                <select
                  value={pendingMove.targetDay}
                  onChange={(e) =>
                    void openMoveDialog(
                      pendingMove.entry,
                      e.target.value,
                      pendingMove.targetSlot,
                      pendingMove.targetRoomId
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {period.days.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Slot Mulai</span>
                <select
                  value={pendingMove.targetSlot}
                  onChange={(e) =>
                    void openMoveDialog(
                      pendingMove.entry,
                      pendingMove.targetDay,
                      Number(e.target.value),
                      pendingMove.targetRoomId
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {period.time_slots.map((s) => (
                    <option key={s.index} value={s.index}>
                      Slot {s.index} ({s.start_time})
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Ruangan</span>
                <select
                  value={pendingMove.targetRoomId}
                  onChange={(e) =>
                    void openMoveDialog(
                      pendingMove.entry,
                      pendingMove.targetDay,
                      pendingMove.targetSlot,
                      Number(e.target.value)
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {activeRooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.code} ({r.capacity} krs, {r.room_type})
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {pendingMove.checking ? (
              <div className="p-3 rounded-lg bg-slate-50 text-xs text-slate-600">
                Memeriksa bentrok ruangan, dosen, kelas, dan kapasitas...
              </div>
            ) : (
              pendingMove.validation && (
                <div className="space-y-2">
                  {pendingMove.validation.valid ? (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>
                        Slot & ruangan bebas bentrok! Proyeksi keterisian kursi:{" "}
                        <strong>{pendingMove.validation.projected_seat_fill_pct}%</strong> (sisa{" "}
                        {pendingMove.validation.projected_seat_waste} kursi).
                      </span>
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-1">
                      <div className="font-bold">Terdeteksi Bentrok / Pelanggaran Aturan:</div>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {pendingMove.validation.conflicts.map((c, idx) => (
                          <li key={idx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {pendingMove.validation.warnings.length > 0 && (
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs space-y-1">
                      <div className="font-bold">Catatan Efisiensi / Beban:</div>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {pendingMove.validation.warnings.map((w, idx) => (
                          <li key={idx}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setPendingMove(null)}
                className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Batal
              </button>
              <button
                type="button"
                disabled={
                  saving ||
                  pendingMove.checking ||
                  !pendingMove.validation?.valid
                }
                onClick={() => void handleConfirmMove(true)}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
              >
                {saving ? "Menyimpan..." : "Simpan & Kunci"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
