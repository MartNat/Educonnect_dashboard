import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Get the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'educonnect.db')

def init_db():
    """Initialize the database and create tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create students table
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                source TEXT,
                destination TEXT,
                course_of_study TEXT,
                level_of_study TEXT,
                application_status TEXT DEFAULT 'Not Started',
                conversion_probability FLOAT DEFAULT 0,
                email_responses INTEGER DEFAULT 0,
                call_responses INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create applications table
        c.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                school_name TEXT NOT NULL,
                program TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                documents_submitted BOOLEAN DEFAULT FALSE,
                offer_received BOOLEAN DEFAULT FALSE,
                offer_accepted BOOLEAN DEFAULT FALSE,
                deadline DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Create interactions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                type TEXT NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        conn.commit()
        print("Database initialized successfully")
        
        # Create test user
        create_test_user()
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_user(email, password, name, role='staff'):
    """Create a new user with hashed password"""
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        password_hash = generate_password_hash(password)
        c.execute('''
            INSERT INTO users (email, password_hash, name, role)
            VALUES (?, ?, ?, ?)
        ''', (email, password_hash, name, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    """Verify user credentials"""
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user:
            # Column index 2 is password
            if check_password_hash(user[2], password):
                return {
                    'id': user[0],
                    'email': user[1],
                    'name': user[3],
                    'role': user[4]
                }
        return None
    finally:
        conn.close()

def add_student(student_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO students (
                name, email, phone, source, destination,
                course_of_study, level_of_study, application_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_data['name'],
            student_data.get('email', ''),
            student_data.get('phone', ''),
            student_data['source'],
            student_data['destination'],
            student_data['course_of_study'],
            student_data['level_of_study'],
            'Not Started'
        ))
        
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding student: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_students():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT s.*, 
                   CASE 
                       WHEN s.application_status = 'Not Started' THEN 'secondary'
                       WHEN s.application_status = 'In Progress' THEN 'primary'
                       WHEN s.application_status = 'Completed' THEN 'success'
                       ELSE 'warning'
                   END as status_color
            FROM students s 
            ORDER BY s.created_at DESC
        ''')
        students = [dict(row) for row in c.fetchall()]
        
        # Get applications for each student
        for student in students:
            c.execute('''
                SELECT * FROM applications 
                WHERE student_id = ?
            ''', (student['id'],))
            student['applications'] = [dict(row) for row in c.fetchall()]
            
        return students
    except sqlite3.Error as e:
        print(f"Error fetching students: {e}")
        return []
    finally:
        conn.close()

def get_student_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get student info
        c.execute('''
            SELECT s.*, 
                   CASE 
                       WHEN s.application_status = 'Not Started' THEN 'secondary'
                       WHEN s.application_status = 'In Progress' THEN 'primary'
                       WHEN s.application_status = 'Completed' THEN 'success'
                       ELSE 'warning'
                   END as status_color
            FROM students s 
            WHERE s.name = ?
        ''', (name,))
        
        student = c.fetchone()
        
        if student:
            result = dict(student)
            
            # Get applications
            c.execute('''
                SELECT * FROM applications 
                WHERE student_id = ? 
                ORDER BY created_at DESC
            ''', (student['id'],))
            result['applications'] = [dict(row) for row in c.fetchall()]
            
            # Get interactions
            c.execute('''
                SELECT i.*,
                       datetime(i.created_at) as date
                FROM interactions i
                WHERE i.student_id = ? 
                ORDER BY i.created_at DESC
            ''', (student['id'],))
            result['interactions'] = [dict(row) for row in c.fetchall()]
            
            return result
            
        return None
        
    except sqlite3.Error as e:
        print(f"Error fetching student: {e}")
        return None
    finally:
        conn.close()

def delete_student(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM students WHERE name = ?', (name,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting student: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_student_interactions(student_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT * FROM interactions 
            WHERE student_id = ? 
            ORDER BY created_at DESC
        ''', (student_id,))
        return [dict(row) for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Error fetching interactions: {e}")
        return []
    finally:
        conn.close()

def add_interaction(student_id, interaction_type, notes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Add the interaction record
        c.execute('''
            INSERT INTO interactions (student_id, type, notes)
            VALUES (?, ?, ?)
        ''', (student_id, interaction_type, notes))
        
        # Update the interaction counter
        update_interaction_count(student_id, interaction_type)
        
        # Update conversion probability
        update_conversion_probability(student_id)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding interaction: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_interaction_count(student_id, interaction_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        if interaction_type == 'email':
            c.execute('''
                UPDATE students 
                SET email_responses = email_responses + 1 
                WHERE id = ?
            ''', (student_id,))
        elif interaction_type == 'call':
            c.execute('''
                UPDATE students 
                SET call_responses = call_responses + 1 
                WHERE id = ?
            ''', (student_id,))
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating interaction count: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_conversion_probability(student_id, probability=None):
    """Update student's conversion probability"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        if probability is None:
            # Get student data for calculation
            c.execute('''
                SELECT source, level_of_study, destination,
                       email_responses, call_responses
                FROM students WHERE id = ?
            ''', (student_id,))
            student_data = dict(c.fetchone())
            
            # Calculate probability based on student data
            probability = calculate_initial_probability(student_data)
        
        # Update the student's conversion probability
        c.execute('''
            UPDATE students 
            SET conversion_probability = ? 
            WHERE id = ?
        ''', (probability, student_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating conversion probability: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_application_status(app_id, field, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Update the application field
        c.execute(f'''
            UPDATE applications 
            SET {field} = ? 
            WHERE id = ?
        ''', (value, app_id))
        
        # Get student_id for this application
        c.execute('SELECT student_id FROM applications WHERE id = ?', (app_id,))
        result = c.fetchone()
        if result:
            student_id = result[0]
            # Update the conversion probability
            update_conversion_probability(student_id)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating application status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_active_applications_count():
    """Get count of active applications (where documents are submitted)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) FROM applications 
            WHERE documents_submitted = 1 
            AND status != 'Completed'
            AND offer_accepted = 0
        ''')
        return c.fetchone()[0]
    finally:
        conn.close()

def get_pending_documents_count():
    """Get count of applications waiting for document submission"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) FROM applications 
            WHERE documents_submitted = 0 
            AND status != 'Completed'
        ''')
        return c.fetchone()[0]
    finally:
        conn.close()

def get_offers_received_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) FROM applications 
            WHERE offer_received = 1
        ''')
        return c.fetchone()[0]
    finally:
        conn.close()

def get_completed_applications_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) FROM applications 
            WHERE offer_accepted = 1
        ''')
        return c.fetchone()[0]
    finally:
        conn.close()

def get_upcoming_deadlines():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                a.*, 
                s.name as student_name,
                julianday(a.deadline) - julianday('now') as days_left,
                CASE 
                    WHEN a.offer_accepted = 1 THEN 'success'
                    WHEN a.offer_received = 1 THEN 'info'
                    WHEN a.documents_submitted = 1 THEN 'primary'
                    ELSE 'warning'
                END as status_color
            FROM applications a
            JOIN students s ON a.student_id = s.id
            WHERE a.deadline >= date('now')
            ORDER BY a.deadline ASC
            LIMIT 10
        ''')
        return [dict(row) for row in c.fetchall()]
    finally:
        conn.close()

