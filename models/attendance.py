from datetime import datetime
from .database import db

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id', ondelete='CASCADE'), nullable=False)
    session_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active') # 'active', 'completed'
    session_code = db.Column(db.String(10), unique=True, nullable=False)
    
    # Relationships
    records = db.relationship('AttendanceRecord', backref='session', lazy=True, cascade="all, delete-orphan")

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    __table_args__ = (db.UniqueConstraint('session_id', 'student_id', name='unique_session_student'),)
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    time_marked = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present') # 'present', 'absent', 'late'
    verification_method = db.Column(db.String(30), default='face_recognition') # 'face_recognition', 'manual'
    confidence_score = db.Column(db.Float, default=1.0)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
