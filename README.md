# EduConnect Dashboard

## Overview
EduConnect Dashboard is a Flask-based web application designed to manage educational workflows, including student profiles, applications, analytics, and tasks. It provides tools for tracking student interactions, managing applications, and analyzing conversion probabilities using a machine learning model.

---

## Features
- **Dashboard**: Centralized hub for navigation and key metrics.
- **Student Management**:
  - View and manage student profiles.
  - Track details like name, email, phone, source, destination, course, and level of study.
  - Display conversion probabilities using a **Random Forest algorithm**.
- **Applications**: Track and manage student application statuses.
- **Analytics**: Analyze trends and metrics related to student applications and interactions.
- **Tasks Management**: Organize and track tasks related to student workflows.
- **Interaction Logging**: Log and track interactions (e.g., calls, emails, meetings) with students.

---

## Conversion Probability Algorithm
The application uses a **Random Forest algorithm** to calculate conversion probabilities. Factors influencing the probability include:
- **Source/Lead Type**:
  - Referral: +15%
  - School Visit: +10%
  - Education Fair: +8%
  - Walk-in: +5%
- **Study Level**:
  - Postgraduate: +10%
  - Undergraduate: +5%
- **Destination Country**:
  - UK: +5%
  - Canada: +4%
  - Australia: +3%
  - US: +2%
- **Application Status**:
  - Application Started: 70% base probability.
  - Documents Submitted: Minimum 50%.
- **Interaction Engagement**:
  - Each email/call contributes 1.5%, capped at 15%.

The total probability is calculated by:
1. Setting a base probability from the application status.
2. Adding bonuses from all factors.
3. Capping the final result at 100%.

---

## Project Structure
```
educonnect_dashboard/
├── app.py                # Main Flask application
├── database.py           # Database initialization and query functions
├── templates/            # HTML templates
│   ├── students.html     # Students page
│   ├── profile.html      # Student profile page
│   ├── analytics.html    # Analytics page
│   ├── applications.html # Applications page
│   ├── tasks.html        # Tasks management page
│   └── modals/           # Modal templates
│       └── log_interaction_modal.html
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css     # Custom styles
├── educonnect.db         # SQLite database
└── venv/                 # Virtual environment
```

---

## How to Run

### Prerequisites
- Python 3.8 or higher
- Flask and required dependencies

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/educonnect_dashboard.git
   cd educonnect_dashboard
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```bash
   python -c "from database import init_db; init_db()"
   ```

### Run the Application
Start the Flask development server:
```bash
python app.py
```

Access the application in your browser at:
```
http://127.0.0.1:5000
```

---

## User Manual

### **1. Navigation**
- Use the **sidebar menu** to navigate between sections:
  - **Dashboard**: Overview of key metrics.
  - **Students**: Manage student profiles and view conversion probabilities.
  - **Applications**: Track application statuses.
  - **Analytics**: Analyze trends and performance.
  - **Tasks**: Manage and assign tasks.

### **2. Adding a New Student**
1. Go to the **Students** page.
2. Click the **"Add New Student"** button.
3. Fill out the form in the modal:
   - Full Name
   - Email
   - Phone
   - Course of Study
   - Level of Study
4. Click **"Add Student"** to save.

### **3. Logging an Interaction**
1. Go to a student's profile.
2. Click **"Log Interaction"**.
3. Select the interaction type (e.g., call, email).
4. Add notes and submit.

### **4. Viewing Conversion Probability**
- Conversion probabilities are displayed as progress bars on the **Students** page.
- Colors indicate the likelihood:
  - **Green**: High probability (>70%)
  - **Yellow**: Medium probability (40-70%)
  - **Red**: Low probability (<40%)

### **5. Managing Tasks**
1. Navigate to the **Tasks** page.
2. View, add, or update tasks related to student applications.

---

## Future Enhancements
1. **Authentication**: Add user login/logout functionality for secure access.
2. **Advanced Analytics**: Provide detailed reports and visualizations.
3. **Search and Filters**: Add search and filter options for student records.
4. **Email Notifications**: Notify students or consultants about updates.
5. **Mobile Optimization**: Ensure the dashboard is fully responsive for mobile devices.

---

## Support
For issues or questions, please contact:
- **Email**: support@educonnect.com
- **GitHub**: [EduConnect Dashboard Repository](https://github.com/your-repo/educonnect_dashboard)
