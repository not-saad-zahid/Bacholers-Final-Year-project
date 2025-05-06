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
                name = int(name)  # Ensure the room name is an integer
                if name <= 0:
                    raise ValueError
                else:
                    print(f"Valid room name: {name}.")
            except ValueError:
                print(f"Invalid room name: {name}. Room name must be a positive integer.")
                return None

        # Check if the record exists
        query = f"SELECT id FROM {table} WHERE name = ?"
        params = [name]

        # Add additional conditions for specific tables
        if table == "class_sections" and "semester" in kwargs and "shift" in kwargs:
            query += " AND semester = ? AND shift = ?"
            params.extend([kwargs["semester"], kwargs["shift"]])

        cur = conn.cursor()
        cur.execute(query, tuple(params))
        result = cur.fetchone()
        if result:
            print(f"Fetched ID for {table}: {result[0]}")  # Print fetched ID
            return result[0]

        # Insert the record if it does not exist
        if table == "courses" and "teacher_id" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, teacher_id) VALUES (?, ?)", (name, kwargs["teacher_id"]))
            print(f"Inserted new course: {name} with teacher ID {kwargs['teacher_id']}")
        elif table == "class_sections" and "semester" in kwargs and "shift" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, semester, shift) VALUES (?, ?, ?)", (name, kwargs["semester"], kwargs["shift"]))
            print(f"Inserted new class_section: {name} with semester {kwargs['semester']} and shift {kwargs['shift']}")
        elif table == "rooms":
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
            print(f"Room name inserted: {name}.")
        else:
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
            print(f"Inserted new {table}: {name}")

        conn.commit()
        generated_id = cur.lastrowid
        print(f"Generated ID for {table}: {generated_id}")  # Print generated ID
        return generated_id
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
    
    # Base query to join timetable with related tables and fetch human-readable names
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
    
    # Add filtering conditions dynamically
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
    
    # Combine conditions into the query
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    # Execute the query with the parameters
    cur.execute(query, params)
    
    # Define the columns to map the results
    columns = [
        'entry_id', 'teacher_id', 'teacher_name', 
        'course_id', 'course_name', 
        'room_id', 'room_name', 
        'class_section_id', 'class_section_name', 
        'semester', 'shift'
    ]
    
    # Return the results as a list of dictionaries
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def close_db():
    conn.close()