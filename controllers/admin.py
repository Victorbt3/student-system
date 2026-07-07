import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Admin, Lecturer, Student, Course, AttendanceSession, AttendanceRecord
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def check_admin():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))
    return None

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    # Calculate KPIs
    total_students = Student.query.count()
    total_lecturers = Lecturer.query.count()
    total_courses = Course.query.count()
    
    active_sessions = AttendanceSession.query.filter_by(status='active').count()
    
    # Global attendance rate
    completed_sessions = AttendanceSession.query.filter_by(status='completed').all()
    total_records = AttendanceRecord.query.count()
    present_records = AttendanceRecord.query.filter_by(status='present').count() + \
                      AttendanceRecord.query.filter_by(status='late').count()
                      
    attendance_rate = 100.0
    if total_records > 0:
        attendance_rate = (present_records / total_records) * 100.0
        
    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_lecturers=total_lecturers,
        total_courses=total_courses,
        active_sessions=active_sessions,
        attendance_rate=round(attendance_rate, 2)
    )

# ==========================================
# STUDENT CRUD
# ==========================================

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    if request.method == 'POST':
        # Add new student
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password', 'student123') # default password
        
        matric_number = request.form.get('matric_number')
        full_name = request.form.get('full_name')
        faculty = request.form.get('faculty')
        department = request.form.get('department')
        level = request.form.get('level')
        phone_number = request.form.get('phone_number')
        
        # Profile Picture Upload
        profile_pic_filename = 'default_profile.png'
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            filename = secure_filename(f"{matric_number.replace('/', '_')}_{file.filename}")
            file.save(os.path.join(Config.PROFILE_FOLDER, filename))
            profile_pic_filename = filename
            
        # Check duplicate
        if User.query.filter_by(username=username).first() or Student.query.filter_by(matric_number=matric_number).first():
            flash('Username or Matric Number already exists!', 'danger')
            return redirect(url_for('admin.students'))
            
        # Create User
        user = User(username=username, email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.flush() # get user ID
        
        # Create Student
        student = Student(
            user_id=user.id,
            matric_number=matric_number,
            full_name=full_name,
            faculty=faculty,
            department=department,
            level=level,
            phone_number=phone_number,
            profile_pic=profile_pic_filename
        )
        db.session.add(student)
        
        # Enroll in selected courses
        course_ids = request.form.getlist('course_ids')
        for c_id in course_ids:
            c = Course.query.get(c_id)
            if c:
                student.courses.append(c)
                
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('admin.students'))
        
    students_list = Student.query.all()
    courses_list = Course.query.all()
    return render_template('admin/students.html', students=students_list, courses=courses_list)

