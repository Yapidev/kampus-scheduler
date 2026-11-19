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
        shift_rules={
            k: {dk: list(dv) for dk, dv in v.items()} for k, v in DEFAULT_SHIFT_RULES.items()
        },
    )
    db.add(period)
    db.flush()

    # 8 Faculties
    faculties_data = [
        ("FTI", "Fakultas Teknologi Informasi"),
        ("FEB", "Fakultas Ekonomi & Bisnis"),
        ("FT", "Fakultas Teknik"),
        ("FH", "Fakultas Hukum"),
        ("FISIP", "Fakultas Ilmu Sosial & Ilmu Politik"),
        ("FKIP", "Fakultas Keguruan & Ilmu Pendidikan"),
        ("FPSI", "Fakultas Psikologi"),
        ("FIKES", "Fakultas Ilmu Kesehatan"),
    ]
    fac_map: dict[str, Faculty] = {}
    for code, name in faculties_data:
        f = Faculty(code=code, name=name)
        db.add(f)
        fac_map[code] = f
    db.flush()

    # 14 Study Programs across 8 Faculties
    programs_data = [
        ("FTI", "IF", "Teknik Informatika", "S1"),
        ("FTI", "SI", "Sistem Informasi", "S1"),
        ("FEB", "MN", "Manajemen Bisnis", "S1"),
        ("FEB", "AK", "Akuntansi", "S1"),
        ("FT", "TE", "Teknik Elektro", "S1"),
        ("FT", "TS", "Teknik Sipil", "S1"),
        ("FH", "IH", "Ilmu Hukum", "S1"),
        ("FISIP", "IK", "Ilmu Komunikasi", "S1"),
        ("FISIP", "HI", "Hubungan Internasional", "S1"),
        ("FKIP", "PB", "Pendidikan Bahasa Inggris", "S1"),
        ("FKIP", "PM", "Pendidikan Matematika", "S1"),
        ("FPSI", "PS", "Psikologi", "S1"),
        ("FIKES", "KM", "Kesehatan Masyarakat", "S1"),
        ("FIKES", "GZ", "Ilmu Gizi", "S1"),
    ]
    prog_map: dict[str, StudyProgram] = {}
    for f_code, p_code, p_name, deg in programs_data:
        p = StudyProgram(
            faculty_id=fac_map[f_code].id, code=p_code, name=p_name, degree_level=deg
        )
        db.add(p)
        prog_map[p_code] = p
    db.flush()

    # 4 Buildings
    buildings_data = [
        ("GDA", "Gedung A — Pusat & Humaniora", 4, "Zona Utama"),
        ("GDB", "Gedung B — Laboratorium & Teknik", 4, "Zona Teknik"),
        ("GDC", "Gedung C — Ekonomi, Hukum & Sosial", 4, "Zona Barat"),
        ("GDD", "Gedung D — Kesehatan & Psikologi", 3, "Zona Timur"),
    ]
    bld_map: dict[str, Building] = {}
    for code, name, floors, zone in buildings_data:
        b = Building(code=code, name=name, floor_count=floors, campus_zone=zone)
        db.add(b)
        bld_map[code] = b
    db.flush()

    # 30 Rooms (varied capacities & room types for Best-Fit & Efficiency)
    rooms_spec = [
        ("GDA", "A-101", "Ruang Kuliah A101 (Kecil)", 1, 28, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDA", "A-102", "Ruang Kuliah A102 (Kecil)", 1, 32, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDA", "A-103", "Ruang Kuliah A103 (Sedang)", 1, 36, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDA", "A-201", "Ruang Kuliah A201 (Sedang)", 2, 42, "Teori", ["Proyektor", "AC", "Smart TV"]),
        ("GDA", "A-202", "Ruang Kuliah A202 (Sedang)", 2, 46, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDA", "A-203", "Ruang Kuliah A203 (Besar)", 2, 52, "Teori", ["Proyektor", "AC", "Smart TV"]),
        ("GDA", "A-301", "Ruang Kuliah A301 (Besar)", 3, 64, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDA", "A-302", "Ruang Kuliah A302 (Besar)", 3, 72, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDA", "AULA-1", "Auditorium Utama Kampus", 4, 140, "Aula", ["Proyektor", "AC", "Audio System", "Podium"]),
        ("GDB", "B-101", "Ruang Kuliah B101", 1, 34, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDB", "B-102", "Ruang Kuliah B102", 1, 40, "Teori", ["Proyektor", "AC", "Smart TV"]),
        ("GDB", "B-103", "Ruang Kuliah B103", 1, 48, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDB", "B-201", "Ruang Kuliah B201 (Besar)", 2, 56, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDB", "LAB-KOM1", "Lab Pemrograman 1", 2, 36, "Lab Komputer", ["PC Workstation", "Proyektor", "AC", "LAN"]),
        ("GDB", "LAB-KOM2", "Lab Data & AI", 2, 45, "Lab Komputer", ["PC Workstation", "GPU Server", "Proyektor", "AC"]),
        ("GDB", "LAB-KOM3", "Lab Komputasi & Statistik", 3, 40, "Lab Komputer", ["PC Workstation", "Proyektor", "AC"]),
        ("GDB", "LAB-JAR", "Lab Jaringan & Cloud", 3, 36, "Lab Jaringan", ["Cisco Rack", "PC Workstation", "Proyektor", "AC"]),
        ("GDB", "LAB-BHS", "Lab Bahasa Terpadu", 3, 36, "Lab Bahasa", ["Audio Booth", "Headset", "Proyektor", "AC"]),
        ("GDC", "C-101", "Ruang Kuliah C101", 1, 30, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDC", "C-102", "Ruang Kuliah C102", 1, 38, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDC", "C-103", "Ruang Kuliah C103", 1, 45, "Teori", ["Proyektor", "AC", "Smart TV"]),
        ("GDC", "C-201", "Ruang Kuliah C201", 2, 54, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDC", "C-202", "Ruang Kuliah C202", 2, 60, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDC", "C-301", "Ruang Kuliah C301", 3, 70, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDC", "STUDIO-1", "Studio Penyiaran & Media", 3, 34, "Studio", ["Kamera Broadcast", "Audio Mixer", "Proyektor", "AC"]),
        ("GDD", "D-101", "Ruang Kuliah D101", 1, 30, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDD", "D-102", "Ruang Kuliah D102", 1, 40, "Teori", ["Proyektor", "AC", "Whiteboard"]),
        ("GDD", "D-201", "Ruang Kuliah D201", 2, 50, "Teori", ["Proyektor", "AC", "Smart TV"]),
        ("GDD", "D-202", "Ruang Kuliah D202", 2, 60, "Teori", ["Proyektor", "AC", "Audio System"]),
        ("GDD", "AULA-2", "Auditorium Barat", 3, 120, "Aula", ["Proyektor", "AC", "Audio System", "Podium"]),
    ]
    for b_code, r_code, r_name, fl, cap, r_type, fac in rooms_spec:
        db.add(
            Room(
                building_id=bld_map[b_code].id,
                code=r_code,
                name=r_name,
                floor=fl,
                capacity=cap,
                room_type=r_type,
                facilities=fac,
                is_active=True,
            )
        )
    db.flush()

    # 32 Lecturers across 8 faculties
    lecturers_spec = [
        ("0410018501", "Dr. Ahmad Fauzi, M.Kom.", "IF", 6, 5, [{"day": "Jumat", "slot": 1}, {"day": "Jumat", "slot": 2}], [{"day": "Senin", "slot": 1}]),
        ("0412058802", "Rina Kartika, M.T.", "IF", 6, 5, [{"day": "Rabu", "slot": 8}, {"day": "Rabu", "slot": 9}], []),
        ("0415088203", "Budi Santoso, M.Cs.", "IF", 6, 5, [], []),
        ("0419118904", "Siti Nurhaliza, M.Kom.", "IF", 6, 5, [{"day": "Senin", "slot": 1}, {"day": "Senin", "slot": 2}], []),
        ("0422038605", "Dr. Hendra Wijaya, M.Sc.", "IF", 6, 4, [], []),
        ("0428109110", "Fajar Nugroho, M.Kom.", "IF", 8, 5, [], []),
        ("0408079006", "Dewi Lestari, M.MSI.", "SI", 6, 5, [], []),
        ("0425098707", "Reza Pratama, M.Kom.", "SI", 6, 5, [{"day": "Kamis", "slot": 1}, {"day": "Kamis", "slot": 2}], []),
        ("0407068811", "Laras Putri, M.Si.", "SI", 6, 5, [], []),
        ("0414048408", "Nadia Kusuma, M.B.A.", "MN", 6, 5, [], []),
        ("0403018109", "Dr. Eko Prasetyo, M.M.", "MN", 6, 5, [{"day": "Selasa", "slot": 8}, {"day": "Selasa", "slot": 9}], []),
        ("0418128312", "Prof. Darmawan, Ph.D.", "MN", 6, 4, [{"day": "Jumat", "slot": 7}, {"day": "Jumat", "slot": 8}], []),
        ("0411028713", "Ratna Sari, M.Ak., Ak.", "AK", 6, 5, [], []),
        ("0420068914", "Bagus Prakoso, M.Ak.", "AK", 6, 5, [], []),
        ("0417038515", "Ir. Wahyu Hidayat, M.T.", "TE", 6, 5, [{"day": "Selasa", "slot": 1}], []),
        ("0421078616", "Dimas Aditya, M.Eng.", "TE", 6, 5, [], []),
        ("0409058317", "Dr. Ir. Bambang Susilo, M.T.", "TS", 6, 5, [], []),
        ("0413099018", "Maya Anggraini, M.T.", "TS", 6, 5, [], []),
        ("0405118019", "Prof. Dr. Suryo Utomo, S.H., M.H.", "IH", 6, 4, [{"day": "Senin", "slot": 8}, {"day": "Senin", "slot": 9}], []),
        ("0416088720", "Kartika Dewi, S.H., LL.M.", "IH", 6, 5, [], []),
        ("0424018821", "Andi Wijaya, S.H., M.H.", "IH", 6, 5, [], []),
        ("0419049122", "Putri Maharani, M.I.Kom.", "IK", 6, 5, [], []),
        ("0426058923", "Gilang Ramadhan, M.Sn.", "IK", 6, 5, [{"day": "Kamis", "slot": 8}], []),
        ("0402078424", "Dr. Farah Diba, M.Si.", "HI", 6, 5, [], []),
        ("0423098825", "Rizal Maulana, M.A.", "HI", 6, 5, [], []),
        ("0415128626", "Diana Puspita, M.Pd.", "PB", 6, 5, [], [{"day": "Rabu", "slot": 1}]),
        ("0404038927", "Teguh Santoso, M.Pd.", "PB", 6, 5, [], []),
        ("0412088528", "Dr. Yoga Pratama, M.Pd.", "PM", 6, 5, [], []),
        ("0429018729", "Indah Permatasari, M.Psi.", "PS", 6, 5, [], []),
        ("0406048330", "Dr. Gunawan Wibisono, M.Psi.", "PS", 6, 5, [], []),
        ("0418068631", "dr. Citra Ayu, M.K.M.", "KM", 6, 5, [{"day": "Rabu", "slot": 1}, {"day": "Rabu", "slot": 2}], []),
        ("0427109032", "Novianti Rahma, M.Gz.", "GZ", 6, 5, [], []),
    ]
    lec_map: dict[str, Lecturer] = {}
    for nidn, name, p_code, max_sks, max_days, unavail, pref in lecturers_spec:
        lec = Lecturer(
            nidn=nidn,
            name=name,
            email=f"{nidn}@kampus.ac.id",
            home_program_id=prog_map[p_code].id,
            max_sks_per_day=max_sks,
            max_days_per_week=max_days,
            unavailable_slots=unavail,
            preferred_slots=pref,
        )
        db.add(lec)
        lec_map[nidn] = lec
    db.flush()

    # 25 Classes across 8 Faculties
    classes_spec = [
        ("IF", "IF-1A", 1, "Reguler", 38),
        ("IF", "IF-1B", 1, "Reguler", 41),
        ("IF", "IF-3A", 3, "Reguler", 33),
        ("IF", "IF-5A", 5, "Reguler", 24),
        ("IF", "IF-5K", 5, "Karyawan", 26),
        ("SI", "SI-1A", 1, "Reguler", 34),
        ("SI", "SI-3A", 3, "Reguler", 27),
        ("MN", "MN-1A", 1, "Reguler", 56),
        ("MN", "MN-3A", 3, "Reguler", 44),
        ("MN", "MN-3K", 3, "Karyawan", 25),
        ("AK", "AK-1A", 1, "Reguler", 46),
        ("AK", "AK-3A", 3, "Reguler", 35),
        ("TE", "TE-1A", 1, "Reguler", 36),
        ("TE", "TE-3A", 3, "Reguler", 29),
        ("TS", "TS-1A", 1, "Reguler", 40),
        ("TS", "TS-3A", 3, "Reguler", 31),
        ("IH", "IH-1A", 1, "Reguler", 52),
        ("IH", "IH-3A", 3, "Reguler", 43),
        ("IK", "IK-1A", 1, "Reguler", 32),
        ("HI", "HI-1A", 1, "Reguler", 34),
        ("PB", "PB-1A", 1, "Reguler", 28),
        ("PM", "PM-1A", 1, "Reguler", 30),
        ("PS", "PS-1A", 1, "Reguler", 48),
        ("KM", "KM-1A", 1, "Reguler", 38),
        ("GZ", "GZ-1A", 1, "Reguler", 29),
    ]
    cls_map: dict[str, StudentClass] = {}
    for p_code, c_code, sem, shift, cnt in classes_spec:
        sc = StudentClass(
            period_id=period.id,
            program_id=prog_map[p_code].id,
            code=c_code,
            semester=sem,
            shift=shift,
            student_count=cnt,
        )
        db.add(sc)
        cls_map[c_code] = sc
    db.flush()

    # Courses across 14 study programs (42 courses)
    courses_spec = [
        ("IF", "MKU101", "Pendidikan Pancasila & Kewarganegaraan", 2, "Teori", "Teori", ["Proyektor"]),
        ("IF", "MKU102", "Bahasa Indonesia Akademik", 2, "Teori", "Teori", ["Proyektor"]),
        ("IF", "IF101", "Algoritma & Pemrograman", 3, "Praktikum", "Lab Komputer", ["PC Workstation", "Proyektor"]),
        ("IF", "IF102", "Matematika Diskrit", 3, "Teori", "Teori", ["Proyektor"]),
        ("IF", "IF103", "Organisasi & Arsitektur Komputer", 3, "Teori", "Teori", ["Proyektor"]),
        ("IF", "IF201", "Struktur Data", 3, "Praktikum", "Lab Komputer", ["PC Workstation"]),
        ("IF", "IF202", "Basis Data Lanjut", 3, "Praktikum", "Lab Komputer", ["PC Workstation"]),
        ("IF", "IF203", "Jaringan Komputer", 3, "Praktikum", "Lab Jaringan", ["Cisco Rack", "PC Workstation"]),
        ("IF", "IF301", "Kecerdasan Buatan", 3, "Praktikum", "Lab Komputer", ["PC Workstation"]),
        ("IF", "IF302", "Rekayasa Perangkat Lunak", 3, "Teori", "Teori", ["Proyektor"]),
        ("IF", "IF303", "Komputasi Awan", 2, "Praktikum", "Lab Jaringan", ["PC Workstation"]),
        ("SI", "SI101", "Pengantar Sistem Informasi", 3, "Teori", "Teori", ["Proyektor"]),
        ("SI", "SI102", "Pemodelan Proses Bisnis", 3, "Teori", "Teori", ["Proyektor"]),
        ("SI", "SI201", "Desain & Manajemen Basis Data", 3, "Praktikum", "Lab Komputer", ["PC Workstation"]),
        ("SI", "SI202", "Enterprise Resource Planning", 3, "Teori", "Teori", ["Proyektor"]),
        ("SI", "SI203", "Keamanan Sistem Informasi", 2, "Teori", "Teori", ["Proyektor"]),
        ("MN", "MN101", "Pengantar Manajemen", 3, "Teori", "Teori", ["Proyektor"]),
        ("MN", "MN102", "Ekonomi Mikro", 3, "Teori", "Teori", ["Proyektor"]),
        ("MN", "MN201", "Manajemen Keuangan", 3, "Teori", "Teori", ["Proyektor"]),
        ("MN", "MN202", "Pemasaran Digital", 3, "Teori", "Teori", ["Proyektor"]),
        ("MN", "MN203", "Statistika Bisnis", 2, "Teori", "Teori", ["Proyektor"]),
        ("AK", "AK101", "Pengantar Akuntansi", 3, "Teori", "Teori", ["Proyektor"]),
        ("AK", "AK102", "Hukum Pajak & Bisnis", 3, "Teori", "Teori", ["Proyektor"]),
        ("AK", "AK201", "Komputerisasi Akuntansi", 3, "Praktikum", "Lab Komputer", ["PC Workstation"]),
        ("AK", "AK202", "Auditing I", 3, "Teori", "Teori", ["Proyektor"]),
        ("TE", "TE101", "Rangkaian Listrik", 3, "Teori", "Teori", ["Proyektor"]),
        ("TE", "TE102", "Fisika Teknik", 3, "Teori", "Teori", ["Proyektor"]),
        ("TE", "TE201", "Sistem Telekomunikasi & Jaringan", 3, "Praktikum", "Lab Jaringan", ["Cisco Rack"]),
        ("TS", "TS101", "Mekanika Rekayasa", 3, "Teori", "Teori", ["Proyektor"]),
        ("TS", "TS201", "Struktur Beton Bertulang", 3, "Teori", "Teori", ["Proyektor"]),
        ("IH", "IH101", "Pengantar Ilmu Hukum", 3, "Teori", "Teori", ["Proyektor"]),
        ("IH", "IH102", "Hukum Tata Negara", 3, "Teori", "Teori", ["Proyektor"]),
        ("IH", "IH201", "Hukum Pidana & Acara", 3, "Teori", "Teori", ["Proyektor"]),
        ("IK", "IK101", "Produksi Media & Broadcasting", 3, "Praktikum", "Studio", ["Kamera Broadcast", "Audio Mixer"]),
        ("IK", "IK102", "Jurnalistik Multimedia", 2, "Praktikum", "Studio", ["Proyektor"]),
        ("HI", "HI101", "Pengantar Hubungan Internasional", 3, "Teori", "Teori", ["Proyektor"]),
        ("HI", "HI102", "Komunikasi Diplomatik Inggris", 2, "Praktikum", "Lab Bahasa", ["Audio Booth"]),
        ("PB", "PB101", "Listening & Pronunciation", 3, "Praktikum", "Lab Bahasa", ["Audio Booth", "Headset"]),
        ("PB", "PB102", "English Grammar & Composition", 3, "Teori", "Teori", ["Proyektor"]),
        ("PM", "PM101", "Kalkulus Diferensial", 3, "Teori", "Teori", ["Proyektor"]),
        ("PM", "PM102", "Aljabar Linear Elementer", 3, "Teori", "Teori", ["Proyektor"]),
        ("PS", "PS101", "Psikologi Umum & Perkembangan", 3, "Teori", "Teori", ["Proyektor"]),
        ("PS", "PS102", "Psikodiagnostika Dasar", 3, "Teori", "Teori", ["Proyektor"]),
        ("KM", "KM101", "Dasar Ilmu Kesehatan Masyarakat", 3, "Teori", "Teori", ["Proyektor"]),
        ("KM", "KM102", "Epidemiologi Dasar", 3, "Teori", "Teori", ["Proyektor"]),
        ("GZ", "GZ101", "Ilmu Gizi Dasar", 3, "Teori", "Teori", ["Proyektor"]),
        ("GZ", "GZ102", "Biokimia Pangan & Gizi", 3, "Teori", "Teori", ["Proyektor"]),
    ]
    c_map: dict[str, Course] = {}
    for p_code, c_code, c_name, sks, c_type, r_type, fac in courses_spec:
        crs = Course(
            program_id=prog_map[p_code].id,
            code=c_code,
            name=c_name,
            sks=sks,
            course_type=c_type,
            required_room_type=r_type,
            required_facilities=fac,
        )
        db.add(crs)
        c_map[c_code] = crs
    db.flush()

    # Lecturer NIDNs shorthand
    L = list(lec_map.values())

    def off(
        course_code: str,
        class_code: str,
        lec_nidn: str,
        dur: int | None = None,
        extra_classes: list[str] | None = None,
        co_lec_nidn: str | None = None,
        notes: str | None = None,
    ) -> CourseOffering:
        crs = c_map[course_code]
        return CourseOffering(
            period_id=period.id,
            course_id=crs.id,
            class_id=cls_map[class_code].id,
            extra_class_ids=[cls_map[ec].id for ec in (extra_classes or [])],
            lecturer_id=lec_map[lec_nidn].id,
            co_lecturer_id=lec_map[co_lec_nidn].id if co_lec_nidn else None,
            sessions_per_week=1,
            session_duration_slots=dur if dur is not None else int(crs.sks),
            notes=notes,
        )

    offerings = [
        # --- Merged MKU classes in Aula across faculties ---
        off("MKU101", "IF-1A", L[11].nidn, extra_classes=["IF-1B"], notes="Gabungan FTI (79 mhs)"),
        off("MKU101", "MN-1A", L[10].nidn, extra_classes=["AK-1A"], notes="Gabungan FEB (102 mhs)"),
        off("MKU101", "IH-1A", L[19].nidn, extra_classes=["PS-1A"], notes="Gabungan FH & FPSI (100 mhs)"),
        off("MKU101", "TE-1A", L[17].nidn, extra_classes=["TS-1A"], notes="Gabungan FT (76 mhs)"),
        off("MKU102", "PB-1A", L[26].nidn, extra_classes=["PM-1A"], notes="Gabungan FKIP (58 mhs)"),
        off("MKU102", "KM-1A", L[30].nidn, extra_classes=["GZ-1A"], notes="Gabungan FIKES (67 mhs)"),
        # --- FTI: IF & SI ---
        off("IF101", "IF-1A", L[0].nidn),
        off("IF102", "IF-1A", L[4].nidn),
        off("IF103", "IF-1A", L[2].nidn),
        off("IF101", "IF-1B", L[5].nidn),
        off("IF102", "IF-1B", L[4].nidn),
        off("IF103", "IF-1B", L[2].nidn),
        off("IF201", "IF-3A", L[0].nidn),
        off("IF202", "IF-3A", L[3].nidn),
        off("IF203", "IF-3A", L[1].nidn),
        off("IF302", "IF-3A", L[3].nidn),
        off("IF301", "IF-5A", L[0].nidn, co_lec_nidn=L[4].nidn),
        off("IF302", "IF-5A", L[1].nidn),
        off("IF303", "IF-5A", L[5].nidn),
        off("IF301", "IF-5K", L[5].nidn),
        off("IF302", "IF-5K", L[3].nidn),
        off("IF303", "IF-5K", L[1].nidn),
        off("SI101", "SI-1A", L[6].nidn),
        off("SI102", "SI-1A", L[7].nidn),
        off("MKU101", "SI-1A", L[8].nidn),
        off("SI201", "SI-3A", L[7].nidn),
        off("SI202", "SI-3A", L[6].nidn),
        off("SI203", "SI-3A", L[8].nidn),
        # --- FEB: MN & AK ---
        off("MN101", "MN-1A", L[9].nidn),
        off("MN102", "MN-1A", L[10].nidn),
        off("MN203", "MN-1A", L[11].nidn),
        off("MN201", "MN-3A", L[10].nidn),
        off("MN202", "MN-3A", L[9].nidn),
        off("MN203", "MN-3A", L[11].nidn),
        off("MN201", "MN-3K", L[10].nidn),
        off("MN202", "MN-3K", L[9].nidn),
        off("MN203", "MN-3K", L[12].nidn),
        off("AK101", "AK-1A", L[12].nidn),
        off("AK102", "AK-1A", L[13].nidn),
        off("AK201", "AK-3A", L[13].nidn),
        off("AK202", "AK-3A", L[12].nidn),
        off("MN201", "AK-3A", L[11].nidn),
        # --- FT: TE & TS ---
        off("TE101", "TE-1A", L[14].nidn),
        off("TE102", "TE-1A", L[15].nidn),
        off("TE101", "TE-3A", L[15].nidn),
        off("TE201", "TE-3A", L[14].nidn),
        off("TS101", "TS-1A", L[16].nidn),
        off("TE102", "TS-1A", L[17].nidn),
        off("TS201", "TS-3A", L[16].nidn),
        off("TS101", "TS-3A", L[17].nidn),
        # --- FH: IH ---
        off("IH101", "IH-1A", L[18].nidn),
        off("IH102", "IH-1A", L[19].nidn),
        off("IH201", "IH-3A", L[20].nidn),
        off("IH102", "IH-3A", L[18].nidn),
        off("AK102", "IH-3A", L[20].nidn),
        # --- FISIP: IK & HI ---
        off("IK101", "IK-1A", L[21].nidn),
        off("IK102", "IK-1A", L[22].nidn),
        off("MKU102", "IK-1A", L[21].nidn),
        off("HI101", "HI-1A", L[23].nidn),
        off("HI102", "HI-1A", L[24].nidn),
        off("MKU101", "HI-1A", L[23].nidn),
        # --- FKIP: PB & PM ---
        off("PB101", "PB-1A", L[25].nidn),
        off("PB102", "PB-1A", L[26].nidn),
        off("MKU101", "PB-1A", L[25].nidn),
        off("PM101", "PM-1A", L[27].nidn),
        off("PM102", "PM-1A", L[27].nidn),
        off("IF102", "PM-1A", L[27].nidn),
        # --- FPSI: PS ---
        off("PS101", "PS-1A", L[28].nidn),
        off("PS102", "PS-1A", L[29].nidn),
        off("MN203", "PS-1A", L[28].nidn),
        # --- FIKES: KM & GZ ---
        off("KM101", "KM-1A", L[30].nidn),
        off("KM102", "KM-1A", L[30].nidn),
        off("MKU101", "KM-1A", L[31].nidn),
        off("GZ101", "GZ-1A", L[31].nidn),
        off("GZ102", "GZ-1A", L[31].nidn),
    ]
    db.add_all(offerings)
    db.commit()
    return period
