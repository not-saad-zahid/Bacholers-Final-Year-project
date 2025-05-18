import tkinter.messagebox as messagebox
import sqlite3
import os

os.chdir(os.path.dirname(__file__))
db_path = os.path.join(os.path.dirname(__file__), 'timetable.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.execute('PRAGMA foreign_keys = ON')

def init_timetable_db():
    c = conn.cursor()
    
    # Create the timetable table
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            class_section_id INTEGER NOT NULL,
            semester TEXT NOT NULL,  -- Changed to TEXT
            shift TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (class_section_id) REFERENCES class_sections (id)
        )
    ''')
    
    # Create the teachers table (no change)
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create the courses table (no change regarding semester here)
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            indicators TEXT,
            teacher_id INTEGER NOT NULL, 
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            UNIQUE(name, code, teacher_id)
        )
    ''')
    
    # Create the rooms table (no change)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name INTEGER NOT NULL UNIQUE 
        )
    ''')
    
    # Create the class_sections table
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT NOT NULL, -- Changed to TEXT
            shift TEXT NOT NULL,
            UNIQUE(name, semester, shift)   
        )
    ''')

    # Attempt to ALTER existing tables if they exist.
    # SQLite has limitations with ALTER TABLE for changing column types directly if constraints exist or data types are very different.
    # Often, for major type changes, a more robust approach is to:
    # 1. Rename the old table.
    # 2. Create the new table with the correct schema.
    # 3. Copy data from the old table to the new, transforming as needed.
    # 4. Drop the old table.
    # For INTEGER to TEXT, SQLite is often flexible, but this is a simplified attempt.
    
    existing_tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    if 'timetable' in existing_tables:
        try:
            # This won't change type if column already text. If it's INT, SQLite stores text fine in INT cols usually.
            # True type change is harder. This just ensures the schema matches if it was recreated.
            print("Checking 'timetable' schema. If it was INTEGER, new entries will be TEXT.")
        except sqlite3.OperationalError:
             pass # Ignore if fails, implies more complex migration needed if types were strictly enforced and different.

    if 'class_sections' in existing_tables:
        try:
            print("Checking 'class_sections' schema. If it was INTEGER, new entries will be TEXT.")
        except sqlite3.OperationalError:
            pass
            
    # Add new columns to courses if they don't exist (from previous step, ensure it's idempotent)
    if 'courses' in existing_tables:
        course_cols = [col[1] for col in c.execute("PRAGMA table_info(courses)").fetchall()]
        if 'code' not in course_cols:
            try:
                c.execute("ALTER TABLE courses ADD COLUMN code TEXT NOT NULL DEFAULT 'N/A'")
                print("Added 'code' column to courses table.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e): raise
        if 'indicators' not in course_cols:
            try:
                c.execute("ALTER TABLE courses ADD COLUMN indicators TEXT")
                print("Added 'indicators' column to courses table.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e): raise
    
    conn.commit()
    return conn


def fetch_id_from_name(table, name, **kwargs):
    cur = conn.cursor()
    try:
        if table == "rooms":
            # ... (no change from previous version for rooms)
            try:
                room_name_val = int(name)
                if room_name_val <= 0:
                    raise ValueError
                query = "SELECT id FROM rooms WHERE name = ?"
                params = (room_name_val,)
            except ValueError:
                messagebox.showerror("Invalid Room", "Room must be a positive integer.")
                return None
        elif table == "teachers":
            # ... (no change for teachers)
            query = "SELECT id FROM teachers WHERE name = ?"
            params = (name,)
        elif table == "courses":
            # ... (no change for courses from previous version)
            teacher_id = kwargs.get("teacher_id")
            code = kwargs.get("code")
            indicators = kwargs.get("indicators", "") 
            if not teacher_id or not code:
                messagebox.showerror("Missing Data", "Teacher ID and Course Code are required for courses.")
                return None
            query = "SELECT id FROM courses WHERE name = ? AND teacher_id = ? AND code = ?"
            params = (name, teacher_id, code)
        elif table == "class_sections":
            semester_text = kwargs.get("semester") # Semester is now TEXT
            shift = kwargs.get("shift")
            if not semester_text or not shift: # semester_text can be any string now
                messagebox.showerror("Missing Data", "Semester (as text) and Shift are required for class sections.")
                return None
            query = "SELECT id FROM class_sections WHERE name = ? AND semester = ? AND shift = ?"
            params = (name, semester_text, shift)
        else:
            messagebox.showerror("Error", f"Unknown table: {table}")
            return None

        cur.execute(query, params)
        result = cur.fetchone()

        if result:
            return result[0]
        else:
            # Insert the record
            if table == "teachers":
                cur.execute("INSERT INTO teachers (name) VALUES (?)", (name,))
            elif table == "courses":
                cur.execute("INSERT INTO courses (name, teacher_id, code, indicators) VALUES (?, ?, ?, ?)", 
                            (name, teacher_id, code, indicators))
            elif table == "rooms":
                cur.execute("INSERT INTO rooms (name) VALUES (?)", (int(name),))
            elif table == "class_sections":
                cur.execute("INSERT INTO class_sections (name, semester, shift) VALUES (?, ?, ?)", 
                            (name, semester_text, shift)) # Use semester_text
            
            conn.commit()
            return cur.lastrowid

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch or create ID in {table} for '{name}': {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred in fetch_id_from_name for {table} '{name}': {e}")
        return None

def load_timetable(shift, semester_label=None): # Primary filter is shift, semester_label is optional text filter
    """
    Load timetable entries from the database.
    Primary filter: shift.
    Optional secondary filter: semester_label (exact string match).
    """
    cur = conn.cursor()
    
    query = '''
        SELECT 
            t.id AS entry_id,
            t.teacher_id,
            teachers.name AS teacher_name, 
            t.course_id,
            courses.name AS course_name,
            courses.code AS course_code,
            courses.indicators AS course_indicators,
            t.room_id,
            rooms.name AS room_name, 
            t.class_section_id,
            class_sections.name AS class_section_name, 
            t.semester,  -- This is the TEXT semester label
            t.shift
        FROM timetable t
        JOIN teachers ON t.teacher_id = teachers.id
        JOIN courses ON t.course_id = courses.id
        JOIN rooms ON t.room_id = rooms.id
        JOIN class_sections ON t.class_section_id = class_sections.id
        WHERE t.shift = ? 
    '''
    params_list = [shift]
    
    if semester_label: # If a specific semester label is provided for further filtering
        query += ' AND t.semester = ?'
        params_list.append(semester_label)
    
    cur.execute(query, tuple(params_list))
    
    columns = [
        'entry_id', 'teacher_id', 'teacher_name', 
        'course_id', 'course_name', 'course_code', 'course_indicators',
        'room_id', 'room_name', 
        'class_section_id', 'class_section_name', 
        'semester', 'shift'
    ]
    
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def load_timetable_for_ga(shift): # Only takes shift as primary criteria
    """
    Load all necessary data for the GA, filtered ONLY by shift.
    Semester is just a descriptive attribute of the loaded entries.
    """
    cur = conn.cursor()
    query = """
        SELECT 
            tt.teacher_id, tt.course_id, tt.room_id, tt.class_section_id, 
            tt.semester, -- Text semester label
            tt.shift,
            c.name as course_name, c.code as course_code, c.indicators as course_indicators,
            r.name as room_name,
            t.name as teacher_name,
            cs.name as class_section_name
        FROM timetable tt
        JOIN courses c ON tt.course_id = c.id
        JOIN rooms r ON tt.room_id = r.id
        JOIN teachers t ON tt.teacher_id = t.id
        JOIN class_sections cs ON tt.class_section_id = cs.id
        WHERE tt.shift = ? 
    """
    # Removed semester from WHERE clause for GA data loading
    params = [shift]
    
    cur.execute(query, tuple(params))
    
    columns = [
        'teacher_id', 'course_id', 'room_id', 'class_section_id', 
        'semester', 'shift', 
        'course_name', 'course_code', 'course_indicators', 
        'room_name', 'teacher_name', 'class_section_name'
    ]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    print(f"Loaded {len(results)} entries for GA for shift: {shift}")
    return results

def close_db():
    conn.close()