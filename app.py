from flask import Flask, render_template, request, redirect, url_for
from student_segmentation import load_model, predict_conversion
from database import init_db, add_student, get_all_students, get_student_by_name
import numpy as np
from datetime import datetime, timedelta
import os
import sqlite3

app = Flask(__name__, static_folder='static')

# Initialize the database at startup
init_db()

# Load the model at startup
model, encoder = load_model()

@app.route("/")
def index():
    students = get_all_students()
    
    # Calculate dashboard metrics
    total_students = len(students)
    probabilities = [student['conversion_probability'] for student in students]
    high_probability = len([p for p in probabilities if p > 70])
    avg_probability = round(np.mean(probabilities) if probabilities else 0, 1)
    
    # Get source analysis
    source_analysis = {
        'high': len([s for s in students if s['conversion_probability'] > 70]),
        'medium': len([s for s in students if 40 < s['conversion_probability'] <= 70]),
        'low': len([s for s in students if s['conversion_probability'] <= 40])
    }
    
    # Get destination analysis
    destinations = {}
    for student in students:
        dest = student['destination']
        if dest not in destinations:
            destinations[dest] = {'high': 0, 'medium': 0, 'low': 0}
        if student['conversion_probability'] > 70:
            destinations[dest]['high'] += 1
        elif student['conversion_probability'] > 40:
            destinations[dest]['medium'] += 1
        else:
            destinations[dest]['low'] += 1
    
    # Get high probability students
    high_prob_students = sorted(
        [s for s in students if s['conversion_probability'] > 70],
        key=lambda x: x['conversion_probability'],
        reverse=True
    )[:5]  # Top 5 students
    
    return render_template(
        "index.html",
        total_students=total_students,
        high_probability=round((high_probability/total_students * 100) if total_students else 0, 1),
        avg_probability=avg_probability,
        active_applications=len([s for s in students if s['conversion_probability'] > 50]),
        source_analysis=source_analysis,
        destination_analysis=destinations,
        high_prob_students=high_prob_students
    )

@app.route("/students")
def students():
    all_students = get_all_students()
    return render_template("students.html", students=all_students)

@app.route("/add_student", methods=['POST'])
def add_student_route():
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
        return render_template("profile.html", student=student)
    return redirect(url_for('students'))

@app.route("/student/<name>/update", methods=['POST'])
def update_student_details(name):
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    # Update database with new details
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
    
    # Get current student data
    student = get_student_by_name(name)
    
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
    c.execute('''
        UPDATE students 
        SET email_responses = ?, call_responses = ?
        WHERE name = ?
    ''', (email_responses, call_responses, name))
    conn.commit()
    
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

if __name__ == "__main__":
    app.run(debug=True)