def get_pending_document_applications():
    """Get all applications where documents are pending submission"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT 
                a.*,
                s.name as student_name,
                s.email as student_email,
                CASE 
                    WHEN a.deadline IS NOT NULL 
                    AND julianday(a.deadline) - julianday('now') <= 7 
                    THEN 'danger'
                    WHEN a.deadline IS NOT NULL 
                    AND julianday(a.deadline) - julianday('now') <= 14 
                    THEN 'warning'
                    ELSE 'info'
                END as urgency_color
            FROM applications a
            JOIN students s ON a.student_id = s.id
            WHERE a.documents_submitted = 0
            AND a.status != 'Completed'
            ORDER BY 
                CASE WHEN a.deadline IS NOT NULL THEN 0 ELSE 1 END,
                a.deadline ASC,
                a.created_at DESC
            LIMIT 20
        ''')
        
        return [dict(row) for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Error fetching pending document applications: {e}")
        return []
    finally:
        conn.close()

def get_recent_offers():
    """Get recent applications where offers have been received"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT 
                a.*,
                s.name as student_name,
                s.email as student_email,
                s.course_of_study,
                s.level_of_study,
                julianday('now') - julianday(a.created_at) as days_since_offer
            FROM applications a
            JOIN students s ON a.student_id = s.id
            WHERE a.offer_received = 1
            ORDER BY 
                a.offer_accepted ASC,  -- Show unaccepted offers first
                a.created_at DESC      -- Most recent first
            LIMIT 15
        ''')
        
        offers = []
        for row in c.fetchall():
            offer = dict(row)
            # Add status description
            offer['status'] = (
                'Accepted' if offer['offer_accepted'] 
                else 'Pending Decision'
            )
            # Format days since offer
            offer['days_ago'] = int(offer['days_since_offer'])
            offers.append(offer)
            
        return offers
    except sqlite3.Error as e:
        print(f"Error fetching recent offers: {e}")
        return []
    finally:
        conn.close()

def calculate_overall_conversion_rate():
    """Calculate the overall conversion rate"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                ROUND(
                    (CAST(COUNT(CASE WHEN offer_accepted = 1 THEN 1 END) AS FLOAT) / 
                     CAST(COUNT(*) AS FLOAT)) * 100,
                    1
                )
            FROM applications
            WHERE created_at >= date('now', '-30 days')
        ''')
        return c.fetchone()[0] or 0
    finally:
        conn.close()

