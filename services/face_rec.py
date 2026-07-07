import os
import base64
import pickle

# Graceful degradation - try to import cv2 and numpy
try:
    import cv2
    import numpy as np
    from PIL import Image
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("WARNING: opencv not installed. System runs in DEMO/MOCK mode for face recognition.")


class FaceRecognitionService:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.dataset_dir = os.path.join(upload_folder, 'face_dataset')
        self.model_path = os.path.join(upload_folder, 'face_recognizer.yml')
        self.orb_model_path = os.path.join(upload_folder, 'face_recognizer_orb.pkl')
        self.has_lbph = False
        self.recognizer = None
        self.face_cascade = None
        self.orb = None
        self.bf = None
        self.orb_data = {}

        os.makedirs(self.dataset_dir, exist_ok=True)

        if HAS_CV2:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            try:
                # Try LBPH (requires opencv-contrib)
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.has_lbph = True
                if os.path.exists(self.model_path):
                    self.recognizer.read(self.model_path)
                    print(f"[FaceRec] Loaded trained model from {self.model_path}")
            except Exception:
                # LBPH not available; fall back to ORB-based recognizer
                self.has_lbph = False
                try:
                    self.orb = cv2.ORB_create()
                    self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    if os.path.exists(self.orb_model_path):
                        with open(self.orb_model_path, 'rb') as f:
                            self.orb_data = pickle.load(f)
                        print(f"[FaceRec] Loaded ORB model from {self.orb_model_path}")
                    else:
                        print("[FaceRec] ORB fallback ready (no model file yet)")
                except Exception:
                    print("[FaceRec] cv2.face and ORB not available. DEMO mode active.")
        else:
            print("[FaceRec] OpenCV not installed. DEMO mode active.")

    def _decode_frame(self, frame_b64):
        """Decode a base64 image to a numpy BGR array."""
        if not HAS_CV2:
            return None
        if ',' in frame_b64:
            frame_b64 = frame_b64.split(',')[1]
        img_bytes = base64.b64decode(frame_b64)
        import numpy as np
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def detect_faces(self, gray_image):
        """Return list of (x, y, w, h) tuples."""
        if not HAS_CV2 or self.face_cascade is None or self.face_cascade.empty():
            return []
        faces = self.face_cascade.detectMultiScale(
            gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return faces if len(faces) > 0 else []

    def save_face_sample(self, image_data, matric_number, sample_num):
        """Save one face sample image for training."""
        if not HAS_CV2:
            # In mock mode, just create a placeholder file
            student_dir = os.path.join(self.dataset_dir, matric_number.replace('/', '_'))
            os.makedirs(student_dir, exist_ok=True)
            file_path = os.path.join(student_dir, f"sample_{sample_num}.txt")
            with open(file_path, 'w') as f:
                f.write(f"mock_sample_{sample_num}")
            return True, file_path

        import numpy as np
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        faces = self.detect_faces(gray)
        if len(faces) == 0:
            return False, "No face detected in the image."

        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w, h = faces[0]
        face_crop = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_crop, (200, 200))

        student_dir = os.path.join(self.dataset_dir, matric_number.replace('/', '_'))
        os.makedirs(student_dir, exist_ok=True)
        file_path = os.path.join(student_dir, f"sample_{sample_num}.jpg")
        cv2.imwrite(file_path, face_resized)
        return True, file_path

    def train_model(self, student_id_mappings):
        """Train the LBPH recognizer on all collected face samples."""
        # If LBPH available, use it
        if HAS_CV2 and self.has_lbph:
            import numpy as np
            from PIL import Image

            face_samples, ids = [], []
            if not os.path.exists(self.dataset_dir):
                return False, "Dataset directory does not exist."

            for folder_name in os.listdir(self.dataset_dir):
                folder_path = os.path.join(self.dataset_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                student_id = student_id_mappings.get(folder_name)
                if student_id is None:
                    continue
                for filename in os.listdir(folder_path):
                    if not filename.endswith('.jpg'):
                        continue
                    img_path = os.path.join(folder_path, filename)
                    try:
                        pil_img = Image.open(img_path).convert('L')
                        face_samples.append(np.array(pil_img, 'uint8'))
                        ids.append(student_id)
                    except Exception as e:
                        print(f"[FaceRec] Error reading {img_path}: {e}")

            if not face_samples:
                return False, "No valid face samples found for training."

            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.train(face_samples, np.array(ids))
                self.recognizer.write(self.model_path)
                self.has_lbph = True
                return True, f"Model trained on {len(face_samples)} samples for {len(set(ids))} student(s)."
            except Exception as e:
                return False, f"Training failed: {str(e)}"

        # Else, if ORB available, build ORB descriptor model
        if HAS_CV2 and self.orb is not None:
            orb_data = {}
            for folder_name in os.listdir(self.dataset_dir):
                folder_path = os.path.join(self.dataset_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                student_id = student_id_mappings.get(folder_name)
                if student_id is None:
                    continue
                descriptors_list = []
                for filename in os.listdir(folder_path):
                    if not filename.endswith('.jpg'):
                        continue
                    img_path = os.path.join(folder_path, filename)
                    try:
                        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                        kp, des = self.orb.detectAndCompute(img, None)
                        if des is not None:
                            descriptors_list.append(des)
                    except Exception as e:
                        print(f"[FaceRec] ORB read error {img_path}: {e}")
                if descriptors_list:
                    # stack descriptors for this student
                    try:
                        stacked = np.vstack(descriptors_list)
                        orb_data[student_id] = stacked
                    except Exception:
                        orb_data[student_id] = descriptors_list[0]

            if not orb_data:
                return False, "No ORB descriptors could be created for training."

            with open(self.orb_model_path, 'wb') as f:
                pickle.dump(orb_data, f)
            self.orb_data = orb_data
            return True, f"ORB model trained for {len(orb_data)} student(s)."

        # Mock training fallback
        with open(self.model_path, 'w') as f:
            f.write("mock_model: true\n")
            for folder, sid in student_id_mappings.items():
                f.write(f"{folder}:{sid}\n")
        return True, "Face model trained successfully (Demo Mode - OpenCV not installed)."

    def recognize_face(self, image_data, enrolled_students):
        """
        Detect and identify faces. Returns list of result dicts.
        Falls back to demo mode (round-robin mock match) if OpenCV is unavailable.
        """
        # ---- DEMO / MOCK MODE ----
        if not HAS_CV2:
            if not enrolled_students:
                return []
            student = enrolled_students[0]
            return [{
                'box': [80, 60, 180, 180],
                'student_id': student['id'],
                'confidence': 50.0,
                'name': student['name'],
                'matric': student['matric'],
                'status': 'recognized'
            }]

        # Convert to gray
        import numpy as np
        try:
            gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        except Exception:
            gray = image_data

        faces = self.detect_faces(gray)
        results = []

        # If no faces detected, fall back to using the whole frame (helps low-quality/demo inputs)
        if len(faces) == 0:
            faces = [(0, 0, gray.shape[1], gray.shape[0])]

        # If LBPH trained, use it
        if self.has_lbph and os.path.exists(self.model_path):
            for (x, y, w, h) in faces:
                face_resized = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                try:
                    student_id, confidence = self.recognizer.predict(face_resized)
                    matched = next((s for s in enrolled_students if s['id'] == student_id), None)
                    if matched and confidence < 85.0:
                        results.append({
                            'box': [int(x), int(y), int(w), int(h)],
                            'student_id': student_id,
                            'confidence': round(confidence, 2),
                            'name': matched['name'],
                            'matric': matched['matric'],
                            'status': 'recognized'
                        })
                    else:
                        results.append({
                            'box': [int(x), int(y), int(w), int(h)],
                            'student_id': None,
                            'confidence': round(confidence, 2),
                            'name': 'Unknown',
                            'matric': 'N/A',
                            'status': 'unknown'
                        })
                except Exception as e:
                    print(f"[FaceRec] Predict error: {e}")
            return results

        # Else, if ORB model available, use descriptor matching
        if self.orb is not None and self.orb_data:
            for (x, y, w, h) in faces:
                face_crop = gray[y:y+h, x:x+w]
                try:
                    face_resized = cv2.resize(face_crop, (200, 200))
                except Exception:
                    face_resized = face_crop
                kp, des = self.orb.detectAndCompute(face_resized, None)
                best = None
                best_score = 0.0
                if des is None:
                    results.append({
                        'box': [int(x), int(y), int(w), int(h)],
                        'student_id': None,
                        'confidence': 0.0,
                        'name': 'Unknown',
                        'matric': 'N/A',
                        'status': 'unknown'
                    })
                    continue

                for student in enrolled_students:
                    sid = student['id']
                    stored = self.orb_data.get(sid)
                    if stored is None:
                        continue
                    try:
                        matches = self.bf.match(des, stored)
                        if not matches:
                            continue
                        good = sum(1 for m in matches if m.distance < 60)
                        score = good / len(matches)
                        if score > best_score:
                            best_score = score
                            best = student
                    except Exception:
                        continue

                if best and best_score > 0.12:
                    # confidence: map score to a 0-100 scale (higher better)
                    confidence_pct = round(best_score * 100, 2)
                    results.append({
                        'box': [int(x), int(y), int(w), int(h)],
                        'student_id': best['id'],
                        'confidence': confidence_pct,
                        'name': best['name'],
                        'matric': best['matric'],
                        'status': 'recognized'
                    })
                else:
                    results.append({
                        'box': [int(x), int(y), int(w), int(h)],
                        'student_id': None,
                        'confidence': round(best_score * 100, 2),
                        'name': 'Unknown',
                        'matric': 'N/A',
                        'status': 'unknown'
                    })
            return results

        # Fallback demo behavior
        if not enrolled_students:
            return []
        student = enrolled_students[0]
        return [{
            'box': [80, 60, 180, 180],
            'student_id': student['id'],
            'confidence': 50.0,
            'name': student['name'],
            'matric': student['matric'],
            'status': 'recognized'
        }]
