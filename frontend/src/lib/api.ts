import type {
  AcademicPeriod,
  Building,
  Course,
  CourseOffering,
  EfficiencySummary,
  Faculty,
  GenerateResponse,
  Lecturer,
  MoveValidationResponse,
  OptimizationWeights,
  PreflightReport,
  Room,
  ScheduleEntry,
  ScheduleJobStatus,
  ScheduleRunSummary,
  StudentClass,
  StudyProgram,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!res.ok) {
    let msg = `Request gagal (${res.status})`;
    if (parsed && typeof parsed === "object" && "detail" in parsed) {
      const d = (parsed as { detail: unknown }).detail;
      if (typeof d === "string") {
        msg = d;
      } else if (d && typeof d === "object" && "message" in d) {
        msg = String((d as { message: unknown }).message);
      }
    }
    throw new ApiError(msg, res.status, parsed);
  }

  return parsed as T;
}

export function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      sp.set(k, String(v));
    }
  });
  const q = sp.toString();
  return q ? `?${q}` : "";
}

export const api = {
  // Periods & Seed
  listPeriods: () => request<AcademicPeriod[]>("/api/periods"),
  createPeriod: (data: Partial<AcademicPeriod>) =>
    request<AcademicPeriod>("/api/periods", { method: "POST", body: JSON.stringify(data) }),
  updatePeriod: (id: number, data: Partial<AcademicPeriod>) =>
    request<AcademicPeriod>(`/api/periods/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  activatePeriod: (id: number) =>
    request<AcademicPeriod>(`/api/periods/${id}/activate`, { method: "POST" }),
  togglePublishPeriod: (id: number) =>
    request<AcademicPeriod>(`/api/periods/${id}/publish`, { method: "POST" }),
  resetSeed: () => request<AcademicPeriod>("/api/seed", { method: "POST" }),

  // Faculties & Programs
  listFaculties: () => request<Faculty[]>("/api/faculties"),
  createFaculty: (data: Omit<Faculty, "id">) =>
    request<Faculty>("/api/faculties", { method: "POST", body: JSON.stringify(data) }),
  deleteFaculty: (id: number) => request<void>(`/api/faculties/${id}`, { method: "DELETE" }),

  listPrograms: () => request<StudyProgram[]>("/api/programs"),
  createProgram: (data: Omit<StudyProgram, "id" | "faculty_name">) =>
    request<StudyProgram>("/api/programs", { method: "POST", body: JSON.stringify(data) }),
  deleteProgram: (id: number) => request<void>(`/api/programs/${id}`, { method: "DELETE" }),

  // Buildings & Rooms
  listBuildings: () => request<Building[]>("/api/buildings"),
  createBuilding: (data: Omit<Building, "id">) =>
    request<Building>("/api/buildings", { method: "POST", body: JSON.stringify(data) }),
  deleteBuilding: (id: number) => request<void>(`/api/buildings/${id}`, { method: "DELETE" }),

  listRooms: () => request<Room[]>("/api/rooms"),
  createRoom: (data: Omit<Room, "id" | "building_code" | "building_name">) =>
    request<Room>("/api/rooms", { method: "POST", body: JSON.stringify(data) }),
  updateRoom: (id: number, data: Partial<Room>) =>
    request<Room>(`/api/rooms/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteRoom: (id: number) => request<void>(`/api/rooms/${id}`, { method: "DELETE" }),

  // Lecturers
  listLecturers: () => request<Lecturer[]>("/api/lecturers"),
  createLecturer: (data: Omit<Lecturer, "id" | "program_name">) =>
    request<Lecturer>("/api/lecturers", { method: "POST", body: JSON.stringify(data) }),
  updateLecturer: (id: number, data: Partial<Lecturer>) =>
    request<Lecturer>(`/api/lecturers/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteLecturer: (id: number) => request<void>(`/api/lecturers/${id}`, { method: "DELETE" }),

  // Classes, Courses, Offerings
  listClasses: (periodId?: number) =>
    request<StudentClass[]>(`/api/classes${buildQuery({ period_id: periodId })}`),
  createClass: (data: Omit<StudentClass, "id" | "program_code" | "program_name">) =>
    request<StudentClass>("/api/classes", { method: "POST", body: JSON.stringify(data) }),
  updateClass: (id: number, data: Partial<StudentClass>) =>
    request<StudentClass>(`/api/classes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteClass: (id: number) => request<void>(`/api/classes/${id}`, { method: "DELETE" }),

  listCourses: (programId?: number) =>
    request<Course[]>(`/api/courses${buildQuery({ program_id: programId })}`),
  createCourse: (data: Omit<Course, "id" | "program_code" | "program_name">) =>
    request<Course>("/api/courses", { method: "POST", body: JSON.stringify(data) }),
  updateCourse: (id: number, data: Partial<Course>) =>
    request<Course>(`/api/courses/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCourse: (id: number) => request<void>(`/api/courses/${id}`, { method: "DELETE" }),

  listOfferings: (periodId?: number) =>
    request<CourseOffering[]>(`/api/offerings${buildQuery({ period_id: periodId })}`),
  createOffering: (data: Record<string, unknown>) =>
    request<CourseOffering>("/api/offerings", { method: "POST", body: JSON.stringify(data) }),
  updateOffering: (id: number, data: Record<string, unknown>) =>
    request<CourseOffering>(`/api/offerings/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteOffering: (id: number) => request<void>(`/api/offerings/${id}`, { method: "DELETE" }),

  // Schedule & Solver
  preflight: (periodId?: number, respectLocked = true) =>
    request<PreflightReport>(
      `/api/schedule/preflight${buildQuery({ period_id: periodId, respect_locked: respectLocked })}`
    ),
  generateSchedule: (payload: {
    period_id?: number;
    preset: "balanced" | "best_fit" | "compact_rooms" | "custom";
    weights?: OptimizationWeights;
    time_limit_seconds: number;
    respect_locked: boolean;
  }) =>
    request<GenerateResponse>("/api/schedule/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startGenerateAsync: (payload: {
    period_id?: number;
    preset: "balanced" | "best_fit" | "compact_rooms" | "custom";
    weights?: OptimizationWeights;
    time_limit_seconds: number;
    respect_locked: boolean;
  }) =>
    request<ScheduleJobStatus>("/api/schedule/generate-async", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getGenerateJob: (jobId: string) =>
    request<ScheduleJobStatus>(`/api/schedule/jobs/${jobId}`),
  generateScheduleWithPolling: async (
    payload: {
      period_id?: number;
      preset: "balanced" | "best_fit" | "compact_rooms" | "custom";
      weights?: OptimizationWeights;
      time_limit_seconds: number;
      respect_locked: boolean;
    },
    onProgress?: (job: ScheduleJobStatus) => void
  ): Promise<GenerateResponse> => {
    const initial = await api.startGenerateAsync(payload);
    onProgress?.(initial);
    while (true) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const job = await api.getGenerateJob(initial.job_id);
      onProgress?.(job);
      if (job.status === "completed" && job.result) {
        return job.result;
      }
      if (job.status === "failed") {
        throw new ApiError(job.error_message || "Generate jadwal gagal.", 409, job);
      }
    }
  },
  listSchedule: (filters?: {
    period_id?: number;
    program_id?: number;
    class_id?: number;
    lecturer_id?: number;
    room_id?: number;
  }) => request<ScheduleEntry[]>(`/api/schedule${buildQuery(filters || {})}`),
  listRuns: (periodId?: number) =>
    request<ScheduleRunSummary[]>(`/api/schedule/runs${buildQuery({ period_id: periodId })}`),
  validateMove: (payload: {
    entry_id: number;
    target_day: string;
    target_start_slot: number;
    target_room_id: number;
  }) =>
    request<MoveValidationResponse>("/api/schedule/validate-move", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  moveEntry: (
    entryId: number,
    payload: {
      target_day: string;
      target_start_slot: number;
      target_room_id: number;
      lock_after_move?: boolean;
    }
  ) =>
    request<ScheduleEntry>(`/api/schedule/entries/${entryId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  toggleLockEntry: (entryId: number) =>
    request<ScheduleEntry>(`/api/schedule/entries/${entryId}/lock`, { method: "POST" }),
  clearSchedule: (periodId?: number, includeLocked = false) =>
    request<void>(
      `/api/schedule${buildQuery({ period_id: periodId, include_locked: includeLocked })}`,
      { method: "DELETE" }
    ),

  // Analytics
  getEfficiency: (periodId?: number) =>
    request<EfficiencySummary>(`/api/analytics/efficiency${buildQuery({ period_id: periodId })}`),

  // Export URLs
  exportUrl: (
    format: "pdf" | "xlsx" | "ics",
    filters?: {
      period_id?: number;
      program_id?: number;
      class_id?: number;
      lecturer_id?: number;
      room_id?: number;
    }
  ) => `${API_BASE}/api/export/${format}${buildQuery(filters || {})}`,
};