def get_high_potential_leads_count():
    """Get count of leads with high conversion probability"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) 
            FROM students 
            WHERE conversion_probability >= 70
        ''')
        return c.fetchone()[0]
    finally:
        conn.close()

def calculate_placement_rate():
    """Calculate the placement success rate"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                ROUND(
                    (CAST(COUNT(CASE WHEN offer_accepted = 1 THEN 1 END) AS FLOAT) / 
                     CAST(NULLIF(COUNT(CASE WHEN offer_received = 1 THEN 1 END), 0) AS FLOAT)) * 100,
                    1
                )
            FROM applications
            WHERE created_at >= date('now', '-90 days')
        ''')
        return c.fetchone()[0] or 0
    finally:
        conn.close()

def calculate_conversion_trend():
    """Calculate month-over-month conversion rate trend"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Get current month's conversion rate
        c.execute('''
            SELECT 
                ROUND(
                    (CAST(COUNT(CASE WHEN offer_accepted = 1 THEN 1 END) AS FLOAT) / 
                     NULLIF(CAST(COUNT(*) AS FLOAT), 0)) * 100,
                    1
                )
            FROM applications
            WHERE created_at >= date('now', 'start of month')
        ''')
        current_rate = c.fetchone()[0] or 0

        # Get previous month's conversion rate
        c.execute('''
            SELECT 
                ROUND(
                    (CAST(COUNT(CASE WHEN offer_accepted = 1 THEN 1 END) AS FLOAT) / 
                     NULLIF(CAST(COUNT(*) AS FLOAT), 0)) * 100,
                    1
                )
            FROM applications
            WHERE created_at >= date('now', 'start of month', '-1 month')
            AND created_at < date('now', 'start of month')
        ''')
        previous_rate = c.fetchone()[0] or 0

        # Calculate trend (difference)
        trend = round(current_rate - previous_rate, 1)
        return trend

    except sqlite3.Error as e:
        print(f"Error calculating conversion trend: {e}")
        return 0.0
    finally:
        conn.close()

def get_total_applications_count():
    """Get total count of all applications"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) FROM applications')
        return c.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error getting total applications count: {e}")
        return 0
    finally:
        conn.close()

def get_successful_placements_count():
    """Get count of successful placements (accepted offers)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(DISTINCT student_id) 
            FROM applications 
            WHERE offer_accepted = 1
            AND created_at >= date('now', '-365 days')
        ''')
        return c.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error getting successful placements count: {e}")
        return 0
    finally:
        conn.close()

