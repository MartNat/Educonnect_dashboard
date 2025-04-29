import sqlite3
from datetime import datetime
import os

# Get the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'educonnect.db')

def init_db():
    conn = sqlite3.connect('educonnect.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            response TEXT NOT NULL,
            destination TEXT NOT NULL,
            course_of_study TEXT NOT NULL,
            level_of_study TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at DATETIME,
            conversion_probability FLOAT,
            email_responses INTEGER DEFAULT 0,
            call_responses INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def add_student(student_data):
    """Add a new student to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO students (
            name, source, response, destination, 
            course_of_study, level_of_study, 
            conversion_probability, created_at,
            email_responses, call_responses
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        student_data['name'],
        student_data['source'],
        student_data['response'],
        student_data['destination'],
        student_data['course_of_study'],
        student_data['level_of_study'],
        student_data.get('conversion_probability', 0),
        datetime.now(),
        student_data.get('email_responses', 0),
        student_data.get('call_responses', 0)
    ))
    
    student_id = c.lastrowid
    conn.commit()
    conn.close()
    return student_id

def get_all_students():
    """Retrieve all students from the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    c.execute('SELECT * FROM students ORDER BY created_at DESC')
    students = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return students

def get_student_by_name(name):
    """Retrieve a student by their name"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM students WHERE name = ?', (name,))
    student = c.fetchone()
    
    conn.close()
    return dict(student) if student else None