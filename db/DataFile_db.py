import tkinter.messagebox as messagebox
import sqlite3
import os

os.chdir(os.path.dirname(__file__))
db_path = os.path.join(os.path.dirname(__file__), 'DataFile.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.execute('PRAGMA foreign_keys = ON')


# Global variable to track the current master module
current_master_module = None

def current_master():
    """Returns the name of the current master module ("Timetable", "Datesheet", or None)."""
    global current_master_module
    return current_master_module

def set_current_master(module_name):
    """Sets the current master module and prints debug info."""
    global current_master_module
    if module_name in ["Timetable", "Datesheet"]:
        current_master_module = module_name
        print(f"[DEBUG] Current master module set to: {current_master_module}")
    else:
        current_master_module = None
        print(f"[DEBUG] Invalid module name provided. Master module set to None.")



def init_timetable_db():
    c = conn.cursor()
    
    # Timetable table
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            class_section_id INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            shift TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (class_section_id) REFERENCES class_sections (id)
        )
    ''')

    # Datesheet table (only stores semester, dates, and times)
    c.execute('''
        CREATE TABLE IF NOT EXISTS datesheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester INTEGER NOT NULL,
            exam_start_date TEXT NOT NULL,
            exam_end_date TEXT NOT NULL,
            exam_start_time TEXT NOT NULL,
            exam_end_time TEXT NOT NULL
        )
    ''')

    # Teachers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Courses table (shared, can be filled from either UI, but only one at a time)
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')

    # Rooms table (shared, can be filled from either UI, but only one at a time)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name INTEGER NOT NULL UNIQUE
        )
    ''')

    # Class sections table (shared, can be filled from either UI, but only one at a time)
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester INTEGER NOT NULL,
            shift TEXT NOT NULL,
            UNIQUE(name, semester, shift)
        )
    ''')

    # Remove duplicate rows in the timetable table
    c.execute('''
        DELETE FROM timetable
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM timetable
            GROUP BY teacher_id, course_id, room_id, class_section_id, semester, shift
        )
    ''')

    conn.commit()
    return conn

def fetch_id_from_name(table, name, **kwargs):
    """
    Fetch the ID of a record from the database by name.
    If the record does not exist, insert it and return the new ID.
    """
    try:
        # Validate the name for rooms (must be a valid integer)
        if table == "rooms":
            try:
                name = int(name)
                if name <= 0:
                    raise ValueError
            except ValueError:
                print(f"Invalid room name: {name}. Room name must be a positive integer.")
                return None

        query = f"SELECT id FROM {table} WHERE name = ?"
        params = [name]

        if table == "class_sections" and "semester" in kwargs and "shift" in kwargs:
            query += " AND semester = ? AND shift = ?"
            params.extend([kwargs["semester"], kwargs["shift"]])

        cur = conn.cursor()
        cur.execute(query, tuple(params))
        result = cur.fetchone()
        if result:
            return result[0]

        # Insert the record if it does not exist
        if table == "courses" and "teacher_id" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, teacher_id) VALUES (?, ?)", (name, kwargs["teacher_id"]))
        elif table == "class_sections" and "semester" in kwargs and "shift" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, semester, shift) VALUES (?, ?, ?)", (name, kwargs["semester"], kwargs["shift"]))
        elif table == "rooms":
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
        else:
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))

        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch or create ID in {table}: {e}")
        return None

def load_timetable(semester=None, shift=None, teacher=None, course=None, room=None, class_section=None):
    """
    Load timetable entries from the database, filtered by the provided criteria.
    Returns a list of dictionaries with IDs and human-readable names for use in the application.
    """
    init_timetable_db()
    cur = conn.cursor()
    query = '''
        SELECT 
            t.id AS entry_id,
            t.teacher_id,
            teachers.name AS teacher_name, 
            t.course_id,
            courses.name AS course_name, 
            t.room_id,
            rooms.name AS room_name, 
            t.class_section_id,
            class_sections.name AS class_section_name, 
            t.semester, 
            t.shift
        FROM timetable t
        JOIN teachers ON t.teacher_id = teachers.id
        JOIN courses ON t.course_id = courses.id
        JOIN rooms ON t.room_id = rooms.id
        JOIN class_sections ON t.class_section_id = class_sections.id
    '''
    conditions = []
    params = []
    if semester is not None:
        conditions.append('t.semester = ?')
        params.append(semester)
    if shift is not None:
        conditions.append('t.shift = ?')
        params.append(shift)
    if teacher is not None:
        conditions.append('teachers.name = ?')
        params.append(teacher)
    if course is not None:
        conditions.append('courses.name = ?')
        params.append(course)
    if room is not None:
        conditions.append('rooms.name = ?')
        params.append(room)
    if class_section is not None:
        conditions.append('class_sections.name = ?')
        params.append(class_section)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    cur.execute(query, params)
    columns = [
        'entry_id', 'teacher_id', 'teacher_name', 
        'course_id', 'course_name', 
        'room_id', 'room_name', 
        'class_section_id', 'class_section_name', 
        'semester', 'shift'
    ]
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def load_timetable_for_ga(semester, shift):
    """
    If semester is '1-2', fetch both 1st and 2nd semester for the shift.
    If semester is None, fetch all semesters for the shift.
    """
    cur = conn.cursor()
    if semester is None:
        query = "SELECT * FROM timetable WHERE shift = ?"
        cur.execute(query, (shift,))
    elif semester in [1, 2]:
        query = "SELECT * FROM timetable WHERE semester = ? AND shift = ?"
        cur.execute(query, (semester, shift))
    else:
        query = "SELECT * FROM timetable WHERE semester = ? AND shift = ?"
        cur.execute(query, (semester, shift))
    return cur.fetchall()

# --- Shared master data management functions ---

class MasterTableDB:
    def __init__(self, conn):
        self.conn = conn

    def is_master_allowed(self):
        return current_master() in ["Timetable", "Datesheet"]

    def show_permission_warning(self, action):
        messagebox.showwarning("Permission Denied", f"No master module selected. Cannot {action}.")

class CourseDB(MasterTableDB):
    def add(self, name, teacher_id=1):
        if not self.is_master_allowed():
            self.show_permission_warning("add course")
            return
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO courses (name, teacher_id) VALUES (?, ?)', (name, teacher_id))
        self.conn.commit()

    def update(self, course_id, name, teacher_id=1):
        if not self.is_master_allowed():
            self.show_permission_warning("update course")
            return
        with self.conn:
            self.conn.execute('UPDATE courses SET name = ?, teacher_id = ? WHERE id = ?', (name, teacher_id, course_id))
        self.conn.commit()

    def delete(self, course_id):
        if not self.is_master_allowed():
            self.show_permission_warning("delete course")
            return
        with self.conn:
            self.conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        self.conn.commit()

class RoomDB(MasterTableDB):
    def add(self, name):
        if not self.is_master_allowed():
            self.show_permission_warning("add room")
            return
        with self.conn:
            self.conn.execute(
                'INSERT OR IGNORE INTO rooms (name) VALUES (?)',
                (name,)
            )
        self.conn.commit()

    def update(self, room_id, name):
        if not self.is_master_allowed():
            self.show_permission_warning("update room")
            return
        with self.conn:
            self.conn.execute(
                'UPDATE rooms SET name = ? WHERE id = ?',
                (name, room_id)
            )
        self.conn.commit()

    def delete(self, room_id):
        if not self.is_master_allowed():
            self.show_permission_warning("delete room")
            return
        with self.conn:
            self.conn.execute(
                'DELETE FROM rooms WHERE id = ?',
                (room_id,)
            )
        self.conn.commit()

class ClassSectionDB(MasterTableDB):
    def add(self, name, semester, shift):
        if not self.is_master_allowed():
            self.show_permission_warning("add class section")
            return
        with self.conn:
            self.conn.execute(
                'INSERT OR IGNORE INTO class_sections (name, semester, shift) VALUES (?, ?, ?)',
                (name, semester, shift)
            )
        self.conn.commit()

    def update(self, section_id, name, semester, shift):
        if not self.is_master_allowed():
            self.show_permission_warning("update class section")
            return
        with self.conn:
            self.conn.execute(
                'UPDATE class_sections SET name = ?, semester = ?, shift = ? WHERE id = ?',
                (name, semester, shift, section_id)
            )
        self.conn.commit()

    def delete(self, section_id):
        if not self.is_master_allowed():
            self.show_permission_warning("delete class section")
            return
        with self.conn:
            self.conn.execute(
                'DELETE FROM class_sections WHERE id = ?',
                (section_id,)
            )
        self.conn.commit()

def close_db():
    conn.close()