@admin_bp.route('/students/edit/<int:id>', methods=['POST'])
@login_required
def edit_student(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    student = Student.query.get(id)
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('admin.students'))
        
    # Update Student profile fields
    student.full_name = request.form.get('full_name')
    student.faculty = request.form.get('faculty')
    student.department = request.form.get('department')
    student.level = request.form.get('level')
    student.phone_number = request.form.get('phone_number')
    student.user.email = request.form.get('email')
    
    # Profile picture
    file = request.files.get('profile_pic')
    if file and file.filename != '':
        filename = secure_filename(f"{student.matric_number.replace('/', '_')}_{file.filename}")
        file.save(os.path.join(Config.PROFILE_FOLDER, filename))
        student.profile_pic = filename
        
    # Update course enrollment
    # Clear previous courses safely
    for c in student.courses.all():
        student.courses.remove(c)
    # Add newly selected courses
    course_ids = request.form.getlist('course_ids')
    for c_id in course_ids:
        c = Course.query.get(c_id)
        if c:
            student.courses.append(c)
            
    db.session.commit()
    flash('Student records updated successfully!', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    student = Student.query.get(id)
    if student:
        user = student.user
        db.session.delete(user) # Will cascade delete the student profile
        db.session.commit()
        flash('Student deleted successfully.', 'success')
    else:
        flash('Student not found.', 'danger')
    return redirect(url_for('admin.students'))


# ==========================================
# LECTURER CRUD
# ==========================================

@admin_bp.route('/lecturers', methods=['GET', 'POST'])
@login_required
def lecturers():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password', 'lecturer123')
        
        staff_number = request.form.get('staff_number')
        full_name = request.form.get('full_name')
        faculty = request.form.get('faculty')
        department = request.form.get('department')
        phone_number = request.form.get('phone_number')
        
        # Check duplicate
        if User.query.filter_by(username=username).first() or Lecturer.query.filter_by(staff_number=staff_number).first():
            flash('Username or Staff Number already exists!', 'danger')
            return redirect(url_for('admin.lecturers'))
            
        # Create User
        user = User(username=username, email=email, role='lecturer')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create Lecturer
        lecturer = Lecturer(
            user_id=user.id,
            staff_number=staff_number,
            full_name=full_name,
            faculty=faculty,
            department=department,
            phone_number=phone_number
        )
        db.session.add(lecturer)
        db.session.commit()
        flash('Lecturer registered successfully.', 'success')
        return redirect(url_for('admin.lecturers'))
        
    lecturers_list = Lecturer.query.all()
    return render_template('admin/lecturers.html', lecturers=lecturers_list)

@admin_bp.route('/lecturers/edit/<int:id>', methods=['POST'])
@login_required
def edit_lecturer(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    lecturer = Lecturer.query.get(id)
    if not lecturer:
        flash('Lecturer not found!', 'danger')
        return redirect(url_for('admin.lecturers'))
        
    lecturer.full_name = request.form.get('full_name')
    lecturer.faculty = request.form.get('faculty')
    lecturer.department = request.form.get('department')
    lecturer.phone_number = request.form.get('phone_number')
    lecturer.user.email = request.form.get('email')
    
    db.session.commit()
    flash('Lecturer records updated.', 'success')
    return redirect(url_for('admin.lecturers'))

@admin_bp.route('/lecturers/delete/<int:id>', methods=['POST'])
@login_required
def delete_lecturer(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    lecturer = Lecturer.query.get(id)
    if lecturer:
        db.session.delete(lecturer.user) # Will cascade delete
        db.session.commit()
        flash('Lecturer deleted successfully.', 'success')
    else:
        flash('Lecturer not found.', 'danger')
    return redirect(url_for('admin.lecturers'))


# ==========================================
# COURSE CRUD
# ==========================================

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_title = request.form.get('course_title')
        department = request.form.get('department')
        unit = request.form.get('unit', 3)
        lecturer_id = request.form.get('lecturer_id')
        
        # Check duplicate
        if Course.query.filter_by(course_code=course_code).first():
            flash('Course Code already exists!', 'danger')
            return redirect(url_for('admin.courses'))
            
        course = Course(
            course_code=course_code,
            course_title=course_title,
            department=department,
            unit=unit,
            lecturer_id=lecturer_id
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully.', 'success')
        return redirect(url_for('admin.courses'))
        
    courses_list = Course.query.all()
    lecturers_list = Lecturer.query.all()
    students_list = Student.query.all()
    return render_template('admin/courses.html', courses=courses_list, lecturers=lecturers_list, students=students_list)

@admin_bp.route('/courses/edit/<int:id>', methods=['POST'])
@login_required
def edit_course(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    course = Course.query.get(id)
    if not course:
        flash('Course not found!', 'danger')
        return redirect(url_for('admin.courses'))
        
    course.course_title = request.form.get('course_title')
    course.department = request.form.get('department')
    course.unit = request.form.get('unit')
    course.lecturer_id = request.form.get('lecturer_id')
    
    db.session.commit()
    flash('Course updated successfully.', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/courses/delete/<int:id>', methods=['POST'])
@login_required
def delete_course(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    course = Course.query.get(id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted.', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/courses/enroll/<int:id>', methods=['POST'])
@login_required
def enroll_students(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    course = Course.query.get(id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found.'}), 404
        
    student_ids = request.form.getlist('student_ids')
    
    # Clear previous students and assign new list
    students_to_enroll = Student.query.filter(Student.id.in_(student_ids)).all()
    course.students = students_to_enroll
    db.session.commit()
    
    flash(f"Updated student enrollments for {course.course_code}.", "success")
    return redirect(url_for('admin.courses'))


# ==========================================
# ATTENDANCE RECORDS CRUD (NEW)
# ==========================================

@admin_bp.route('/attendance', methods=['GET'])
@login_required
def attendance():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    from datetime import datetime
    
    # Query filters
    course_id = request.args.get('course_id', type=int)
    status_filter = request.args.get('status')
    session_date_str = request.args.get('session_date')
    
    # Base query
    query = AttendanceRecord.query
    
    if course_id:
        query = query.join(AttendanceSession).filter(AttendanceSession.course_id == course_id)
        
    if status_filter:
        query = query.filter(AttendanceRecord.status == status_filter)
        
    if session_date_str:
        try:
            s_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
            query = query.join(AttendanceSession).filter(db.func.date(AttendanceSession.session_date) == s_date)
        except ValueError:
            pass
            
    # Sort and load records
    records_list = query.order_by(AttendanceRecord.time_marked.desc()).all()
    
    # Get helpers for modals / dropdowns
    courses_list = Course.query.all()
    students_list = Student.query.all()
    sessions_list = AttendanceSession.query.order_by(AttendanceSession.start_time.desc()).all()
    
    return render_template(
        'admin/attendance.html',
        records=records_list,
        courses=courses_list,
        students=students_list,
        sessions=sessions_list,
        selected_course=course_id,
        selected_status=status_filter,
        selected_date=session_date_str
    )

@admin_bp.route('/attendance/add', methods=['POST'])
@login_required
def add_attendance():
    auth_check = check_admin()
    if auth_check: return auth_check
    
    student_id = request.form.get('student_id', type=int)
    session_id = request.form.get('session_id', type=int)
    status = request.form.get('status', 'present')
    
    if not student_id or not session_id:
        flash('Student and Session are required.', 'danger')
        return redirect(url_for('admin.attendance'))
        
    session_obj = AttendanceSession.query.get(session_id)
    student_obj = Student.query.get(student_id)
    
    if not session_obj or not student_obj:
        flash('Invalid session or student.', 'danger')
        return redirect(url_for('admin.attendance'))
        
    # Check duplicate
    existing = AttendanceRecord.query.filter_by(session_id=session_id, student_id=student_id).first()
    if existing:
        existing.status = status
        existing.verification_method = 'manual'
        existing.confidence_score = 1.0
        db.session.commit()
        flash(f"Updated attendance for {student_obj.full_name}.", "success")
    else:
        new_record = AttendanceRecord(
            session_id=session_id,
            student_id=student_id,
            status=status,
            verification_method='manual',
            confidence_score=1.0
        )
        db.session.add(new_record)
        db.session.commit()
        flash(f"Manual attendance marked for {student_obj.full_name}.", "success")
        
    return redirect(url_for('admin.attendance'))

@admin_bp.route('/attendance/edit/<int:id>', methods=['POST'])
@login_required
def edit_attendance(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    record = AttendanceRecord.query.get(id)
    if not record:
        flash('Attendance record not found.', 'danger')
        return redirect(url_for('admin.attendance'))
        
    status = request.form.get('status')
    verification_method = request.form.get('verification_method', record.verification_method)
    try:
        confidence = float(request.form.get('confidence_score', record.confidence_score))
    except ValueError:
        confidence = record.confidence_score
        
    record.status = status
    record.verification_method = verification_method
    record.confidence_score = confidence
    
    db.session.commit()
    flash('Attendance record updated successfully.', 'success')
    return redirect(url_for('admin.attendance'))

@admin_bp.route('/attendance/delete/<int:id>', methods=['POST'])
@login_required
def delete_attendance(id):
    auth_check = check_admin()
    if auth_check: return auth_check
    
    record = AttendanceRecord.query.get(id)
    if record:
        db.session.delete(record)
        db.session.commit()
        flash('Attendance record deleted.', 'success')
    else:
        flash('Record not found.', 'danger')
        
    return redirect(url_for('admin.attendance'))

