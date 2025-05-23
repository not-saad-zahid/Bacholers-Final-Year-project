import sqlite3
from db.DataFile_db import init_timetable_db

conn = sqlite3.connect('DataFile.db', check_same_thread=False)

def save_datesheet(entries):
    """
    Save datesheet entries to the database.
    Each entry should be a dict with keys: semester, exam_start_date, exam_end_date, exam_start_time, exam_end_time
    """
    if not entries:
        return
    init_timetable_db()
    with conn:
        for e in entries:
            conn.execute('''
                INSERT INTO datesheet (
                    semester, exam_start_date, exam_end_date, exam_start_time, exam_end_time
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                int(e.get('semester', 0)),
                e.get('exam_start_date', e.get('start_date', '')),
                e.get('exam_end_date', e.get('end_date', '')),
                e.get('exam_start_time', e.get('start_time', '')),
                e.get('exam_end_time', e.get('end_time', ''))
            ))
    conn.commit()

def load_datesheet():
    """
    Load all datesheet entries from the database.
    Returns a list of dicts with keys: id, semester, exam_start_date, exam_end_date, exam_start_time, exam_end_time
    """
    init_timetable_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, semester, exam_start_date, exam_end_date, exam_start_time, exam_end_time
        FROM datesheet
    ''')
    columns = ['id', 'semester', 'exam_start_date', 'exam_end_date', 'exam_start_time', 'exam_end_time']
    return [dict(zip(columns, row)) for row in cur.fetchall()]

# Master data (courses, rooms, class_sections) should be managed via OOP classes in db/DataFile_db.py

def close_db():
    conn.close()
    
    