import csv
import io
from datetime import datetime
import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response
from flask_login import login_required, current_user
from models import db, Course, Student, AttendanceSession, AttendanceRecord, Lecturer
from services import AIAnalyticsService

# Import openpyxl and reportlab for file exports
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

lecturer_bp = Blueprint('lecturer', __name__, url_prefix='/lecturer')

def check_lecturer():
    if current_user.role != 'lecturer':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('auth.login'))
    return None

def generate_session_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@lecturer_bp.route('/dashboard')
@login_required
def dashboard():
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    lecturer = current_user.lecturer_profile
    courses = Course.query.filter_by(lecturer_id=lecturer.id).all()
    course_ids = [c.id for c in courses]
    
    # Calculate stats
    total_courses = len(courses)
    active_session = AttendanceSession.query.filter(
        AttendanceSession.lecturer_id == lecturer.id,
        AttendanceSession.status == 'active'
    ).first()
    
    # AI Risk Analysis
    at_risk_students = []
    for course in courses:
        at_risk = AIAnalyticsService.get_course_risk_analysis(course.id)
        for student in at_risk:
            # Add course info
            student['course_code'] = course.course_code
            at_risk_students.append(student)
            
    # Calculate overall attendance rate for lecturer's classes
    sessions = AttendanceSession.query.filter(
        AttendanceSession.course_id.in_(course_ids) if course_ids else False,
        AttendanceSession.status == 'completed'
    ).all()
    
    total_records = 0
    present_records = 0
    if sessions:
        session_ids = [s.id for s in sessions]
        total_records = AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(session_ids)).count()
        present_records = AttendanceRecord.query.filter(
            AttendanceRecord.session_id.in_(session_ids),
            AttendanceRecord.status.in_(['present', 'late'])
        ).count()
        
    overall_rate = 100.0
    if total_records > 0:
        overall_rate = (present_records / total_records) * 100.0
        
    return render_template(
        'lecturer/dashboard.html',
        lecturer=lecturer,
        courses=courses,
        total_courses=total_courses,
        active_session=active_session,
        at_risk_students=at_risk_students,
        overall_rate=round(overall_rate, 2)
    )

@lecturer_bp.route('/session/start', methods=['GET', 'POST'])
@login_required
def start_session():
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    lecturer = current_user.lecturer_profile
    courses = Course.query.filter_by(lecturer_id=lecturer.id).all()
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        
        # Check if there is already an active session
        existing = AttendanceSession.query.filter_by(
            lecturer_id=lecturer.id,
            status='active'
        ).first()
        
        if existing:
            flash(f"You already have an active session for {existing.course.course_code}!", "warning")
            return redirect(url_for('lecturer.live_scan', session_id=existing.id))
            
        session_code = generate_session_code()
        
        new_session = AttendanceSession(
            course_id=course_id,
            lecturer_id=lecturer.id,
            status='active',
            session_code=session_code,
            session_date=datetime.utcnow().date()
        )
        db.session.add(new_session)
        db.session.commit()
        
        flash("Attendance session started successfully.", "success")
        return redirect(url_for('lecturer.live_scan', session_id=new_session.id))
        
    return render_template('lecturer/start_session.html', courses=courses)

@lecturer_bp.route('/session/live/<int:session_id>')
@login_required
def live_scan(session_id):
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    session = AttendanceSession.query.get_or_404(session_id)
    if session.lecturer_id != current_user.lecturer_profile.id:
        flash("Access denied.", "danger")
        return redirect(url_for('lecturer.dashboard'))
        
    if session.status != 'active':
        flash("This session has already ended.", "info")
        return redirect(url_for('lecturer.dashboard'))
        
    # Get all students enrolled in the course
    enrolled_students = session.course.students
    
    # Get current records in this session
    records = AttendanceRecord.query.filter_by(session_id=session.id).all()
    marked_student_ids = [r.student_id for r in records]
    
    return render_template(
        'lecturer/live_scan.html',
        session=session,
        enrolled_students=enrolled_students,
        marked_student_ids=marked_student_ids,
        records=records
    )

