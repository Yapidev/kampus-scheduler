"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Building2, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Building, Room } from "@/lib/types";

const ROOM_TYPES = ["Teori", "Lab Komputer", "Lab Jaringan", "Lab Bahasa", "Studio", "Aula"];

export default function RuanganMasterPage() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const [bldCode, setBldCode] = useState("");
  const [bldName, setBldName] = useState("");
  const [bldZone, setBldZone] = useState("Zona Utama");

  const [buildingId, setBuildingId] = useState<number | "">("");
  const [roomCode, setRoomCode] = useState("");
  const [roomName, setRoomName] = useState("");
  const [floor, setFloor] = useState(1);
  const [capacity, setCapacity] = useState(40);
  const [roomType, setRoomType] = useState("Teori");
  const [facilitiesInput, setFacilitiesInput] = useState("Proyektor, AC, Whiteboard");

  const loadData = useCallback(async () => {
    const [bList, rList] = await Promise.all([api.listBuildings(), api.listRooms()]);
    setBuildings(bList);
    setRooms(rList);
    if (bList.length > 0 && buildingId === "") setBuildingId(bList[0].id);
  }, [buildingId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleAddBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrMsg(null);
    try {
      await api.createBuilding({
        code: bldCode.trim(),
        name: bldName.trim(),
        floor_count: 4,
        campus_zone: bldZone,
      });
      setBldCode("");
      setBldName("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal menambah gedung");
    }
  };

  const handleAddRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!buildingId) return;
    setErrMsg(null);
    try {
      const facilities = facilitiesInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await api.createRoom({
        building_id: Number(buildingId),
        code: roomCode.trim(),
        name: roomName.trim(),
        floor,
        capacity,
        room_type: roomType,
        facilities,
        is_active: true,
      });
      setRoomCode("");
      setRoomName("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal menambah ruangan");
    }
  };

  const toggleActive = async (r: Room) => {
    await api.updateRoom(r.id, { is_active: !r.is_active });
    await loadData();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Master Gedung & Ruangan</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kapasitas, tipe ruangan, dan fasilitas menjadi acuan utama optimasi Best-Fit solver.
        </p>
      </div>

      {errMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {errMsg}
        </div>
      )}

      {/* Buildings */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <h2 className="font-semibold text-slate-900 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-blue-600" />
          Daftar Gedung Kampus
        </h2>
        <form
          onSubmit={(e) => void handleAddBuilding(e)}
          className="grid grid-cols-1 sm:grid-cols-4 gap-2"
        >
          <input
            type="text"
            required
            placeholder="Kode (GDC)"
            value={bldCode}
            onChange={(e) => setBldCode(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="text"
            required
            placeholder="Nama Gedung"
            value={bldName}
            onChange={(e) => setBldName(e.target.value)}
            className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Zona"
              value={bldZone}
              onChange={(e) => setBldZone(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 cursor-pointer"
            >
              Tambah
            </button>
          </div>
        </form>

        <div className="flex flex-wrap gap-2">
          {buildings.map((b) => (
            <div
              key={b.id}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-sm"
            >
              <span className="font-bold text-slate-900">{b.code}</span>
              <span className="text-slate-600">{b.name}</span>
              <span className="text-xs text-slate-400">({b.campus_zone})</span>
              <button
                onClick={async () => {
                  await api.deleteBuilding(b.id);
                  await loadData();
                }}
                className="text-slate-400 hover:text-rose-600 cursor-pointer"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Add Room Form */}
      <form
        onSubmit={(e) => void handleAddRoom(e)}
        className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
      >
        <h2 className="font-semibold text-slate-900">Tambah Ruangan Baru</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Gedung</span>
            <select
              value={buildingId}
              onChange={(e) => setBuildingId(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              {buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.code} — {b.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Kode Ruang</span>
            <input
              type="text"
              required
              placeholder="A-103"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block sm:col-span-2">
            <span className="text-xs font-medium text-slate-600">Nama Ruangan</span>
            <input
              type="text"
              required
              placeholder="Ruang Kuliah A103"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Kapasitas</span>
            <input
              type="number"
              min={5}
              max={1000}
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Tipe Ruang</span>
            <select
              value={roomType}
              onChange={(e) => setRoomType(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              {ROOM_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-slate-600">Lantai</span>
            <input
              type="number"
              min={1}
              max={30}
              value={floor}
              onChange={(e) => setFloor(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block sm:col-span-4">
            <span className="text-xs font-medium text-slate-600">
              Fasilitas (pisahkan dengan koma)
            </span>
            <input
              type="text"
              value={facilitiesInput}
              onChange={(e) => setFacilitiesInput(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
            >
              <Plus className="h-4 w-4" />
              Simpan Ruang
            </button>
          </div>
        </div>
      </form>

      {/* Rooms Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Kode & Nama</th>
                <th className="py-3 px-4">Gedung / Lt</th>
                <th className="py-3 px-4">Tipe</th>
                <th className="py-3 px-4 text-right">Kapasitas</th>
                <th className="py-3 px-4">Fasilitas</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rooms.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4">
                    <div className="font-bold text-slate-900">{r.code}</div>
                    <div className="text-xs text-slate-500">{r.name}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-700">
                    {r.building_code} · Lt {r.floor}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {r.room_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-semibold">{r.capacity} kursi</td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {r.facilities.map((f) => (
                        <span
                          key={f}
                          className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => void toggleActive(r)}
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border cursor-pointer ${
                        r.is_active
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-slate-100 text-slate-500 border-slate-200"
                      }`}
                    >
                      {r.is_active ? "Aktif" : "Non-Aktif"}
                    </button>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={async () => {
                        await api.deleteRoom(r.id);
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
    </div>
  );
}
