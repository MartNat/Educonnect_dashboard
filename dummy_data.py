from database import init_db, add_student, add_interaction, add_application
from datetime import datetime, timedelta
import random

dummy_students = [
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@gmail.com",
        "phone": "0712345678",
        "source": "walk-in",
        "destination": "UK",
        "course_of_study": "Computer Science",
        "level_of_study": "undergraduate",
        "date_of_birth": "2000-05-15",
        "emergency_contact_name": "Robert Johnson",
        "emergency_contact_phone": "0798765432",
        "applications": [
            {
                "school_name": "University of Manchester",
                "program": "BSc Computer Science",
                "documents_submitted": True,
                "offer_received": True,
                "offer_accepted": False
            }
        ],
        "interactions": [
            {
                "type": "email",
                "notes": "Initial inquiry about UK universities",
                "date": "2025-04-28"
            },
            {
                "type": "call",
                "notes": "Discussed application requirements",
                "date": "2025-04-29"
            }
        ]
    },
    {
        "name": "Bob Smith",
        "email": "bob.smith@yahoo.com",
        "phone": "0723456789",
        "source": "fairs",
        "destination": "US",
        "course_of_study": "Business Administration",
        "level_of_study": "postgraduate",
        "date_of_birth": "1995-08-22",
        "emergency_contact_name": "Sarah Smith",
        "emergency_contact_phone": "0787654321"
    },
    {
        "name": "Carol Zhang",
        "email": "carol.zhang@outlook.com",
        "phone": "0734567890",
        "source": "referrals",
        "destination": "Canada",
        "course_of_study": "Data Science",
        "level_of_study": "postgraduate",
        "date_of_birth": "1997-03-10",
        "emergency_contact_name": "David Zhang",
        "emergency_contact_phone": "0776543210"
    },
    {
        "name": "David Kumar",
        "email": "david.kumar@gmail.com",
        "phone": "0745678901",
        "source": "school visit",
        "destination": "Australia",
        "course_of_study": "Engineering",
        "level_of_study": "undergraduate",
        "date_of_birth": "2001-11-30",
        "emergency_contact_name": "Priya Kumar",
        "emergency_contact_phone": "0765432109"
    }
]

# Add more varied student profiles
more_students = [
    {
        "name": "Emma Wilson",
        "email": "emma.w@outlook.com",
        "phone": "0756789012",
        "source": "referrals",
        "destination": "Canada",
        "course_of_study": "MBA",
        "level_of_study": "postgraduate",
        "date_of_birth": "1998-07-19",
        "emergency_contact_name": "William Wilson",
        "emergency_contact_phone": "0754321098",
        "applications": [
            {
                "school_name": "University of Toronto",
                "program": "MBA Finance",
                "documents_submitted": True,
                "offer_received": False,
                "offer_accepted": False
            }
        ],
        "interactions": [
            {
                "type": "call",
                "notes": "Discussed MBA requirements",
                "date": "2025-04-25"
            }
        ]
    },
    # Add more students here...
]

dummy_students.extend(more_students)

def load_dummy_data():
    print("Initializing database...")
    init_db()
    
    print("Loading dummy students...")
    for student in dummy_students:
        try:
            # Add student basic info
            student_id = add_student(student)
            
            if student_id:
                print(f"Added student: {student['name']}")
                
                # Add applications
                for app in student.get('applications', []):
                    add_application(student_id, app)
                    print(f"  Added application for {student['name']}: {app['school_name']}")
                
                # Add interactions
                for interaction in student.get('interactions', []):
                    add_interaction(
                        student_id,
                        interaction['type'],
                        interaction['notes']
                    )
                    print(f"  Added {interaction['type']} interaction for {student['name']}")
            else:
                print(f"Failed to add student: {student['name']}")
                
        except Exception as e:
            print(f"Error adding student {student['name']}: {e}")
    
    print("Dummy data loading completed!")

if __name__ == "__main__":
    load_dummy_data()