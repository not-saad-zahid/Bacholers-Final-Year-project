import sqlite3

conn = sqlite3.connect('timetable.db', check_same_thread=False)

def init_datesheet_db():
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS datesheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            class_section_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            shift TEXT NOT NULL,
            semester INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (class_section_id) REFERENCES class_sections (id)
        )
    ''')
    conn.commit()

def save_datesheet(entries):
    if not entries:
        return
    init_datesheet_db()
    with conn:
        for e in entries:
            conn.execute('''
                INSERT INTO datesheet (
                    course_id, teacher_id, room_id, class_section_id,
                    exam_date, start_time, end_time, shift, semester
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                e.get('course_id'),
                e.get('teacher_id'),
                e.get('room_id'),
                e.get('class_section_id'),
                e.get('exam_date', ''),
                e.get('start_time', ''),
                e.get('end_time', ''),
                e.get('shift', ''),
                int(e.get('semester', 0))
            ))
    conn.commit()

def load_datesheet():
    init_datesheet_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT d.id, c.name as course, t.name as teacher, r.name as room, cs.name as section,
               d.exam_date, d.start_time, d.end_time, d.shift, d.semester
        FROM datesheet d
        JOIN courses c ON d.course_id = c.id
        JOIN teachers t ON d.teacher_id = t.id
        JOIN rooms r ON d.room_id = r.id
        JOIN class_sections cs ON d.class_section_id = cs.id
    ''')
    columns = ['id', 'course', 'teacher', 'room', 'section', 'exam_date', 'start_time', 'end_time', 'shift', 'semester']
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def fetch_all_courses():
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM courses')
    return cur.fetchall()

def fetch_all_teachers():
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM teachers')
    return cur.fetchall()

def fetch_all_rooms():
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM rooms')
    return cur.fetchall()

def fetch_all_class_sections():
    cur = conn.cursor()
    cur.execute('SELECT id, name, semester, shift FROM class_sections')
    return cur.fetchall()

def close_db():
    conn.close()