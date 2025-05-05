import sqlite3

conn = sqlite3.connect('timetable.db', check_same_thread=False)

def init_datesheet_db():
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS datesheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            course TEXT NOT NULL,
            semester INTEGER NOT NULL,
            shift TEXT NOT NULL,
            section TEXT NOT NULL
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
                INSERT INTO datesheet (date, time, course, semester, shift, section)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                e.get('date', ''), e.get('time', ''), e.get('course', ''),
                int(e.get('semester', 0)), e.get('shift', ''), e.get('section', '')
            ))
    conn.commit()

def load_datesheet():
    init_datesheet_db()
    cur = conn.cursor()
    cur.execute('SELECT date, time, course, semester, shift, section FROM datesheet')
    columns = ['date', 'time', 'course', 'semester', 'shift', 'section']
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def close_db():
    conn.close()