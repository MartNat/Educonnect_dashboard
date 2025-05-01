from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from student_segmentation import load_model, predict_conversion, calculate_initial_probability
from database import (
    init_db, 
    add_student, 
    get_all_students, 
    get_student_by_name, 
    verify_user, 
    create_user, 
    delete_student,
    update_conversion_probability,  # Add this import
    add_interaction,  # Add this import
    update_interaction_count,  # Add this import
    get_active_applications_count,  # Add this import
    get_pending_documents_count,  # Add this import
    get_offers_received_count,  # Add this import
    get_completed_applications_count,  # Add this import
    get_upcoming_deadlines,  # Add this import
    get_pending_document_applications,  # Add this import
    get_recent_offers,  # Add this import
    calculate_overall_conversion_rate,  # Add this import
    calculate_conversion_trend,  # Add this import
    get_high_potential_leads_count,  # Add this import
    get_total_applications_count,  # Add this import
    get_successful_placements_count,  # Add this import
    calculate_placement_rate,  # Add this import
    get_trend_labels,  # Add this import
    get_conversion_rates_by_period,  # Add this import
    get_source_labels,  # Add this import
    get_source_conversion_rates,  # Add this import
    get_destination_labels,  # Add this import
    get_destination_applications  # Add this import
)
from datetime import datetime
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize database and load model
init_db()
model, encoder = load_model()

@app.context_processor
def utility_processor():
    def is_active_page(page_name):
        return 'active' if request.endpoint == page_name else ''
    return dict(is_active_page=is_active_page)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Store the requested endpoint in the URL parameters
            return redirect(url_for('login', next=request.endpoint))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = verify_user(email, password)
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['logged_in'] = True
            
            # Redirect to the next page or index
            next_page = request.args.get('next', 'index')
            return redirect(url_for(next_page))
            
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Protect all routes that require authentication
@app.route("/")
@login_required
def index():
    return render_template("index.html", page="index")

@app.route("/students")
@login_required
def students():
    try:
        # Your students page logic here
        return render_template('students.html', page="students")
    except Exception as e:
        flash('Error loading students page', 'error')
        return redirect(url_for('index'))

@app.route('/add_new_student', methods=['POST'])
@login_required
def add_new_student():
    try:
        new_student = {
            'name': request.form['name'],
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'source': request.form['source'],
            'destination': request.form['destination'],
            'course_of_study': request.form['course_of_study'],
            'level_of_study': request.form['level_of_study'],
        }
        # Add student and get ID
        student_id = add_student(new_student)
        if student_id:
            # Calculate initial probability
            initial_probability = calculate_initial_probability(new_student)
            # Update the conversion probability
            update_conversion_probability(student_id, initial_probability)
            # Get updated student data
            student = get_student_by_name(new_student['name'])
            flash(f"Student {new_student['name']} added successfully! Initial conversion probability: {initial_probability}%", 'success')
            return redirect(url_for('students', new_student=student_id))
        else:
            flash('Error adding student', 'error')
        return redirect(url_for('students'))
    except Exception as e:
        print(f"Error in add_new_student: {str(e)}")
        flash(f'Error adding student: {str(e)}', 'error')
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

@app.route('/student/<name>/interaction', methods=['POST'])
@login_required
def log_interaction(name):
    try:
        student = get_student_by_name(name)
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('students'))
        interaction_type = request.form['interaction_type']
        notes = request.form['notes']
        # Add the interaction
        add_interaction(student['id'], interaction_type, notes)
        # Update interaction counter and conversion probability
        update_interaction_count(student['id'], interaction_type)
        update_conversion_probability(student['id'])
        flash('Interaction logged successfully!', 'success')
        return redirect(url_for('student_profile', name=name))
    except Exception as e:
        print(f"Error logging interaction: {e}")
        flash('Error logging interaction', 'error')
        return redirect(url_for('student_profile', name=name))

