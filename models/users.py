from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .database import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'lecturer', 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin_profile = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    lecturer_profile = db.relationship('Lecturer', backref='user', uselist=False, cascade="all, delete-orphan")
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    employee_no = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))

class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    staff_number = db.Column(db.String(50), unique=True, nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    
    # Relationships
    courses = db.relationship('Course', backref='lecturer', lazy=True)
    attendance_sessions = db.relationship('AttendanceSession', backref='lecturer', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    matric_number = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(10), nullable=False) # e.g. 100, 200, 300, 400, 500
    phone_number = db.Column(db.String(20))
    profile_pic = db.Column(db.String(255), default='default_profile.png')
    face_registered = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True, cascade="all, delete-orphan")