def get_trend_labels():
    """Get labels for trend data (last 6 months)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            WITH RECURSIVE months(date) AS (
                SELECT date('now', 'start of month', '-5 months')
                UNION ALL
                SELECT date(date, '+1 month')
                FROM months
                WHERE date < date('now', 'start of month')
            )
            SELECT strftime('%B %Y', date) as month_label
            FROM months
            ORDER BY date
        ''')
        return [row[0] for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Error getting trend labels: {e}")
        return []
    finally:
        conn.close()

def get_conversion_rates_by_period():
    """Get conversion rates for the last 6 months"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            WITH RECURSIVE months(start_date, end_date) AS (
                SELECT 
                    date('now', 'start of month', '-5 months'),
                    date('now', 'start of month', '-4 months')
                UNION ALL
                SELECT 
                    date(end_date),
                    date(end_date, '+1 month')
                FROM months
                WHERE end_date < date('now', 'start of month', '+1 month')
            )
            SELECT 
                ROUND(
                    (CAST(COUNT(CASE WHEN a.offer_accepted = 1 THEN 1 END) AS FLOAT) / 
                     NULLIF(CAST(COUNT(a.id) AS FLOAT), 0) * 100),
                    1
                ) as conversion_rate
            FROM months m
            LEFT JOIN applications a 
                ON a.created_at >= m.start_date 
                AND a.created_at < m.end_date
            GROUP BY m.start_date
            ORDER BY m.start_date
        ''')
        rates = [row[0] or 0 for row in c.fetchall()]
        return rates
    except sqlite3.Error as e:
        print(f"Error getting conversion rates: {e}")
        return [0] * 6  # Return 6 months of zero values on error
    finally:
        conn.close()

def get_source_labels():
    """Get distinct lead source labels"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT DISTINCT source 
            FROM students 
            WHERE source IS NOT NULL
            ORDER BY source
        ''')
        return [row[0] for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Error getting source labels: {e}")
        return []
    finally:
        conn.close()

def get_source_conversion_rates():
    """Get conversion rates by lead source"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            WITH source_stats AS (
                SELECT 
                    s.source,
                    COUNT(DISTINCT s.id) as total_leads,
                    COUNT(DISTINCT CASE WHEN a.offer_accepted = 1 THEN s.id END) as conversions
                FROM students s
                LEFT JOIN applications a ON s.id = a.student_id
                WHERE s.source IS NOT NULL
                GROUP BY s.source
            )
            SELECT ROUND(
                (CAST(conversions AS FLOAT) / 
                 NULLIF(CAST(total_leads AS FLOAT), 0)) * 100,
                1
            ) as conversion_rate
            FROM source_stats
            ORDER BY source
        ''')
        rates = [row[0] or 0 for row in c.fetchall()]
        return rates
    except sqlite3.Error as e:
        print(f"Error getting source conversion rates: {e}")
        return []
    finally:
        conn.close()

def get_destination_labels():
    """Get distinct destination labels from students"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT DISTINCT destination 
            FROM students 
            WHERE destination IS NOT NULL
            ORDER BY destination
        ''')
        return [row[0] for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Error getting destination labels: {e}")
        return []
    finally:
        conn.close()

def get_destination_applications():
    """Get application counts by destination"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(a.id) as application_count
            FROM students s
            LEFT JOIN applications a ON s.id = a.student_id
            WHERE s.destination IS NOT NULL
            GROUP BY s.destination
            ORDER BY s.destination
        ''')
        counts = [row[0] or 0 for row in c.fetchall()]
        return counts
    except sqlite3.Error as e:
        print(f"Error getting destination applications: {e}")
        return []
    finally:
        conn.close()

def create_test_user():
    """Create a test user if none exists"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Check if any user exists
        c.execute('SELECT COUNT(*) FROM users')
        if c.fetchone()[0] == 0:
            # Create test user
            password_hash = generate_password_hash('admin123')
            c.execute('''
                INSERT INTO users (email, password, name, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin@educonnect.com', password_hash, 'Admin User', 'admin'))
            conn.commit()
            print("Test user created successfully")
    except sqlite3.Error as e:
        print(f"Error creating test user: {e}")
        conn.rollback()
    finally:
        conn.close()