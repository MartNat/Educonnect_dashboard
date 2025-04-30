from flask import Flask, render_template, request, redirect, url_for
from student_segmentation import load_model, predict_conversion
from database import init_db, add_student, get_all_students, get_student_by_name
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize database and load model
init_db()
model, encoder = load_model()

@app.context_processor
def utility_processor():
    def is_active_page(page):
        return 'active' if request.endpoint == page else ''
    return dict(is_active_page=is_active_page)

@app.route("/")
def index():
    return render_template("index.html", page="index")

@app.route("/students")
def students():
    all_students = get_all_students()
    return render_template("students.html", students=all_students, page="students")

@app.route("/add_student", methods=['POST'])
def add_new_student():
    new_student = {
        "name": request.form.get('name'),
        "source": request.form.get('source'),
        "response": request.form.get('response'),
        "destination": request.form.get('destination'),
        "course_of_study": request.form.get('course_of_study'),
        "level_of_study": request.form.get('level_of_study'),
        "email_responses": 0,
        "call_responses": 0
    }
    
    # Calculate conversion probability
    conversion_probability = predict_conversion(new_student, model, encoder)
    new_student['conversion_probability'] = conversion_probability
    
    # Add to database
    add_student(new_student)
    
    return redirect(url_for('students'))

@app.route("/student/<name>")
def student_profile(name):
    student = get_student_by_name(name)
    if student:
        return render_template("profile.html", student=student, page="student_profile")
    return redirect(url_for('students'))

@app.route("/student/<name>/update", methods=['POST'])
def update_student_details(name):
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    conn = sqlite3.connect('educonnect.db')
    c = conn.cursor()
    c.execute('''
        UPDATE students 
        SET email = ?, phone = ?
        WHERE name = ?
    ''', (email, phone, name))
    conn.commit()
    conn.close()
    
    return redirect(url_for('student_profile', name=name))

@app.route("/student/<name>/interaction", methods=['POST'])
def log_interaction(name):
    interaction_type = request.form.get('interaction_type')
    notes = request.form.get('notes')
    
    student = get_student_by_name(name)
    if not student:
        return redirect(url_for('students'))
    
    # Update interaction counts
    email_responses = student['email_responses']
    call_responses = student['call_responses']
    
    if interaction_type == 'email':
        email_responses += 1
    else:
        call_responses += 1
    
    # Update database
    conn = sqlite3.connect('educonnect.db')
    c = conn.cursor()
    
    # Update interaction counts
    c.execute('''
        UPDATE students 
        SET email_responses = ?, call_responses = ?
        WHERE name = ?
    ''', (email_responses, call_responses, name))
    
    # Recalculate conversion probability
    student_data = {
        'source': student['source'],
        'email_responses': email_responses,
        'call_responses': call_responses,
        'destination': student['destination'],
        'level_of_study': student['level_of_study'],
        'course_of_study': student['course_of_study']
    }
    
    new_probability = predict_conversion(student_data, model, encoder)
    
    # Update conversion probability
    c.execute('''
        UPDATE students 
        SET conversion_probability = ?
        WHERE name = ?
    ''', (new_probability, name))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('student_profile', name=name))

@app.route("/applications")
def applications():
    return render_template("applications.html", page="applications")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html", page="analytics")

@app.route("/tasks")
def tasks():
    return render_template("tasks.html", page="tasks")

@app.route("/interviews")
def interviews():
    return render_template("interviews.html", page="interviews")

@app.route("/placements")
def placements():
    return render_template("placements.html", page="placements")

@app.route("/programs")
def programs():
    return render_template("programs.html", page="programs")

@app.route("/settings")
def settings():
    return render_template("settings.html", page="settings")

if __name__ == "__main__":
    app.run(debug=True)