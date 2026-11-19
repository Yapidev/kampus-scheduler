from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Building,
    Course,
    CourseOffering,
    Faculty,
    Lecturer,
    Room,
    StudentClass,
    StudyProgram,
)
from app.schemas import (
    BuildingCreate,
    BuildingOut,
    CourseCreate,
    CourseOfferingCreate,
    CourseOfferingOut,
    CourseOfferingUpdate,
    CourseOut,
    CourseUpdate,
    FacultyCreate,
    FacultyOut,
    LecturerCreate,
    LecturerOut,
    LecturerUpdate,
    RoomCreate,
    RoomOut,
    RoomUpdate,
    StudentClassCreate,
    StudentClassOut,
    StudentClassUpdate,
    StudyProgramCreate,
    StudyProgramOut,
)


router = APIRouter(prefix="/api", tags=["Master Data"])


def _commit_or_409(db: Session, err_msg: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=err_msg)


# --- Faculties ---
@router.get("/faculties", response_model=list[FacultyOut])
def list_faculties(db: Session = Depends(get_db)):
    return db.query(Faculty).order_by(Faculty.code).all()


@router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(payload: FacultyCreate, db: Session = Depends(get_db)):
    row = Faculty(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Kode fakultas sudah digunakan.")
    db.refresh(row)
    return row


@router.put("/faculties/{faculty_id}", response_model=FacultyOut)
def update_faculty(faculty_id: int, payload: FacultyCreate, db: Session = Depends(get_db)):
    row = db.get(Faculty, faculty_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan.")
    row.code = payload.code
    row.name = payload.name
    _commit_or_409(db, "Kode fakultas sudah digunakan.")
    db.refresh(row)
    return row


@router.delete("/faculties/{faculty_id}", status_code=204)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    row = db.get(Faculty, faculty_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Study Programs ---
@router.get("/programs", response_model=list[StudyProgramOut])
def list_programs(db: Session = Depends(get_db)):
    facs = {f.id: f.name for f in db.query(Faculty).all()}
    rows = db.query(StudyProgram).order_by(StudyProgram.code).all()
    out = []
    for r in rows:
        item = StudyProgramOut.model_validate(r)
        item.faculty_name = facs.get(r.faculty_id)
        out.append(item)
    return out


@router.post("/programs", response_model=StudyProgramOut, status_code=201)
def create_program(payload: StudyProgramCreate, db: Session = Depends(get_db)):
    fac = db.get(Faculty, payload.faculty_id)
    if not fac:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan.")
    row = StudyProgram(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Kode program studi sudah digunakan.")
    db.refresh(row)
    out = StudyProgramOut.model_validate(row)
    out.faculty_name = fac.name
    return out


@router.put("/programs/{program_id}", response_model=StudyProgramOut)
def update_program(program_id: int, payload: StudyProgramCreate, db: Session = Depends(get_db)):
    row = db.get(StudyProgram, program_id)
    if not row:
        raise HTTPException(status_code=404, detail="Program studi tidak ditemukan.")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    _commit_or_409(db, "Kode program studi sudah digunakan atau fakultas invalid.")
    db.refresh(row)
    fac = db.get(Faculty, row.faculty_id)
    out = StudyProgramOut.model_validate(row)
    out.faculty_name = fac.name if fac else None
    return out


@router.delete("/programs/{program_id}", status_code=204)
def delete_program(program_id: int, db: Session = Depends(get_db)):
    row = db.get(StudyProgram, program_id)
    if not row:
        raise HTTPException(status_code=404, detail="Program studi tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Buildings ---
@router.get("/buildings", response_model=list[BuildingOut])
def list_buildings(db: Session = Depends(get_db)):
    return db.query(Building).order_by(Building.code).all()


@router.post("/buildings", response_model=BuildingOut, status_code=201)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db)):
    row = Building(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Kode gedung sudah digunakan.")
    db.refresh(row)
    return row


@router.put("/buildings/{building_id}", response_model=BuildingOut)
def update_building(building_id: int, payload: BuildingCreate, db: Session = Depends(get_db)):
    row = db.get(Building, building_id)
    if not row:
        raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    _commit_or_409(db, "Kode gedung sudah digunakan.")
    db.refresh(row)
    return row


@router.delete("/buildings/{building_id}", status_code=204)
def delete_building(building_id: int, db: Session = Depends(get_db)):
    row = db.get(Building, building_id)
    if not row:
        raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Rooms ---
@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    blds = {b.id: b for b in db.query(Building).all()}
    rows = db.query(Room).order_by(Room.code).all()
    out = []
    for r in rows:
        item = RoomOut.model_validate(r)
        b = blds.get(r.building_id)
        item.building_code = b.code if b else None
        item.building_name = b.name if b else None
        out.append(item)
    return out


@router.post("/rooms", response_model=RoomOut, status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    bld = db.get(Building, payload.building_id)
    if not bld:
        raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
    row = Room(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Kode ruangan sudah digunakan.")
    db.refresh(row)
    out = RoomOut.model_validate(row)
    out.building_code = bld.code
    out.building_name = bld.name
    return out


@router.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db)):
    row = db.get(Room, room_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ruangan tidak ditemukan.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    _commit_or_409(db, "Gagal memperbarui ruangan (kode duplikat atau gedung invalid).")
    db.refresh(row)
    bld = db.get(Building, row.building_id)
    out = RoomOut.model_validate(row)
    out.building_code = bld.code if bld else None
    out.building_name = bld.name if bld else None
    return out


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    row = db.get(Room, room_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ruangan tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Lecturers ---
@router.get("/lecturers", response_model=list[LecturerOut])
def list_lecturers(db: Session = Depends(get_db)):
    progs = {p.id: p.name for p in db.query(StudyProgram).all()}
    rows = db.query(Lecturer).order_by(Lecturer.name).all()
    out = []
    for r in rows:
        item = LecturerOut.model_validate(r)
        item.program_name = progs.get(r.home_program_id) if r.home_program_id else None
        out.append(item)
    return out


@router.post("/lecturers", response_model=LecturerOut, status_code=201)
def create_lecturer(payload: LecturerCreate, db: Session = Depends(get_db)):
    row = Lecturer(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "NIDN dosen sudah terdaftar.")
    db.refresh(row)
    out = LecturerOut.model_validate(row)
    if row.home_program_id:
        p = db.get(StudyProgram, row.home_program_id)
        out.program_name = p.name if p else None
    return out


@router.put("/lecturers/{lecturer_id}", response_model=LecturerOut)
def update_lecturer(lecturer_id: int, payload: LecturerUpdate, db: Session = Depends(get_db)):
    row = db.get(Lecturer, lecturer_id)
    if not row:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    _commit_or_409(db, "NIDN dosen sudah digunakan.")
    db.refresh(row)
    out = LecturerOut.model_validate(row)
    if row.home_program_id:
        p = db.get(StudyProgram, row.home_program_id)
        out.program_name = p.name if p else None
    return out


@router.delete("/lecturers/{lecturer_id}", status_code=204)
def delete_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    row = db.get(Lecturer, lecturer_id)
    if not row:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Student Classes ---
@router.get("/classes", response_model=list[StudentClassOut])
def list_classes(period_id: int | None = None, db: Session = Depends(get_db)):
    progs = {p.id: p for p in db.query(StudyProgram).all()}
    q = db.query(StudentClass)
    if period_id is not None:
        q = q.filter(StudentClass.period_id == period_id)
    rows = q.order_by(StudentClass.code).all()
    out = []
    for r in rows:
        item = StudentClassOut.model_validate(r)
        p = progs.get(r.program_id)
        item.program_code = p.code if p else None
        item.program_name = p.name if p else None
        out.append(item)
    return out


@router.post("/classes", response_model=StudentClassOut, status_code=201)
def create_class(payload: StudentClassCreate, db: Session = Depends(get_db)):
    row = StudentClass(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Gagal membuat kelas (periksa periode/prodi).")
    db.refresh(row)
    p = db.get(StudyProgram, row.program_id)
    out = StudentClassOut.model_validate(row)
    out.program_code = p.code if p else None
    out.program_name = p.name if p else None
    return out


@router.put("/classes/{class_id}", response_model=StudentClassOut)
def update_class(class_id: int, payload: StudentClassUpdate, db: Session = Depends(get_db)):
    row = db.get(StudentClass, class_id)
    if not row:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    _commit_or_409(db, "Gagal memperbarui kelas.")
    db.refresh(row)
    p = db.get(StudyProgram, row.program_id)
    out = StudentClassOut.model_validate(row)
    out.program_code = p.code if p else None
    out.program_name = p.name if p else None
    return out


@router.delete("/classes/{class_id}", status_code=204)
def delete_class(class_id: int, db: Session = Depends(get_db)):
    row = db.get(StudentClass, class_id)
    if not row:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Courses ---
@router.get("/courses", response_model=list[CourseOut])
def list_courses(program_id: int | None = None, db: Session = Depends(get_db)):
    progs = {p.id: p for p in db.query(StudyProgram).all()}
    q = db.query(Course)
    if program_id is not None:
        q = q.filter(Course.program_id == program_id)
    rows = q.order_by(Course.code).all()
    out = []
    for r in rows:
        item = CourseOut.model_validate(r)
        p = progs.get(r.program_id)
        item.program_code = p.code if p else None
        item.program_name = p.name if p else None
        out.append(item)
    return out


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    row = Course(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Kode mata kuliah sudah digunakan.")
    db.refresh(row)
    p = db.get(StudyProgram, row.program_id)
    out = CourseOut.model_validate(row)
    out.program_code = p.code if p else None
    out.program_name = p.name if p else None
    return out


@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    row = db.get(Course, course_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mata kuliah tidak ditemukan.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    _commit_or_409(db, "Kode mata kuliah sudah digunakan.")
    db.refresh(row)
    p = db.get(StudyProgram, row.program_id)
    out = CourseOut.model_validate(row)
    out.program_code = p.code if p else None
    out.program_name = p.name if p else None
    return out


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    row = db.get(Course, course_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mata kuliah tidak ditemukan.")
    db.delete(row)
    db.commit()


# --- Course Offerings ---
def _enrich_offering(
    r: CourseOffering,
    courses: dict[int, Course],
    classes: dict[int, StudentClass],
    lecturers: dict[int, Lecturer],
    progs: dict[int, StudyProgram],
) -> CourseOfferingOut:
    item = CourseOfferingOut.model_validate(r)
    c = courses.get(r.course_id)
    cls = classes.get(r.class_id)
    lec = lecturers.get(r.lecturer_id)
    co_lec = lecturers.get(r.co_lecturer_id) if r.co_lecturer_id else None
    extra_cls = [classes[cid] for cid in (r.extra_class_ids or []) if cid in classes and cid != r.class_id]

    if c:
        item.course_code = c.code
        item.course_name = c.name
        item.sks = c.sks
        item.required_room_type = c.required_room_type
    if cls:
        item.class_code = cls.code
        item.shift = cls.shift
        p = progs.get(cls.program_id)
        item.program_code = p.code if p else None
    item.extra_class_codes = [ec.code for ec in extra_cls]
    item.effective_student_count = (
        int(r.student_count_override)
        if r.student_count_override is not None
        else ((cls.student_count if cls else 0) + sum(ec.student_count for ec in extra_cls))
    )
    if lec:
        item.lecturer_name = lec.name
    if co_lec:
        item.co_lecturer_name = co_lec.name
    return item


@router.get("/offerings", response_model=list[CourseOfferingOut])
def list_offerings(period_id: int | None = None, db: Session = Depends(get_db)):
    courses = {c.id: c for c in db.query(Course).all()}
    classes = {c.id: c for c in db.query(StudentClass).all()}
    lecturers = {l.id: l for l in db.query(Lecturer).all()}
    progs = {p.id: p for p in db.query(StudyProgram).all()}

    q = db.query(CourseOffering)
    if period_id is not None:
        q = q.filter(CourseOffering.period_id == period_id)
    rows = q.order_by(CourseOffering.id).all()
    return [_enrich_offering(r, courses, classes, lecturers, progs) for r in rows]


@router.post("/offerings", response_model=CourseOfferingOut, status_code=201)
def create_offering(payload: CourseOfferingCreate, db: Session = Depends(get_db)):
    row = CourseOffering(**payload.model_dump())
    db.add(row)
    _commit_or_409(db, "Gagal membuat penawaran mata kuliah (periksa relasi data).")
    db.refresh(row)
    courses = {c.id: c for c in db.query(Course).all()}
    classes = {c.id: c for c in db.query(StudentClass).all()}
    lecturers = {l.id: l for l in db.query(Lecturer).all()}
    progs = {p.id: p for p in db.query(StudyProgram).all()}
    return _enrich_offering(row, courses, classes, lecturers, progs)


@router.put("/offerings/{offering_id}", response_model=CourseOfferingOut)
def update_offering(
    offering_id: int, payload: CourseOfferingUpdate, db: Session = Depends(get_db)
):
    row = db.get(CourseOffering, offering_id)
    if not row:
        raise HTTPException(status_code=404, detail="Penawaran mata kuliah tidak ditemukan.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    _commit_or_409(db, "Gagal memperbarui penawaran mata kuliah.")
    db.refresh(row)
    courses = {c.id: c for c in db.query(Course).all()}
    classes = {c.id: c for c in db.query(StudentClass).all()}
    lecturers = {l.id: l for l in db.query(Lecturer).all()}
    progs = {p.id: p for p in db.query(StudyProgram).all()}
    return _enrich_offering(row, courses, classes, lecturers, progs)


@router.delete("/offerings/{offering_id}", status_code=204)
def delete_offering(offering_id: int, db: Session = Depends(get_db)):
    row = db.get(CourseOffering, offering_id)
    if not row:
        raise HTTPException(status_code=404, detail="Penawaran mata kuliah tidak ditemukan.")
    db.delete(row)
    db.commit()
