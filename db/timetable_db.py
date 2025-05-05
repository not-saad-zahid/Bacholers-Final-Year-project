import sqlite3
import os

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
            semester INTEGER NOT NULL,
            shift TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (class_section_id) REFERENCES class_sections (id)
        )
    ''')
    
    # Create the teachers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create the courses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')
    
    # Create the rooms table (accepts integer values)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name INTEGER NOT NULL UNIQUE
        )
    ''')
    
    # Create the class_sections table (accepts alphanumeric values)
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE CHECK(name GLOB '[a-zA-Z0-9]*'),
            semester INTEGER NOT NULL,
            shift TEXT NOT NULL
        )
    ''')
    
    # Remove obsolete columns if they exist
    c.execute("PRAGMA table_info(timetable)")
    existing_cols = [row[1] for row in c.fetchall()]
    obsolete_cols = ['start_time', 'end_time']  # Add any obsolete column names here
    for col in obsolete_cols:
        if col in existing_cols:
            # SQLite doesn't support DROP COLUMN directly; use workaround
            columns_to_select = [col for col in ['id', 'teacher_id', 'course_id', 'room_id', 'class_section_id', 'semester', 'shift'] if col in existing_cols]
            query = f"CREATE TABLE temp_table AS SELECT {', '.join(columns_to_select)} FROM timetable"
            conn.execute(query)
            conn.execute("DROP TABLE timetable")
            conn.execute("ALTER TABLE temp_table RENAME TO timetable")
    conn.commit()
    return conn

def get_or_create_id(table, name, **kwargs):
    """
    Get the ID of a record in the specified table by name, or create it if it doesn't exist.
    """
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = c.fetchone()
    if row:
        return row[0]
    columns = ['name'] + list(kwargs.keys())
    values = [name] + list(kwargs.values())
    try:
        c.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})", values)
    except sqlite3.IntegrityError:
        c.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
        row = c.fetchone()
        return row[0] if row else None
    conn.commit()
    return c.lastrowid

def save_timetable(entries):
    """
    Save timetable entries to the database.
    """
    if not entries:
        return
    try:
        semester = int(entries[0].get('semester', 0))
    except ValueError:
        semester = 0
    shift = entries[0].get('shift', '').strip()
    
    init_timetable_db()
    with conn:
        # Delete existing timetable entries for the same semester and shift
        conn.execute('DELETE FROM timetable WHERE semester = ? AND shift = ?', (semester, shift))
        
        for e in entries:
            if not e.get('teacher') or not e.get('course') or not e.get('room') or not e.get('class_section'):
                continue  # Skip invalid entries
            
            # Get or insert teacher
            teacher_id = get_or_create_id('teachers', e.get('teachers', ''))
            
            # Get or insert course
            course_id = get_or_create_id('courses', e.get('course', ''), teacher_id=teacher_id)
            
            # Get or insert room
            room_id = get_or_create_id('rooms', e.get('room', ''))
            
            # Get or insert class_section
            class_section_id = get_or_create_id('class_sections', e.get('class_section', ''), semester=semester, shift=shift)
            
            # Insert timetable entry
            conn.execute('''
                INSERT INTO timetable (
                    teacher_id, course_id, room_id, class_section_id, semester, shift
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                teacher_id,
                course_id,
                room_id,
                class_section_id,
                semester,
                shift
            ))
    conn.commit()

def load_timetable(semester=None, shift=None):
    """
    Load timetable entries from the database.
    """
    init_timetable_db()
    cur = conn.cursor()
    
    # Query to join timetable with related tables and fetch human-readable names
    query = '''
        SELECT 
            teachers.name AS teacher, 
            courses.name AS course, 
            rooms.name AS room, 
            class_sections.name AS class_section, 
            t.semester, t.shift
        FROM timetable t
        JOIN teachers ON t.teacher_id = teachers.id
        JOIN courses ON t.course_id = courses.id
        JOIN rooms ON t.room_id = rooms.id
        JOIN class_sections ON t.class_section_id = class_sections.id
        '''
    
    # Add filtering conditions dynamically
    params = []
    if semester is not None and shift is not None:
        query += ' WHERE t.semester = ? AND t.shift = ?'
        params.extend([semester, shift])
    elif semester is not None:
        query += ' WHERE t.semester = ?'
        params.append(semester)
    elif shift is not None:
        query += ' WHERE t.shift = ?'
        params.append(shift)
    
    # Execute the query with the parameters
    cur.execute(query, params)
    
    # Define the columns to map the results
    columns = ['teacher', 'course', 'room', 'class_section', 'semester', 'shift']
    
    # Return the results as a list of dictionaries
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def close_db():
    conn.close()