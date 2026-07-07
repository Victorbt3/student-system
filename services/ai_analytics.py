from models import db, Student, Course, AttendanceSession, AttendanceRecord, Notification
from datetime import datetime

class AIAnalyticsService:
    @staticmethod
    def get_student_course_attendance(student_id, course_id):
        """
        Calculates detailed attendance metrics for a specific student in a course.
        """
        # Fetch all completed sessions for this course
        sessions = AttendanceSession.query.filter_by(course_id=course_id, status='completed').all()
        total_sessions = len(sessions)
        
        if total_sessions == 0:
            return {
                'total_sessions': 0,
                'attended_sessions': 0,
                'absent_sessions': 0,
                'attendance_rate': 100.0,
                'status': 'Good Standing',
                'predicted_final_rate': 100.0,
                'trend': 'Stable'
            }
            
        session_ids = [s.id for s in sessions]
        
        # Fetch student's records for these sessions
        records = AttendanceRecord.query.filter(
            AttendanceRecord.session_id.in_(session_ids),
            AttendanceRecord.student_id == student_id
        ).all()
        
        attended = sum(1 for r in records if r.status in ['present', 'late'])
        absent = total_sessions - attended
        
        attendance_rate = (attended / total_sessions) * 100.0
        
        # Calculate recent trend (last 4 sessions)
        # Sort sessions by date/time to get the order
        sessions_sorted = sorted(sessions, key=lambda s: s.start_time)
        last_sessions = sessions_sorted[-4:]
        last_session_ids = [s.id for s in last_sessions]
        
        last_records = AttendanceRecord.query.filter(
            AttendanceRecord.session_id.in_(last_session_ids),
            AttendanceRecord.student_id == student_id
        ).all()
        
        last_records_map = {r.session_id: r.status for r in last_records}
        
        # Build binary sequence of presence (1=present/late, 0=absent)
        presence_sequence = []
        for s in last_sessions:
            status = last_records_map.get(s.id, 'absent')
            presence_sequence.append(1 if status in ['present', 'late'] else 0)
            
        # Analyze trend
        if len(presence_sequence) >= 2:
            recent_rate = sum(presence_sequence) / len(presence_sequence)
            overall_diff = recent_rate - (attendance_rate / 100.0)
            if overall_diff < -0.15:
                trend = 'Declining'
            elif overall_diff > 0.15:
                trend = 'Improving'
            else:
                trend = 'Stable'
        else:
            trend = 'Stable'
            
        # Predict final attendance rate
        # Assume a standard 15-week semester (15 sessions total)
        total_semester_sessions = 15
        remaining_sessions = max(0, total_semester_sessions - total_sessions)
        
        # If trend is declining, project future attendance using recent rate, otherwise use overall rate
        projection_rate = (sum(presence_sequence) / len(presence_sequence)) if len(presence_sequence) >= 3 else (attendance_rate / 100.0)
        
        predicted_future_attendance = remaining_sessions * projection_rate
        predicted_final_attended = attended + predicted_future_attendance
        predicted_final_rate = (predicted_final_attended / total_semester_sessions) * 100.0
        predicted_final_rate = min(100.0, max(0.0, predicted_final_rate))
        
        # Classify risk status
        # Under university regulations, attendance < 75% is critical (fails to sit for exams)
        if attendance_rate < 60.0 or (len(presence_sequence) >= 3 and sum(presence_sequence[-3:]) == 0):
            risk_status = 'Critical'
        elif attendance_rate < 75.0 or predicted_final_rate < 75.0:
            risk_status = 'Warning'
        else:
            risk_status = 'Good Standing'
            
        return {
            'total_sessions': total_sessions,
            'attended_sessions': attended,
            'absent_sessions': absent,
            'attendance_rate': round(attendance_rate, 2),
            'status': risk_status,
            'predicted_final_rate': round(predicted_final_rate, 2),
            'trend': trend,
            'recent_history': presence_sequence
        }

    @staticmethod
    def get_course_risk_analysis(course_id):
        """
        Runs prediction analytics on all students enrolled in a course.
        Returns a list of students flagged as At Risk or Critical.
        """
        course = Course.query.get(course_id)
        if not course:
            return []
            
        at_risk_list = []
        
        for student in course.students:
            analysis = AIAnalyticsService.get_student_course_attendance(student.id, course_id)
            if analysis['status'] in ['Warning', 'Critical']:
                at_risk_list.append({
                    'student_id': student.id,
                    'name': student.full_name,
                    'matric': student.matric_number,
                    'attendance_rate': analysis['attendance_rate'],
                    'predicted_final_rate': analysis['predicted_final_rate'],
                    'status': analysis['status'],
                    'trend': analysis['trend']
                })
                
        # Sort by worst attendance rate first
        at_risk_list = sorted(at_risk_list, key=lambda x: x['attendance_rate'])
        return at_risk_list

    @staticmethod
    def check_and_generate_early_warnings(student_id):
        """
        Evaluates a student's attendance across all their registered courses.
        If any course is in a 'Warning' or 'Critical' state, check if an early
        warning notification was already sent today. If not, generate one.
        """
        student = Student.query.get(student_id)
        if not student:
            return
            
        for course in student.courses:
            analysis = AIAnalyticsService.get_student_course_attendance(student.id, course.id)
            if analysis['status'] in ['Warning', 'Critical']:
                # Formulate message
                title = f"AI Early Warning: Low Attendance in {course.course_code}"
                
                if analysis['status'] == 'Critical':
                    msg = (f"URGENT: Your attendance in {course.course_code} ({course.course_title}) "
                           f"is currently {analysis['attendance_rate']}%. You have missed multiple consecutive sessions. "
                           f"You are at critical risk of failing the 75% attendance threshold required to sit for the final exam. "
                           f"Please contact your lecturer, Dr. {course.lecturer.full_name}, immediately.")
                else:
                    msg = (f"NOTICE: Your attendance in {course.course_code} ({course.course_title}) "
                           f"is {analysis['attendance_rate']}%. The AI predicts a final attendance rate of "
                           f"{analysis['predicted_final_rate']}% if current trends continue. Please attend the next classes "
                           f"to ensure you meet the 75% requirement.")
                
                # Check if notification was already generated recently for this course
                existing = Notification.query.filter_by(
                    user_id=student.user_id,
                    title=title
                ).first()
                
                if not existing:
                    warning = Notification(
                        user_id=student.user_id,
                        title=title,
                        message=msg,
                        is_read=False
                    )
                    db.session.add(warning)
        
        db.session.commit()
