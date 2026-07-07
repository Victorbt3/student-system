from .database import db

# Association Table for Student-Course enrollment (Many-to-Many)
student_courses = db.Table('student_courses',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True)
)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(15), unique=True, nullable=False)
    course_title = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.Integer, default=3)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    students = db.relationship('Student', secondary=student_courses, backref=db.backref('courses', lazy='dynamic'))
    sessions = db.relationship('AttendanceSession', backref='course', lazy=True, cascade="all, delete-orphan")
