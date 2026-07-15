import os
import base64
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Student, AttendanceRecord, AttendanceSession, Course, Notification, User
from services import FaceRecognitionService
from config import Config

student_bp = Blueprint('student', __name__, url_prefix='/student')

# Helper to initialize FaceRecognitionService dynamically using config values
def get_face_rec_service():
    return FaceRecognitionService(Config.UPLOAD_FOLDER)

def check_student():
    if current_user.role != 'student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))
    return None

@student_bp.route('/dashboard')
@login_required
def dashboard():
    auth_check = check_student()
    if auth_check: return auth_check
    
    student = current_user.student_profile
    courses = student.courses.all()
    
    # Calculate stats
    total_courses = len(courses)
    
    # Calculate attendance rates per course
    course_stats = []
    total_attended = 0
    total_sessions_all_courses = 0
    
    for course in courses:
        sessions = AttendanceSession.query.filter_by(course_id=course.id, status='completed').all()
        total_sessions = len(sessions)
        
        if total_sessions > 0:
            session_ids = [s.id for s in sessions]
            records = AttendanceRecord.query.filter(
                AttendanceRecord.session_id.in_(session_ids),
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.status.in_(['present', 'late'])
            ).all()
            
            attended = len(records)
            rate = (attended / total_sessions) * 100.0
            
            total_attended += attended
            total_sessions_all_courses += total_sessions
        else:
            attended = 0
            rate = 100.0 # No classes held yet
            
        course_stats.append({
            'id': course.id,
            'code': course.course_code,
            'title': course.course_title,
            'lecturer': course.lecturer.full_name,
            'attended': attended,
            'total': total_sessions,
            'rate': round(rate, 1)
        })
        
    overall_rate = 100.0
    if total_sessions_all_courses > 0:
        overall_rate = (total_attended / total_sessions_all_courses) * 100.0
        
    # Notifications box
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Recent Attendance History
    recent_records = AttendanceRecord.query.filter_by(student_id=student.id).order_by(AttendanceRecord.time_marked.desc()).limit(10).all()
    
    return render_template(
        'student/dashboard.html',
        student=student,
        course_stats=course_stats,
        total_courses=total_courses,
        overall_rate=round(overall_rate, 2),
        notifications=notifications,
        recent_records=recent_records
    )

@student_bp.route('/register-face')
@login_required
def register_face():
    auth_check = check_student()
    if auth_check: return auth_check
    
    student = current_user.student_profile
    return render_template('student/register_face.html', student=student)

@student_bp.route('/register-face/capture', methods=['POST'])
@login_required
def capture_face():
    auth_check = check_student()
    if auth_check: return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    student = current_user.student_profile
    data = request.json
    
    if not data or 'frame' not in data or 'sample_num' not in data:
        return jsonify({'success': False, 'message': 'Invalid request parameters'}), 400
        
    frame_b64 = data['frame']
    sample_num = data['sample_num']
    
    try:
        # Decode base64 image
        if ',' in frame_b64:
            frame_b64 = frame_b64.split(',')[1]
            
        img_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'Failed to decode image'}), 400
            
        # Save face sample
        face_service = get_face_rec_service()
        success, msg = face_service.save_face_sample(img, student.matric_number, sample_num)
        
        if success:
            return jsonify({'success': True, 'message': f"Captured sample {sample_num}/100."})
        else:
            return jsonify({'success': False, 'message': msg})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@student_bp.route('/register-face/train', methods=['POST'])
@login_required
def train_face():
    auth_check = check_student()
    if auth_check: return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    student = current_user.student_profile
    
    try:
        # Setup student ID mapping. LBPH needs numerical IDs.
        # We query all students who have folders in the face_dataset folder
        # and map their folder name (escaped matric number) to their Student DB ID.
        students = Student.query.all()
        id_mappings = {}
        for s in students:
            folder_name = s.matric_number.replace('/', '_')
            id_mappings[folder_name] = s.id
            
        face_service = get_face_rec_service()
        success, msg = face_service.train_model(id_mappings)
        
        if success:
            # Mark face as registered in DB
            student.face_registered = True
            student.registered_at = datetime.utcnow()
            db.session.commit()
            
            # Send notification
            notification = Notification(
                user_id=current_user.id,
                title="Facial Registration Successful",
                message="Your face has been successfully registered and trained in the Smart Attendance System.",
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'message': msg}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    auth_check = check_student()
    if auth_check: return auth_check
    
    student = current_user.student_profile
    
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone_number')
        password = request.form.get('password')
        
        # Check duplicate email
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            flash("This email address is already in use by another account.", "danger")
            return redirect(url_for('student.profile'))
            
        # Update user
        current_user.email = email
        student.phone_number = phone
        
        # Update password if provided
        if password and password.strip() != '':
            current_user.set_password(password)
            
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('student.profile'))
        
    return render_template('student/profile.html', student=student)

@student_bp.route('/notification/read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    if notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})
