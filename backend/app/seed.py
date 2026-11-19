from sqlalchemy.orm import Session

from app.models import (
    AcademicPeriod,
    Building,
    Course,
    CourseOffering,
    DEFAULT_BLOCKED_SLOTS,
    DEFAULT_BREAKS,
    DEFAULT_DAYS,
    DEFAULT_SHIFT_RULES,
    Faculty,
    Lecturer,
    Room,
    ScheduleEntry,
    ScheduleRun,
    StudentClass,
    StudyProgram,
)


def seed_sample_campus(db: Session, reset: bool = False) -> AcademicPeriod:
    existing = db.query(AcademicPeriod).first()
    if existing and not reset:
        return existing

    if reset:
        db.query(ScheduleEntry).delete()
        db.query(ScheduleRun).delete()
        db.query(CourseOffering).delete()
        db.query(StudentClass).delete()
        db.query(Course).delete()
        db.query(Lecturer).delete()
        db.query(Room).delete()
        db.query(Building).delete()
        db.query(StudyProgram).delete()
        db.query(Faculty).delete()
        db.query(AcademicPeriod).delete()
        db.commit()

    period = AcademicPeriod(
        name="2026/2027 Ganjil",
        year="2026/2027",
        semester_type="Ganjil",
        is_active=True,
        status="draft",
        days=list(DEFAULT_DAYS),
        start_time="08:00",
        slot_minutes=50,
        slots_per_day=9,
        breaks=[dict(b) for b in DEFAULT_BREAKS],
        blocked_slots=[dict(b) for b in DEFAULT_BLOCKED_SLOTS],
        shift_rules={k: {dk: list(dv) for dk, dv in v.items()} for k, v in DEFAULT_SHIFT_RULES.items()},
    )
    db.add(period)
    db.flush()

    # Faculties & Study Programs
    fti = Faculty(code="FTI", name="Fakultas Teknologi Informasi")
    feb = Faculty(code="FEB", name="Fakultas Ekonomi & Bisnis")
    db.add_all([fti, feb])
    db.flush()

    prodi_if = StudyProgram(faculty_id=fti.id, code="IF", name="Teknik Informatika", degree_level="S1")
    prodi_si = StudyProgram(faculty_id=fti.id, code="SI", name="Sistem Informasi", degree_level="S1")
    prodi_mn = StudyProgram(faculty_id=feb.id, code="MN", name="Manajemen Bisnis", degree_level="S1")
    db.add_all([prodi_if, prodi_si, prodi_mn])
    db.flush()

    # Buildings & Rooms (diverse capacities to demonstrate Best-Fit efficiency!)
    gd_a = Building(code="GDA", name="Gedung A — Akademik Pusat", floor_count=4, campus_zone="Zona Utama")
    gd_b = Building(code="GDB", name="Gedung B — Laboratorium & Teknik", floor_count=3, campus_zone="Zona Teknik")
    db.add_all([gd_a, gd_b])
    db.flush()

    rooms = [
        # Gedung A: Teori beragam ukuran + Aula
        Room(building_id=gd_a.id, code="A-101", name="Ruang Kuliah A101 (Kecil)", floor=1, capacity=28, room_type="Teori", facilities=["Proyektor", "AC", "Whiteboard"]),
        Room(building_id=gd_a.id, code="A-102", name="Ruang Kuliah A102 (Kecil)", floor=1, capacity=30, room_type="Teori", facilities=["Proyektor", "AC", "Whiteboard"]),
        Room(building_id=gd_a.id, code="A-201", name="Ruang Kuliah A201 (Sedang)", floor=2, capacity=42, room_type="Teori", facilities=["Proyektor", "AC", "Smart TV"]),
        Room(building_id=gd_a.id, code="A-202", name="Ruang Kuliah A202 (Sedang)", floor=2, capacity=45, room_type="Teori", facilities=["Proyektor", "AC", "Whiteboard"]),
        Room(building_id=gd_a.id, code="A-301", name="Ruang Kuliah A301 (Besar)", floor=3, capacity=65, room_type="Teori", facilities=["Proyektor", "AC", "Audio System"]),
        Room(building_id=gd_a.id, code="A-302", name="Ruang Kuliah A302 (Besar)", floor=3, capacity=70, room_type="Teori", facilities=["Proyektor", "AC", "Audio System"]),
        Room(building_id=gd_a.id, code="AULA-1", name="Auditorium Kampus", floor=4, capacity=120, room_type="Aula", facilities=["Proyektor", "AC", "Audio System", "Podium"]),
        # Gedung B: Lab & Teori Teknik
        Room(building_id=gd_b.id, code="B-101", name="Ruang Kuliah B101", floor=1, capacity=36, room_type="Teori", facilities=["Proyektor", "AC", "Whiteboard"]),
        Room(building_id=gd_b.id, code="B-102", name="Ruang Kuliah B102", floor=1, capacity=40, room_type="Teori", facilities=["Proyektor", "AC", "Smart TV"]),
        Room(building_id=gd_b.id, code="LAB-KOM1", name="Lab Pemrograman 1", floor=2, capacity=35, room_type="Lab Komputer", facilities=["PC Workstation", "Proyektor", "AC", "LAN"]),
        Room(building_id=gd_b.id, code="LAB-KOM2", name="Lab Data & AI", floor=2, capacity=45, room_type="Lab Komputer", facilities=["PC Workstation", "GPU Server", "Proyektor", "AC"]),
        Room(building_id=gd_b.id, code="LAB-JAR", name="Lab Jaringan & Cloud", floor=3, capacity=34, room_type="Lab Jaringan", facilities=["Cisco Rack", "PC Workstation", "Proyektor", "AC"]),
    ]
    db.add_all(rooms)
    db.flush()

    # Lecturers
    lecturers = [
        Lecturer(nidn="0410018501", name="Dr. Ahmad Fauzi, M.Kom.", email="ahmad.fauzi@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Jumat", "slot": 1}, {"day": "Jumat", "slot": 2}], preferred_slots=[{"day": "Senin", "slot": 1}, {"day": "Senin", "slot": 2}]),
        Lecturer(nidn="0412058802", name="Rina Kartika, M.T.", email="rina.kartika@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Rabu", "slot": 8}, {"day": "Rabu", "slot": 9}], preferred_slots=[]),
        Lecturer(nidn="0415088203", name="Budi Santoso, M.Cs.", email="budi.santoso@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0419118904", name="Siti Nurhaliza, M.Kom.", email="siti.nur@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Senin", "slot": 1}, {"day": "Senin", "slot": 2}], preferred_slots=[]),
        Lecturer(nidn="0422038605", name="Dr. Hendra Wijaya, M.Sc.", email="hendra.w@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=6, max_days_per_week=4, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0408079006", name="Dewi Lestari, M.MSI.", email="dewi.lestari@kampus.ac.id", home_program_id=prodi_si.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0425098707", name="Reza Pratama, M.Kom.", email="reza.pratama@kampus.ac.id", home_program_id=prodi_si.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Kamis", "slot": 1}, {"day": "Kamis", "slot": 2}], preferred_slots=[]),
        Lecturer(nidn="0414048408", name="Nadia Kusuma, M.B.A.", email="nadia.kusuma@kampus.ac.id", home_program_id=prodi_mn.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0403018109", name="Dr. Eko Prasetyo, M.M.", email="eko.prasetyo@kampus.ac.id", home_program_id=prodi_mn.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Selasa", "slot": 8}, {"day": "Selasa", "slot": 9}], preferred_slots=[]),
        Lecturer(nidn="0428109110", name="Fajar Nugroho, M.Kom.", email="fajar.n@kampus.ac.id", home_program_id=prodi_if.id, max_sks_per_day=8, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0407068811", name="Laras Putri, M.Si.", email="laras.putri@kampus.ac.id", home_program_id=prodi_si.id, max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]),
        Lecturer(nidn="0418128312", name="Prof. Darmawan, Ph.D.", email="darmawan@kampus.ac.id", home_program_id=prodi_mn.id, max_sks_per_day=6, max_days_per_week=4, unavailable_slots=[{"day": "Jumat", "slot": 7}, {"day": "Jumat", "slot": 8}], preferred_slots=[]),
    ]
    db.add_all(lecturers)
    db.flush()

    # Classes (varied student counts: 22, 26, 33, 38, 42, 54 to test best-fit room efficiency!)
    cls_if1a = StudentClass(period_id=period.id, program_id=prodi_if.id, code="IF-1A", semester=1, shift="Reguler", student_count=38)
    cls_if1b = StudentClass(period_id=period.id, program_id=prodi_if.id, code="IF-1B", semester=1, shift="Reguler", student_count=41)
    cls_if3a = StudentClass(period_id=period.id, program_id=prodi_if.id, code="IF-3A", semester=3, shift="Reguler", student_count=33)
    cls_if5a = StudentClass(period_id=period.id, program_id=prodi_if.id, code="IF-5A", semester=5, shift="Reguler", student_count=24)
    cls_if5k = StudentClass(period_id=period.id, program_id=prodi_if.id, code="IF-5K", semester=5, shift="Karyawan", student_count=26)
    cls_si1a = StudentClass(period_id=period.id, program_id=prodi_si.id, code="SI-1A", semester=1, shift="Reguler", student_count=34)
    cls_si3a = StudentClass(period_id=period.id, program_id=prodi_si.id, code="SI-3A", semester=3, shift="Reguler", student_count=27)
    cls_mn1a = StudentClass(period_id=period.id, program_id=prodi_mn.id, code="MN-1A", semester=1, shift="Reguler", student_count=56)
    cls_mn3a = StudentClass(period_id=period.id, program_id=prodi_mn.id, code="MN-3A", semester=3, shift="Reguler", student_count=44)
    cls_mn3k = StudentClass(period_id=period.id, program_id=prodi_mn.id, code="MN-3K", semester=3, shift="Karyawan", student_count=25)
    classes = [cls_if1a, cls_if1b, cls_if3a, cls_if5a, cls_if5k, cls_si1a, cls_si3a, cls_mn1a, cls_mn3a, cls_mn3k]
    db.add_all(classes)
    db.flush()

    # Courses
    courses = [
        Course(program_id=prodi_if.id, code="MKU101", name="Pendidikan Pancasila & Kewarganegaraan", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_if.id, code="IF101", name="Algoritma & Pemrograman", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation", "Proyektor"]),
        Course(program_id=prodi_if.id, code="IF102", name="Matematika Diskrit", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_if.id, code="IF103", name="Organisasi & Arsitektur Komputer", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_if.id, code="IF201", name="Struktur Data", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation"]),
        Course(program_id=prodi_if.id, code="IF202", name="Basis Data Lanjut", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation"]),
        Course(program_id=prodi_if.id, code="IF203", name="Jaringan Komputer", sks=3, course_type="Praktikum", required_room_type="Lab Jaringan", required_facilities=["Cisco Rack", "PC Workstation"]),
        Course(program_id=prodi_if.id, code="IF301", name="Kecerdasan Buatan", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation"]),
        Course(program_id=prodi_if.id, code="IF302", name="Rekayasa Perangkat Lunak", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_if.id, code="IF303", name="Komputasi Awan", sks=2, course_type="Praktikum", required_room_type="Lab Jaringan", required_facilities=["PC Workstation"]),
        Course(program_id=prodi_si.id, code="SI101", name="Pengantar Sistem Informasi", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_si.id, code="SI102", name="Pemodelan Proses Bisnis", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_si.id, code="SI201", name="Desain & Manajemen Basis Data", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation"]),
        Course(program_id=prodi_si.id, code="SI202", name="Enterprise Resource Planning", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_si.id, code="SI203", name="Keamanan Sistem Informasi", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN101", name="Pengantar Manajemen", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN102", name="Ekonomi Mikro", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN103", name="Akuntansi Dasar", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN201", name="Manajemen Keuangan", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN202", name="Pemasaran Digital", sks=3, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
        Course(program_id=prodi_mn.id, code="MN203", name="Statistika Bisnis", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]),
    ]
    db.add_all(courses)
    db.flush()
    c_map = {c.code: c for c in courses}
    l0, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11 = lecturers

    offerings = [
        # Merged general lecture in Aula (IF-1A + IF-1B = 79 students!)
        CourseOffering(period_id=period.id, course_id=c_map["MKU101"].id, class_id=cls_if1a.id, extra_class_ids=[cls_if1b.id], lecturer_id=l11.id, sessions_per_week=1, session_duration_slots=2, notes="Kuliah gabungan MKU IF-1A & IF-1B"),
        # IF-1A (38 students)
        CourseOffering(period_id=period.id, course_id=c_map["IF101"].id, class_id=cls_if1a.id, lecturer_id=l0.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF102"].id, class_id=cls_if1a.id, lecturer_id=l4.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF103"].id, class_id=cls_if1a.id, lecturer_id=l2.id, sessions_per_week=1, session_duration_slots=3),
        # IF-1B (41 students)
        CourseOffering(period_id=period.id, course_id=c_map["IF101"].id, class_id=cls_if1b.id, lecturer_id=l9.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF102"].id, class_id=cls_if1b.id, lecturer_id=l4.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF103"].id, class_id=cls_if1b.id, lecturer_id=l2.id, sessions_per_week=1, session_duration_slots=3),
        # IF-3A (33 students)
        CourseOffering(period_id=period.id, course_id=c_map["IF201"].id, class_id=cls_if3a.id, lecturer_id=l0.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF202"].id, class_id=cls_if3a.id, lecturer_id=l3.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF203"].id, class_id=cls_if3a.id, lecturer_id=l1.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF302"].id, class_id=cls_if3a.id, lecturer_id=l3.id, sessions_per_week=1, session_duration_slots=3),
        # IF-5A (24 students -> should best-fit small rooms A-101/A-102 or LAB-KOM1/LAB-JAR!)
        CourseOffering(period_id=period.id, course_id=c_map["IF301"].id, class_id=cls_if5a.id, lecturer_id=l0.id, co_lecturer_id=l4.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF302"].id, class_id=cls_if5a.id, lecturer_id=l1.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF303"].id, class_id=cls_if5a.id, lecturer_id=l9.id, sessions_per_week=1, session_duration_slots=2),
        # IF-5K (Karyawan, 26 students)
        CourseOffering(period_id=period.id, course_id=c_map["IF301"].id, class_id=cls_if5k.id, lecturer_id=l9.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF302"].id, class_id=cls_if5k.id, lecturer_id=l3.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["IF303"].id, class_id=cls_if5k.id, lecturer_id=l1.id, sessions_per_week=1, session_duration_slots=2),
        # SI-1A (34 students)
        CourseOffering(period_id=period.id, course_id=c_map["SI101"].id, class_id=cls_si1a.id, lecturer_id=l5.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["SI102"].id, class_id=cls_si1a.id, lecturer_id=l6.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MKU101"].id, class_id=cls_si1a.id, lecturer_id=l11.id, sessions_per_week=1, session_duration_slots=2),
        # SI-3A (27 students)
        CourseOffering(period_id=period.id, course_id=c_map["SI201"].id, class_id=cls_si3a.id, lecturer_id=l6.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["SI202"].id, class_id=cls_si3a.id, lecturer_id=l5.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["SI203"].id, class_id=cls_si3a.id, lecturer_id=l10.id, sessions_per_week=1, session_duration_slots=2),
        # MN-1A (56 students -> should choose large rooms A-301/A-302)
        CourseOffering(period_id=period.id, course_id=c_map["MN101"].id, class_id=cls_mn1a.id, lecturer_id=l7.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN102"].id, class_id=cls_mn1a.id, lecturer_id=l8.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN103"].id, class_id=cls_mn1a.id, lecturer_id=l11.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MKU101"].id, class_id=cls_mn1a.id, lecturer_id=l10.id, sessions_per_week=1, session_duration_slots=2),
        # MN-3A (44 students)
        CourseOffering(period_id=period.id, course_id=c_map["MN201"].id, class_id=cls_mn3a.id, lecturer_id=l8.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN202"].id, class_id=cls_mn3a.id, lecturer_id=l7.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN203"].id, class_id=cls_mn3a.id, lecturer_id=l10.id, sessions_per_week=1, session_duration_slots=2),
        # MN-3K (Karyawan, 25 students)
        CourseOffering(period_id=period.id, course_id=c_map["MN201"].id, class_id=cls_mn3k.id, lecturer_id=l8.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN202"].id, class_id=cls_mn3k.id, lecturer_id=l7.id, sessions_per_week=1, session_duration_slots=3),
        CourseOffering(period_id=period.id, course_id=c_map["MN203"].id, class_id=cls_mn3k.id, lecturer_id=l10.id, sessions_per_week=1, session_duration_slots=2),
    ]
    db.add_all(offerings)
    db.commit()
    return period