@lecturer_bp.route('/session/stop/<int:session_id>', methods=['POST'])
@login_required
def stop_session(session_id):
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    session = AttendanceSession.query.get_or_404(session_id)
    if session.lecturer_id != current_user.lecturer_profile.id:
        flash("Access denied.", "danger")
        return redirect(url_for('lecturer.dashboard'))
        
    session.status = 'completed'
    session.end_time = datetime.utcnow()
    
    # Automatically mark all non-marked students as "absent" for completeness
    enrolled_students = session.course.students
    marked_records = AttendanceRecord.query.filter_by(session_id=session.id).all()
    marked_student_ids = {r.student_id for r in marked_records}
    
    for s in enrolled_students:
        if s.id not in marked_student_ids:
            absent_record = AttendanceRecord(
                session_id=session.id,
                student_id=s.id,
                status='absent',
                verification_method='manual',
                confidence_score=0.0
            )
            db.session.add(absent_record)
            
            # Trigger AI check for this student to generate warnings
            AIAnalyticsService.check_and_generate_early_warnings(s.id)
            
    db.session.commit()
    flash("Attendance session completed. Absences have been recorded.", "success")
    return redirect(url_for('lecturer.reports'))

@lecturer_bp.route('/reports')
@login_required
def reports():
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    lecturer = current_user.lecturer_profile
    courses = Course.query.filter_by(lecturer_id=lecturer.id).all()
    course_ids = [c.id for c in courses]
    
    sessions = AttendanceSession.query.filter(
        AttendanceSession.course_id.in_(course_ids) if course_ids else False
    ).order_by(AttendanceSession.start_time.desc()).all()
    
    return render_template('lecturer/reports.html', courses=courses, sessions=sessions)

# ==========================================
# EXPORT API MODULE
# ==========================================

@lecturer_bp.route('/reports/export/<string:fmt>/<int:session_id>')
@login_required
def export_report(fmt, session_id):
    auth_check = check_lecturer()
    if auth_check: return auth_check
    
    session = AttendanceSession.query.get_or_404(session_id)
    if session.lecturer_id != current_user.lecturer_profile.id:
        return "Access Denied", 403
        
    records = AttendanceRecord.query.filter_by(session_id=session.id).all()
    
    data = []
    for r in records:
        data.append({
            'Student Name': r.student.full_name,
            'Matric Number': r.student.matric_number,
            'Department': r.student.department,
            'Time Marked': r.time_marked.strftime('%Y-%m-%d %H:%M:%S') if r.time_marked else 'N/A',
            'Verification Method': r.verification_method.replace('_', ' ').title(),
            'Confidence (%)': f"{round(r.confidence_score * 100, 1)}%" if r.status == 'present' else 'N/A',
            'Status': r.status.upper()
        })
        
    df = pd.DataFrame(data)
    
    # 1. CSV EXPORT
    if fmt == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=attendance_{session.course.course_code}_{session.session_date}.csv"
        return response
        
    # 2. EXCEL EXPORT
    elif fmt == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Attendance', index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"attendance_{session.course.course_code}_{session.session_date}.xlsx"
        )
        
    # 3. PDF EXPORT
    elif fmt == 'pdf':
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        
        # Custom Title Style
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=10
        )
        
        meta_style = ParagraphStyle(
            name='MetaStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=20
        )
        
        elements = []
        
        # Add headers
        elements.append(Paragraph(f"Smart Attendance System Report", title_style))
        elements.append(Paragraph(
            f"<b>Course:</b> {session.course.course_code} - {session.course.course_title}<br/>"
            f"<b>Lecturer:</b> Dr. {session.lecturer.full_name}<br/>"
            f"<b>Date:</b> {session.session_date.strftime('%B %d, %Y')}<br/>"
            f"<b>Time:</b> {session.start_time.strftime('%I:%M %p')} - "
            f"{session.end_time.strftime('%I:%M %p') if session.end_time else 'Active'}",
            meta_style
        ))
        
        # Add table
        table_data = [[
            Paragraph("<b>Student Name</b>", styles['Normal']),
            Paragraph("<b>Matric No</b>", styles['Normal']),
            Paragraph("<b>Time Marked</b>", styles['Normal']),
            Paragraph("<b>Method</b>", styles['Normal']),
            Paragraph("<b>Status</b>", styles['Normal'])
        ]]
        
        for r in records:
            table_data.append([
                Paragraph(r.student.full_name, styles['Normal']),
                Paragraph(r.student.matric_number, styles['Normal']),
                Paragraph(r.time_marked.strftime('%I:%M %p') if r.time_marked else '-', styles['Normal']),
                Paragraph(r.verification_method.replace('_', ' ').title(), styles['Normal']),
                Paragraph(f"<font color='{'green' if r.status == 'present' else 'red'}'><b>{r.status.upper()}</b></font>", styles['Normal'])
            ])
            
        t = Table(table_data, colWidths=[180, 100, 100, 100, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
        ]))
        
        elements.append(t)
        doc.build(elements)
        output.seek(0)
        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"attendance_{session.course.course_code}_{session.session_date}.pdf"
        )
        
    return "Format not supported", 400
