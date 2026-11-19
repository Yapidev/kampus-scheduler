export interface BreakConfig {
  after_slot: number;
  minutes: number;
  label: string;
}

export interface BlockedSlotConfig {
  day: string;
  slot: number;
  reason: string;
}

export interface SlotCoord {
  day: string;
  slot: number;
}

export interface TimeSlotMeta {
  index: number;
  start_time: string;
  end_time: string;
  label: string;
  block_index: number;
  break_after_minutes: number;
  break_after_label?: string | null;
}

export interface AcademicPeriod {
  id: number;
  name: string;
  year: string;
  semester_type: "Ganjil" | "Genap" | "Pendek";
  is_active: boolean;
  status: "draft" | "published";
  days: string[];
  start_time: string;
  slot_minutes: number;
  slots_per_day: number;
  breaks: BreakConfig[];
  blocked_slots: BlockedSlotConfig[];
  shift_rules: Record<string, Record<string, number[]>>;
  created_at: string;
  time_slots: TimeSlotMeta[];
}

export interface Faculty {
  id: number;
  code: string;
  name: string;
}

export interface StudyProgram {
  id: number;
  faculty_id: number;
  code: string;
  name: string;
  degree_level: "D3" | "D4" | "S1" | "S2" | "S3";
  faculty_name?: string | null;
}

export interface Building {
  id: number;
  code: string;
  name: string;
  floor_count: number;
  campus_zone: string;
}

export interface Room {
  id: number;
  building_id: number;
  code: string;
  name: string;
  floor: number;
  capacity: number;
  room_type: string;
  facilities: string[];
  is_active: boolean;
  building_code?: string | null;
  building_name?: string | null;
}

export interface Lecturer {
  id: number;
  nidn: string;
  name: string;
  email?: string | null;
  home_program_id?: number | null;
  max_sks_per_day: number;
  max_days_per_week: number;
  unavailable_slots: SlotCoord[];
  preferred_slots: SlotCoord[];
  program_name?: string | null;
}

export interface StudentClass {
  id: number;
  period_id: number;
  program_id: number;
  code: string;
  semester: number;
  shift: "Reguler" | "Karyawan";
  student_count: number;
  program_code?: string | null;
  program_name?: string | null;
}

export interface Course {
  id: number;
  program_id: number;
  code: string;
  name: string;
  sks: number;
  course_type: "Teori" | "Praktikum" | "Teori+Praktikum";
  required_room_type: string;
  required_facilities: string[];
  program_code?: string | null;
  program_name?: string | null;
}

export interface CourseOffering {
  id: number;
  period_id: number;
  course_id: number;
  class_id: number;
  extra_class_ids: number[];
  lecturer_id: number;
  co_lecturer_id?: number | null;
  sessions_per_week: number;
  session_duration_slots: number;
  student_count_override?: number | null;
  notes?: string | null;
  course_code?: string | null;
  course_name?: string | null;
  sks?: number | null;
  required_room_type?: string | null;
  class_code?: string | null;
  extra_class_codes: string[];
  shift?: string | null;
  effective_student_count: number;
  lecturer_name?: string | null;
  co_lecturer_name?: string | null;
  program_code?: string | null;
}

export interface OptimizationWeights {
  w_seat: number;
  w_gap: number;
  w_pack: number;
  w_building: number;
  w_pref: number;
}

export interface PreflightIssue {
  severity: "error" | "warning";
  category: string;
  message: string;
  entity_ref?: string | null;
}

export interface PreflightReport {
  feasible: boolean;
  total_sessions: number;
  total_required_slots: number;
  total_available_room_slots: number;
  issues: PreflightIssue[];
}

export interface ScheduleEntry {
  id: number;
  period_id: number;
  run_id?: number | null;
  offering_id: number;
  session_index: number;
  room_id: number;
  room_code: string;
  room_name: string;
  room_capacity: number;
  room_type: string;
  building_id: number;
  building_code: string;
  building_name: string;
  day: string;
  start_slot: number;
  duration_slots: number;
  time_range: string;
  is_locked: boolean;
  is_manual_override: boolean;
  course_code: string;
  course_name: string;
  sks: number;
  required_room_type: string;
  class_id: number;
  class_code: string;
  extra_class_ids: number[];
  extra_class_codes: string[];
  shift: string;
  program_id: number;
  program_code: string;
  program_name: string;
  student_count: number;
  seat_fill_pct: number;
  seat_waste: number;
  lecturer_id: number;
  lecturer_name: string;
  co_lecturer_id?: number | null;
  co_lecturer_name?: string | null;
}

export interface RoomEfficiencyMetric {
  room_id: number;
  room_code: string;
  room_name: string;
  building_code: string;
  building_name: string;
  room_type: string;
  capacity: number;
  used_slots: number;
  available_slots: number;
  time_utilization_pct: number;
  avg_seat_fill_pct: number;
  total_seat_waste: number;
  idle_gap_slots: number;
  session_count: number;
  status: "Optimal" | "Underutilized" | "Oversized Match" | "High Load" | "Idle";
}

export interface BuildingUtilization {
  building_id: number;
  building_code: string;
  building_name: string;
  room_count: number;
  used_slots: number;
  available_slots: number;
  time_utilization_pct: number;
  seat_fill_efficiency_pct: number;
}

export interface EfficiencySummary {
  period_id: number;
  period_name: string;
  run_id?: number | null;
  run_status?: string | null;
  preset?: string | null;
  solve_time_ms: number;
  total_sessions: number;
  total_rooms: number;
  active_rooms: number;
  room_time_utilization_pct: number;
  seat_fill_efficiency_pct: number;
  total_seat_waste_slots: number;
  idle_gap_count: number;
  efficiency_score: number;
  rooms: RoomEfficiencyMetric[];
  heatmap: Record<string, Record<number, number>>;
  building_utilization: BuildingUtilization[];
}

export interface ScheduleRunSummary {
  id: number;
  period_id: number;
  status: string;
  preset: string;
  weights_json: OptimizationWeights;
  solve_time_ms: number;
  total_sessions: number;
  room_time_utilization: number;
  seat_fill_efficiency: number;
  idle_gap_count: number;
  efficiency_score: number;
  created_at: string;
}

export interface MoveValidationResponse {
  valid: boolean;
  conflicts: string[];
  warnings: string[];
  projected_seat_fill_pct: number;
  projected_seat_waste: number;
}

export interface GenerateResponse {
  run_id: number;
  status: string;
  preset: string;
  solve_time_ms: number;
  efficiency: EfficiencySummary;
  entries: ScheduleEntry[];
}
