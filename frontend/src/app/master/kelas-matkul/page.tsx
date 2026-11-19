"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type {
  Course,
  CourseOffering,
  Lecturer,
  StudentClass,
  StudyProgram,
} from "@/lib/types";
import { usePeriod } from "@/components/PeriodContext";

const ROOM_TYPES = ["Teori", "Lab Komputer", "Lab Jaringan", "Lab Bahasa", "Studio", "Aula"];

export default function KelasMatkulMasterPage() {
  const { activePeriod } = usePeriod();
  const [tab, setTab] = useState<"offerings" | "classes" | "courses">("offerings");
  const [programs, setPrograms] = useState<StudyProgram[]>([]);
  const [classes, setClasses] = useState<StudentClass[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [lecturers, setLecturers] = useState<Lecturer[]>([]);
  const [offerings, setOfferings] = useState<CourseOffering[]>([]);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const [clsProgId, setClsProgId] = useState<number | "">("");
  const [clsCode, setClsCode] = useState("");
  const [clsSem, setClsSem] = useState(1);
  const [clsShift, setClsShift] = useState<"Reguler" | "Karyawan">("Reguler");
  const [clsCount, setClsCount] = useState(35);

  const [crsProgId, setCrsProgId] = useState<number | "">("");
  const [crsCode, setCrsCode] = useState("");
  const [crsName, setCrsName] = useState("");
  const [crsSks, setCrsSks] = useState(3);
  const [crsType, setCrsType] = useState<"Teori" | "Praktikum" | "Teori+Praktikum">("Teori");
  const [crsRoomType, setCrsRoomType] = useState("Teori");
  const [crsFac, setCrsFac] = useState("Proyektor");

  const [offCourseId, setOffCourseId] = useState<number | "">("");
  const [offClassId, setOffClassId] = useState<number | "">("");
  const [offExtraClassId, setOffExtraClassId] = useState<number | "">("");
  const [offLecId, setOffLecId] = useState<number | "">("");
  const [offCoLecId, setOffCoLecId] = useState<number | "">("");
  const [offSessions, setOffSessions] = useState(1);
  const [offDuration, setOffDuration] = useState(3);

  const loadData = useCallback(async () => {
    if (!activePeriod) return;
    const [pList, clsList, crsList, lecList, offList] = await Promise.all([
      api.listPrograms(),
      api.listClasses(activePeriod.id),
      api.listCourses(),
      api.listLecturers(),
      api.listOfferings(activePeriod.id),
    ]);
    setPrograms(pList);
    setClasses(clsList);
    setCourses(crsList);
    setLecturers(lecList);
    setOfferings(offList);

    if (pList.length > 0) {
      if (clsProgId === "") setClsProgId(pList[0].id);
      if (crsProgId === "") setCrsProgId(pList[0].id);
    }
    if (crsList.length > 0 && offCourseId === "") {
      setOffCourseId(crsList[0].id);
      setOffDuration(crsList[0].sks);
    }
    if (clsList.length > 0 && offClassId === "") setOffClassId(clsList[0].id);
    if (lecList.length > 0 && offLecId === "") setOffLecId(lecList[0].id);
  }, [activePeriod, clsProgId, crsProgId, offCourseId, offClassId, offLecId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleAddClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePeriod || !clsProgId) return;
    setErrMsg(null);
    try {
      await api.createClass({
        period_id: activePeriod.id,
        program_id: Number(clsProgId),
        code: clsCode.trim(),
        semester: clsSem,
        shift: clsShift,
        student_count: clsCount,
      });
      setClsCode("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal membuat kelas");
    }
  };

  const handleAddCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!crsProgId) return;
    setErrMsg(null);
    try {
      await api.createCourse({
        program_id: Number(crsProgId),
        code: crsCode.trim(),
        name: crsName.trim(),
        sks: crsSks,
        course_type: crsType,
        required_room_type: crsRoomType,
        required_facilities: crsFac
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      setCrsCode("");
      setCrsName("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal membuat mata kuliah");
    }
  };

  const handleAddOffering = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePeriod || !offCourseId || !offClassId || !offLecId) return;
    setErrMsg(null);
    try {
      await api.createOffering({
        period_id: activePeriod.id,
        course_id: Number(offCourseId),
        class_id: Number(offClassId),
        extra_class_ids:
          offExtraClassId && Number(offExtraClassId) !== Number(offClassId)
            ? [Number(offExtraClassId)]
            : [],
        lecturer_id: Number(offLecId),
        co_lecturer_id: offCoLecId ? Number(offCoLecId) : null,
        sessions_per_week: offSessions,
        session_duration_slots: offDuration,
      });
      setOffExtraClassId("");
      setOffCoLecId("");
      await loadData();
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Gagal menambah plotting kuliah");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Master Kelas, Mata Kuliah & Plotting
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Kelola rombongan belajar kelas, kurikulum SKS, serta penawaran mata kuliah yang akan dijadwalkan.
          </p>
        </div>

        <div className="inline-flex rounded-lg bg-slate-100 p-1 gap-1">
          {(
            [
              ["offerings", `Plotting Kuliah (${offerings.length})`],
              ["classes", `Kelas (${classes.length})`],
              ["courses", `Mata Kuliah (${courses.length})`],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer ${
                tab === id ? "bg-white text-blue-700 shadow-2xs" : "text-slate-600"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {errMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {errMsg}
        </div>
      )}

      {/* TAB 1: OFFERINGS */}
      {tab === "offerings" && (
        <div className="space-y-5">
          <form
            onSubmit={(e) => void handleAddOffering(e)}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
          >
            <h2 className="font-semibold text-slate-900">
              Tambah Plotting Kuliah ({activePeriod?.name})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <label className="block">
                <span className="text-xs font-medium text-slate-600">Mata Kuliah</span>
                <select
                  value={offCourseId}
                  onChange={(e) => {
                    const cid = Number(e.target.value);
                    setOffCourseId(cid);
                    const c = courses.find((x) => x.id === cid);
                    if (c) setOffDuration(c.sks);
                  }}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} — {c.name} ({c.sks} SKS)
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Kelas Utama</span>
                <select
                  value={offClassId}
                  onChange={(e) => setOffClassId(Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} ({c.shift}, {c.student_count} mhs)
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">
                  Gabung Kelas (Opsional MKU)
                </span>
                <select
                  value={offExtraClassId}
                  onChange={(e) =>
                    setOffExtraClassId(e.target.value ? Number(e.target.value) : "")
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  <option value="">Tidak digabung</option>
                  {classes
                    .filter((c) => c.id !== offClassId)
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        + {c.code} ({c.student_count} mhs)
                      </option>
                    ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Dosen Pengampu</span>
                <select
                  value={offLecId}
                  onChange={(e) => setOffLecId(Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  {lecturers.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">
                  Co-Dosen / Team Teaching
                </span>
                <select
                  value={offCoLecId}
                  onChange={(e) =>
                    setOffCoLecId(e.target.value ? Number(e.target.value) : "")
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
                >
                  <option value="">Tidak ada</option>
                  {lecturers
                    .filter((l) => l.id !== offLecId)
                    .map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Pertemuan / Minggu</span>
                <input
                  type="number"
                  min={1}
                  max={4}
                  value={offSessions}
                  onChange={(e) => setOffSessions(Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>

              <label className="block">
                <span className="text-xs font-medium text-slate-600">Durasi Slot / Sesi</span>
                <input
                  type="number"
                  min={1}
                  max={6}
                  value={offDuration}
                  onChange={(e) => setOffDuration(Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>

              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-4 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
                >
                  <Plus className="h-4 w-4" />
                  Tambah Plotting
                </button>
              </div>
            </div>
          </form>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Mata Kuliah</th>
                    <th className="py-3 px-4">Kelas & Mhs</th>
                    <th className="py-3 px-4">Dosen Pengampu</th>
                    <th className="py-3 px-4">Kebutuhan Ruang</th>
                    <th className="py-3 px-4 text-center">Pola Sesi</th>
                    <th className="py-3 px-4 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {offerings.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">
                          {o.course_code} · {o.course_name}
                        </div>
                        <div className="text-xs text-slate-500">{o.sks} SKS</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-800">
                          {o.class_code}
                          {o.extra_class_codes.length > 0
                            ? ` + ${o.extra_class_codes.join(", ")}`
                            : ""}
                        </div>
                        <div className="text-xs text-slate-500">
                          {o.shift} · {o.effective_student_count} mahasiswa
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        <div>{o.lecturer_name}</div>
                        {o.co_lecturer_name && (
                          <div className="text-xs text-slate-500">
                            Co: {o.co_lecturer_name}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {o.required_room_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center text-xs font-semibold text-slate-700">
                        {o.sessions_per_week}× / mgg ({o.session_duration_slots} slot)
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={async () => {
                            await api.deleteOffering(o.id);
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
      )}

      {/* TAB 2: CLASSES */}
      {tab === "classes" && (
        <div className="space-y-5">
          <form
            onSubmit={(e) => void handleAddClass(e)}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs grid grid-cols-1 sm:grid-cols-6 gap-3"
          >
            <select
              value={clsProgId}
              onChange={(e) => setClsProgId(Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              {programs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code} — {p.name}
                </option>
              ))}
            </select>
            <input
              type="text"
              required
              placeholder="Kode (IF-3B)"
              value={clsCode}
              onChange={(e) => setClsCode(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="number"
              min={1}
              max={14}
              value={clsSem}
              onChange={(e) => setClsSem(Number(e.target.value))}
              placeholder="Semester"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={clsShift}
              onChange={(e) => setClsShift(e.target.value as "Reguler" | "Karyawan")}
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              <option value="Reguler">Reguler</option>
              <option value="Karyawan">Karyawan</option>
            </select>
            <input
              type="number"
              min={1}
              max={500}
              value={clsCount}
              onChange={(e) => setClsCount(Number(e.target.value))}
              placeholder="Jumlah Mhs"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
            >
              Tambah Kelas
            </button>
          </form>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Kode Kelas</th>
                  <th className="py-3 px-4">Prodi</th>
                  <th className="py-3 px-4">Semester</th>
                  <th className="py-3 px-4">Shift</th>
                  <th className="py-3 px-4 text-right">Mahasiswa</th>
                  <th className="py-3 px-4 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {classes.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-bold text-slate-900">{c.code}</td>
                    <td className="py-3 px-4">{c.program_name}</td>
                    <td className="py-3 px-4">Semester {c.semester}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          c.shift === "Reguler"
                            ? "bg-blue-50 text-blue-700"
                            : "bg-violet-50 text-violet-700"
                        }`}
                      >
                        {c.shift}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">{c.student_count} mhs</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={async () => {
                          await api.deleteClass(c.id);
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
      )}

      {/* TAB 3: COURSES */}
      {tab === "courses" && (
        <div className="space-y-5">
          <form
            onSubmit={(e) => void handleAddCourse(e)}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-7 gap-3"
          >
            <select
              value={crsProgId}
              onChange={(e) => setCrsProgId(Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              {programs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input
              type="text"
              required
              placeholder="Kode (IF401)"
              value={crsCode}
              onChange={(e) => setCrsCode(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="text"
              required
              placeholder="Nama Mata Kuliah"
              value={crsName}
              onChange={(e) => setCrsName(e.target.value)}
              className="sm:col-span-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              type="number"
              min={1}
              max={8}
              value={crsSks}
              onChange={(e) => setCrsSks(Number(e.target.value))}
              placeholder="SKS"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={crsRoomType}
              onChange={(e) => setCrsRoomType(e.target.value)}
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              {ROOM_TYPES.map((t) => (
                <option key={t} value={t}>
                  Ruang: {t}
                </option>
              ))}
            </select>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 cursor-pointer"
            >
              Tambah MK
            </button>
            <select
              value={crsType}
              onChange={(e) =>
                setCrsType(
                  e.target.value as "Teori" | "Praktikum" | "Teori+Praktikum"
                )
              }
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
            >
              <option value="Teori">Teori</option>
              <option value="Praktikum">Praktikum</option>
              <option value="Teori+Praktikum">Teori+Praktikum</option>
            </select>
            <input
              type="text"
              placeholder="Fasilitas Wajib (koma): Proyektor, PC Workstation"
              value={crsFac}
              onChange={(e) => setCrsFac(e.target.value)}
              className="sm:col-span-6 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </form>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Kode</th>
                  <th className="py-3 px-4">Nama Mata Kuliah</th>
                  <th className="py-3 px-4">Prodi</th>
                  <th className="py-3 px-4 text-center">SKS</th>
                  <th className="py-3 px-4">Kebutuhan Ruang</th>
                  <th className="py-3 px-4">Fasilitas Wajib</th>
                  <th className="py-3 px-4 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {courses.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-bold text-slate-900">{c.code}</td>
                    <td className="py-3 px-4 font-medium">{c.name}</td>
                    <td className="py-3 px-4 text-slate-600">{c.program_code}</td>
                    <td className="py-3 px-4 text-center font-semibold">{c.sks}</td>
                    <td className="py-3 px-4">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {c.required_room_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      {c.required_facilities.join(", ") || "-"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={async () => {
                          await api.deleteCourse(c.id);
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
      )}
    </div>
  );
}
