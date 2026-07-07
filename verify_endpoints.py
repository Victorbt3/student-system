"""
Smart Student Attendance System – Integration Test Suite
Uses Flask's built-in test client (no external server required).
Run with:  python verify_endpoints.py   or   pytest verify_endpoints.py
"""
import unittest
import sys
import os

# ── Make sure the project root is importable ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db as _db, User, Student, Lecturer, Course, \
    AttendanceSession, AttendanceRecord, Admin
from datetime import datetime
import random, string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _login(client, username, password, role):
    """POST to /login and follow redirect."""
    return client.post(
        '/login',
        data={'username': username, 'password': password, 'role': role},
        follow_redirects=True
    )


def _logout(client):
    return client.get('/logout', follow_redirects=True)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------
class TestStudentAttendanceSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a fresh Flask app wired to an in-memory SQLite DB."""
        cls.app = create_app()
        cls.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(
                os.path.dirname(__file__), 'attendance.db'),
            'SECRET_KEY': 'test-secret',
        })
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def setUp(self):
        """Fresh test client before every test (no lingering sessions)."""
        self.client = self.app.test_client()
        self.client.testing = True

    def tearDown(self):
        """Log out after every test so session cookies don't bleed."""
        _logout(self.client)

    # ------------------------------------------------------------------ #
    #  1. Landing page
    # ------------------------------------------------------------------ #
    def test_01_landing_page(self):
        """Landing page loads and contains 'Smart Attendance'."""
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        self.assertIn('Smart Attendance', body)

    # ------------------------------------------------------------------ #
    #  2. Login page
    # ------------------------------------------------------------------ #
    def test_02_login_page(self):
        """Login page loads and contains the word 'Login'."""
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Login', r.data.decode())

    # ------------------------------------------------------------------ #
    #  3. Protected route redirects unauthenticated users
    # ------------------------------------------------------------------ #
    def test_03_admin_dashboard_requires_login(self):
        """Admin dashboard redirects unauthenticated users to /login."""
        r = self.client.get('/admin/dashboard')          # do NOT follow redirect
        self.assertEqual(r.status_code, 302)
        location = r.headers.get('Location', '')
        self.assertIn('/login', location)

    # ------------------------------------------------------------------ #
    #  4. Admin login + dashboard
    # ------------------------------------------------------------------ #
    def test_04_admin_login_and_dashboard(self):
        """Admin can log in and see Admin Dashboard with their name."""
        r = _login(self.client, 'admin', 'admin123', 'admin')
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        self.assertIn('Admin Dashboard', body)

        # Admin full name ('Prof. Albert Einstein') should appear in sidebar header
        self.assertIn('Albert Einstein', body)

        # Direct GET also works
        r2 = self.client.get('/admin/dashboard')
        self.assertEqual(r2.status_code, 200)
        self.assertIn('Admin Dashboard', r2.data.decode())

    # ------------------------------------------------------------------ #
    #  5. Lecturer login + dashboard
    # ------------------------------------------------------------------ #
    def test_05_lecturer_login_and_dashboard(self):
        """Lecturer can log in and see Lecturer Dashboard with their name."""
        r = _login(self.client, 'lecturer1', 'lecturer123', 'lecturer')
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        self.assertIn('Lecturer Dashboard', body)
        # 'Dr. Richard Smith' appears somewhere on the page
        self.assertIn('Richard Smith', body)

        # Direct GET
        r2 = self.client.get('/lecturer/dashboard')
        self.assertEqual(r2.status_code, 200)
        self.assertIn('Richard Smith', r2.data.decode())

    # ------------------------------------------------------------------ #
    #  6. Student login + dashboard
    # ------------------------------------------------------------------ #
    def test_06_student_login_and_dashboard(self):
        """Student can log in and see their attendance portal."""
        r = _login(self.client, 'student1', 'student123', 'student')
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        # header_title block contains 'My Attendance Portal'
        self.assertIn('My Attendance Portal', body)
        # student's full name on page
        self.assertIn('John Doe', body)

        # Direct GET
        r2 = self.client.get('/student/dashboard')
        self.assertEqual(r2.status_code, 200)
        self.assertIn('John Doe', r2.data.decode())

    # ------------------------------------------------------------------ #
    #  7. Admin – add student with course enrollment
    # ------------------------------------------------------------------ #
    def test_07_admin_manage_student_course_enrollment(self):
        """Admin can add a new student and enroll them in courses."""
        _login(self.client, 'admin', 'admin123', 'admin')

        # Fetch existing course IDs
        with self.app.app_context():
            courses = Course.query.all()
            self.assertTrue(len(courses) >= 2,
                            "Need at least 2 courses in DB for this test")
            c1_id = courses[0].id
            c2_id = courses[1].id

        payload = {
            'username':    'testenrollstudent',
            'email':       'testcs@enroll.edu',
            'password':    'test1234',
            'matric_number': 'TST/2026/888',
            'full_name':   'Test Enroll Student',
            'faculty':     'Science and Technology',
            'department':  'Computer Science',
            'level':       '400',
            'phone_number': '+234801000111',
            'course_ids':  [c1_id, c2_id],
        }
        r = self.client.post('/admin/students', data=payload,
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        with self.app.app_context():
            student = Student.query.filter_by(
                matric_number='TST/2026/888').first()
            self.assertIsNotNone(student, "Newly added student not found in DB")

            enrolled_ids = [c.id for c in student.courses.all()]
            self.assertIn(c1_id, enrolled_ids)
            self.assertIn(c2_id, enrolled_ids)

            # Clean up
            _db.session.delete(student.user)
            _db.session.commit()

    # ------------------------------------------------------------------ #
    #  8. Admin – attendance CRUD (add, edit, delete)
    # ------------------------------------------------------------------ #
    def test_08_admin_attendance_crud(self):
        """Admin can view, add, edit and delete attendance records."""
        _login(self.client, 'admin', 'admin123', 'admin')

        # --- GET attendance page ---
        r = self.client.get('/admin/attendance')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Attendance Records', r.data.decode())

        # --- find or create a session + student in DB ---
        with self.app.app_context():
            student = Student.query.first()
            sess = AttendanceSession.query.first()
            if not sess:
                course   = Course.query.first()
                lecturer = Lecturer.query.first()
                code = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=6))
                sess = AttendanceSession(
                    course_id    = course.id,
                    lecturer_id  = lecturer.id,
                    session_date = datetime.utcnow().date(),
                    session_code = code,
                    status       = 'active'
                )
                _db.session.add(sess)
                _db.session.commit()

            student_id = student.id
            session_id = sess.id

            # Remove any pre-existing record for this pair so ADD creates fresh
            old = AttendanceRecord.query.filter_by(
                session_id=session_id,
                student_id=student_id
            ).first()
            if old:
                _db.session.delete(old)
                _db.session.commit()

        # --- ADD ---
        r = self.client.post('/admin/attendance/add', data={
            'student_id': student_id,
            'session_id': session_id,
            'status':     'late',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        with self.app.app_context():
            record = AttendanceRecord.query.filter_by(
                session_id=session_id,
                student_id=student_id
            ).first()
            self.assertIsNotNone(record, "Record not created by ADD route")
            self.assertEqual(record.status, 'late')
            record_id = record.id

        # --- EDIT ---
        r = self.client.post(f'/admin/attendance/edit/{record_id}', data={
            'status':              'present',
            'verification_method': 'manual',
            'confidence_score':    '0.95',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        with self.app.app_context():
            rec = _db.session.get(AttendanceRecord, record_id)
            self.assertIsNotNone(rec)
            self.assertEqual(rec.status, 'present')
            self.assertAlmostEqual(rec.confidence_score, 0.95, places=2)

        # --- DELETE ---
        r = self.client.post(f'/admin/attendance/delete/{record_id}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        with self.app.app_context():
            deleted = _db.session.get(AttendanceRecord, record_id)
            self.assertIsNone(deleted, "Record not deleted")


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print('Running Smart Attendance integration tests...\n')
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None          # keep our numeric ordering
    suite = loader.loadTestsFromTestCase(TestStudentAttendanceSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