@app.route('/student/<int:student_id>/application', methods=['POST'])
@login_required
def add_application(student_id):
    try:
        # Get form data
        school_name = request.form['school_name']
        program = request.form['program']
        # Connect to database
        conn = sqlite3.connect('educonnect.db')
        c = conn.cursor()
        # Insert new application
        c.execute('''
            INSERT INTO applications (
                student_id, school_name, program, 
                status, documents_submitted, 
                offer_received, offer_accepted
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, school_name, program, 'Pending', False, False, False))
        # Update student's application status
        c.execute('''
            UPDATE students 
            SET application_status = 'In Progress' 
            WHERE id = ?
        ''', (student_id,))
        conn.commit()
        conn.close()
        flash('Application added successfully!', 'success')
        return redirect(url_for('student_profile', name=request.form['student_name']))
    except Exception as e:
        print(f"Error adding application: {e}")
        flash('Error adding application', 'error')
        return redirect(url_for('student_profile', name=request.form['student_name']))

@app.route('/api/application/<int:app_id>/update', methods=['POST'])
@login_required
def update_application_status(app_id):
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        conn = sqlite3.connect('educonnect.db')
        c = conn.cursor()
        # Update the specific field
        c.execute(f'UPDATE applications SET {field} = ? WHERE id = ?', (value, app_id))
        # If offer is accepted, update student status
        if field == 'offer_accepted' and value:
            c.execute('''
                UPDATE students 
                SET application_status = 'Completed'
                WHERE id = (SELECT student_id FROM applications WHERE id = ?)
            ''', (app_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating application: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route("/applications")
@login_required
def applications():
    # Get all students and their applications
    students = get_all_students()
    # Get application statistics
    stats = {
        'active_applications': get_active_applications_count(),
        'pending_documents': get_pending_documents_count(),
        'offers_received': get_offers_received_count(),
        'completed_applications': get_completed_applications_count()
    }
    # Get upcoming deadlines with student info
    upcoming_deadlines = get_upcoming_deadlines()
    # Get applications pending documents with student details
    pending_documents = get_pending_document_applications()
    # Get recent offers with student info
    recent_offers = get_recent_offers()
    return render_template(
        'applications.html',
        page="applications",
        students=students,
        stats=stats,
        upcoming_deadlines=upcoming_deadlines,
        pending_documents=pending_documents,
        recent_offers=recent_offers
    )

@app.route("/analytics")
@login_required
def analytics():
    try:
        # Get and evaluate all stats immediately
        stats = {
            'conversion_rate': float(calculate_overall_conversion_rate() or 0),
            'conversion_trend': float(calculate_conversion_trend() or 0),
            'high_potential_leads': int(get_high_potential_leads_count() or 0),
            'active_applications': int(get_active_applications_count() or 0),
            'total_applications': int(get_total_applications_count() or 0),
            'successful_placements': int(get_successful_placements_count() or 0),
            'placement_rate': float(calculate_placement_rate() or 0)
        }

        # Execute functions and store results
        trend_labels = list(map(str, get_trend_labels() or []))
        conversion_rates = list(map(float, get_conversion_rates_by_period() or [0] * 6))
        trends = {
            'labels': trend_labels,
            'conversion_rates': conversion_rates
        }

        # Get source data with proper type conversion
        source_labels = list(map(str, get_source_labels() or []))
        source_values = list(map(float, get_source_conversion_rates() or []))
        source_data = {
            'labels': source_labels,
            'values': source_values
        }

        # Get destination data with proper type conversion
        dest_labels = list(map(str, get_destination_labels() or []))
        dest_values = list(map(int, get_destination_applications() or []))
        destination_data = {
            'labels': dest_labels,
            'values': dest_values
        }

        # Convert data to JSON strings
        trends_json = json.dumps(trends)
        source_data_json = json.dumps(source_data)
        destination_data_json = json.dumps(destination_data)

        # Debug print
        print("Analytics data prepared:", {
            'stats': stats,
            'trends': trends,
            'source_data': source_data,
            'destination_data': destination_data
        })

        return render_template(
            'analytics.html',
            page="analytics",
            stats=stats,
            trends_json=trends_json,
            source_data_json=source_data_json,
            destination_data_json=destination_data_json,
            user_name=session.get('user_name', '')
        )

    except Exception as e:
        print(f"Error in analytics route: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading analytics data', 'error')
        return redirect(url_for('index'))

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

@app.route('/student/<name>')
@login_required
def student_profile(name):
    student = get_student_by_name(name)
    if student is None:
        flash('Student not found', 'error')
        return redirect(url_for('students'))
    
    print("Fetched student data:", student)  # Debug print
    return render_template('profile.html', student=student)

@app.route('/api/students/<name>', methods=['DELETE'])
@login_required
def delete_student_route(name):
    if delete_student(name):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

if __name__ == "__main__":
    # Initialize database
    init_db()
    # Create test user if it doesn't exist
    try:
        create_user(
            email='admin@educonnect.com',
            password='admin123',
            name='Admin User',
            role='admin'
        )
        print("Test user created or already exists")
    except Exception as e:
        print(f"Note: {e}")
    app.run(debug=True)