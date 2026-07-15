import base64
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, AttendanceSession, AttendanceRecord, Student
from services import FaceRecognitionService
from config import Config

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

def get_face_rec_service():
    return FaceRecognitionService(Config.UPLOAD_FOLDER)

@attendance_bp.route('/scan/<int:session_id>', methods=['POST'])
@login_required
def scan_frame(session_id):
    """
    Handles base64 frames sent from the lecturer's camera scanning interface.
    Performs face detection and recognition, and records attendance in real-time.
    """
    session = AttendanceSession.query.get_or_404(session_id)
    if session.status != 'active':
        return jsonify({'success': False, 'message': 'This session is no longer active.'}), 400
        
    data = request.json
    if not data or 'frame' not in data:
        return jsonify({'success': False, 'message': 'No video frame provided.'}), 400
        
    frame_b64 = data['frame']
    
    try:
        # Decode image
        if ',' in frame_b64:
            frame_b64 = frame_b64.split(',')[1]
            
        img_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'Failed to decode image frame.'}), 400
            
        # Get enrolled students
        enrolled_students = []
        for student in session.course.students:
            enrolled_students.append({
                'id': student.id,
                'name': student.full_name,
                'matric': student.matric_number,
                'face_registered': student.face_registered
            })
            
        # We only pass students who actually have registered faces to OpenCV (unless in demo mode, which handles fallback)
        # Note: FaceRecognitionService will handle mock mapping if recognizer isn't trained
        face_service = get_face_rec_service()
        scan_results = face_service.recognize_face(img, enrolled_students)
        
        saved_records = []
        
        for result in scan_results:
            student_id = result['student_id']
            if student_id:
                # Check if student is already marked present in this session
                existing = AttendanceRecord.query.filter_by(
                    session_id=session.id,
                    student_id=student_id
                ).first()
                
                # Convert confidence distance to a percentage score
                # LBPH confidence is a distance. 0 is perfect, ~80 is maximum distance.
                # Let's map it: score = max(0, 1.0 - (dist / 100))
                raw_conf = result['confidence']
                pct_score = max(0.0, 1.0 - (raw_conf / 100.0))
                if raw_conf == 50.0 and not face_service.has_lbph: # Demo mode
                    pct_score = 0.95
                
                if not existing:
                    # Mark student as present
                    record = AttendanceRecord(
                        session_id=session.id,
                        student_id=student_id,
                        status='present',
                        verification_method='face_recognition',
                        confidence_score=pct_score,
                        time_marked=datetime.utcnow()
                    )
                    db.session.add(record)
                    db.session.commit()
                    
                    result['action'] = 'marked'
                    result['time_marked'] = record.time_marked.strftime('%I:%M:%S %p')
                else:
                    result['action'] = 'already_marked'
                    result['time_marked'] = existing.time_marked.strftime('%I:%M:%S %p')
            else:
                result['action'] = 'ignored'
                result['time_marked'] = None
                
            saved_records.append(result)
            
        return jsonify({
            'success': True,
            'results': saved_records,
            'total_detected': len(scan_results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
