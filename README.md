# Smart Student Attendance System Using Facial Recognition

> **Final Year Computer Science Project** — University of Technology, 2026

A modern, professional, university-grade web application for automated student attendance tracking using real-time facial recognition powered by OpenCV LBPH, Python Flask, and intelligent AI analytics.

---

## Technology Stack

| Layer        | Technology                                   |
|-------------|----------------------------------------------|
| **Backend**     | Python 3.9, Flask 2.3, Flask-SQLAlchemy      |
| **Database**    | SQLite (default) / MySQL (configurable)      |
| **Face Engine** | OpenCV Haar Cascades + LBPH Face Recognizer  |
| **Frontend**    | HTML5, CSS3, Bootstrap 5, JavaScript          |
| **Charts**      | Chart.js 4.x                                 |
| **AI Module**   | Custom trend analyzer & risk predictor        |
| **Exports**     | PDF (ReportLab), Excel (openpyxl), CSV        |

---

## Quick Start

```bash
# 1. Clone or extract the project
cd "student system"

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Default Login Credentials

| Role       | Username    | Password      |
|-----------|------------|---------------|
| Admin      | `admin`     | `admin123`    |
| Lecturer   | `lecturer1` | `lecturer123` |
| Lecturer   | `lecturer2` | `lecturer123` |
| Student    | `student1`  | `student123`  |
| Student    | `student2`  | `student123`  |

---

## System Modules

1. **Authentication System** — Role-based login (Admin/Lecturer/Student), password recovery
2. **Admin Dashboard** — KPI stats, Chart.js analytics, dark mode glassmorphic UI
3. **Student Management** — Full CRUD with search/filter, profile photos
4. **Facial Registration** — Webcam capture of 100 samples, LBPH training with progress indicator
5. **Smart Attendance** — Real-time face scanning, automatic attendance recording
6. **Attendance Analytics** — Daily/Weekly/Monthly trend charts, department comparison
7. **Lecturer Portal** — Start/stop sessions, view records, AI risk analysis
8. **Student Portal** — Attendance history, per-course stats, AI early warnings
9. **Report Generation** — Export PDF, Excel, CSV for each session
10. **AI Prediction** — At-risk student detection, predicted final attendance rates

---

## Project Structure

```
student_system/
├── app.py                    # Flask entry point
├── config.py                 # Configuration (DB URI, paths)
├── database.sql              # MySQL schema reference
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── models/                   # SQLAlchemy ORM models
│   ├── database.py           # DB instance
│   ├── users.py              # User, Admin, Lecturer, Student
│   ├── courses.py            # Course, enrollment
│   └── attendance.py         # Sessions, Records, Notifications
│
├── controllers/              # Flask Blueprint routes
│   ├── auth.py               # Login/logout/recovery
│   ├── admin.py              # Admin CRUD operations
│   ├── lecturer.py           # Session mgmt, exports
│   ├── student.py            # Dashboard, face registration
│   └── attendance.py         # Real-time scan API
│
├── services/                 # Business logic engines
│   ├── face_rec.py           # OpenCV face detection/recognition
│   └── ai_analytics.py       # At-risk prediction & warnings
│
├── static/
│   ├── css/style.css         # Glassmorphic dark theme
│   ├── js/
│   │   ├── main.js           # General utilities
│   │   ├── charts_dashboard.js  # Chart.js builders
│   │   ├── face_reg.js       # Webcam capture controller
│   │   └── attendance_scan.js   # Live scan controller
│   └── uploads/
│       ├── profile_pics/     # Student photos
│       └── face_dataset/     # Training face samples
│
└── templates/                # Jinja2 HTML templates
    ├── base.html             # Master layout with sidebar
    ├── index.html            # Portal selection landing page
    ├── auth/                 # Login, recovery
    ├── admin/                # Dashboard, students, lecturers, courses
    ├── lecturer/             # Dashboard, scan, reports
    └── student/              # Dashboard, face register, profile
```

---

## Switching to MySQL

Edit `config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/student_attendance_db'
```

Then install the MySQL driver:
```bash
pip install pymysql
```

Import the schema from `database.sql` if you want the MySQL-specific DDL.

---

© 2026 Smart Student Attendance System. Final Year CS Project.
# student-system
# student-system
