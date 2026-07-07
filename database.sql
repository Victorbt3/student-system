-- Smart Student Attendance System Using Facial Recognition
-- MySQL Database Design & Sample Data

CREATE DATABASE IF NOT EXISTS student_attendance_db;
USE student_attendance_db;

-- 1. Users table (Central authentication)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    role ENUM('admin', 'lecturer', 'student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    employee_no VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Lecturers table
CREATE TABLE IF NOT EXISTS lecturers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    staff_number VARCHAR(50) UNIQUE NOT NULL,
    faculty VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Students table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    matric_number VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    faculty VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,
    phone_number VARCHAR(20),
    profile_pic VARCHAR(255) DEFAULT 'default_profile.png',
    face_registered BOOLEAN DEFAULT FALSE,
    registered_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Courses table
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(15) UNIQUE NOT NULL,
    course_title VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    unit INT DEFAULT 3,
    lecturer_id INT NOT NULL,
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Student-Course enrollment (Many-to-Many)
CREATE TABLE IF NOT EXISTS student_courses (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Attendance Sessions
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    lecturer_id INT NOT NULL,
    session_date DATE NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    status ENUM('active', 'completed') DEFAULT 'active',
    session_code VARCHAR(10) UNIQUE NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Attendance Records
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    student_id INT NOT NULL,
    time_marked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('present', 'absent', 'late') DEFAULT 'present',
    verification_method ENUM('face_recognition', 'manual') DEFAULT 'face_recognition',
    confidence_score FLOAT DEFAULT 1.0,
    FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_session_student (session_id, student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- SAMPLE DATA SEEDING (Password is 'password123' hashed with pbkdf2:sha256)
-- pbkdf2:sha256:600000$hG7xI5vJ$3a8... for pbkdf2:sha256:260000$sha256_hash
-- In python: generate_password_hash('password123')
-- =========================================================

-- Insert Users
-- passwords are all 'pbkdf2:sha256:260000$u66jL5BvN1n3z9p2$2f9d6c7b9e8a7bc...' or similar.
-- We will use a standard Flask werkzeug pbkdf2:sha256 hash format.
-- 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5' (for 'password123')
INSERT INTO users (id, username, password_hash, email, role) VALUES
(1, 'admin', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'admin@university.edu', 'admin'),
(2, 'lecturer1', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'dr.smith@university.edu', 'lecturer'),
(3, 'lecturer2', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'dr.davis@university.edu', 'lecturer'),
(4, 'student1', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'john.doe@student.edu', 'student'),
(5, 'student2', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'jane.doe@student.edu', 'student'),
(6, 'student3', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'robert.johnson@student.edu', 'student'),
(7, 'student4', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'mary.williams@student.edu', 'student'),
(8, 'student5', 'pbkdf2:sha256:260000$gSdf8SDF$cf7b819f6a7d526786016e4ee6bf0b98eb605b4b1a41f6e2101031d234a9b5f5', 'david.brown@student.edu', 'student');

-- Insert Admins
INSERT INTO admins (id, user_id, full_name, employee_no, phone_number) VALUES
(1, 1, 'Prof. Albert Einstein', 'EMP001', '+1234567890');

-- Insert Lecturers
INSERT INTO lecturers (id, user_id, full_name, staff_number, faculty, department, phone_number) VALUES
(1, 2, 'Dr. Richard Smith', 'LCT101', 'Science and Technology', 'Computer Science', '+12025550143'),
(2, 3, 'Dr. Sarah Davis', 'LCT102', 'Science and Technology', 'Mathematics', '+12025550188');

-- Insert Students
INSERT INTO students (id, user_id, matric_number, full_name, faculty, department, level, phone_number, face_registered) VALUES
(1, 4, '22/10120', 'John Doe', 'Science and Technology', 'Computer Science', '400', '+12025550111', FALSE),
(2, 5, '22/11383', 'Jane Doe', 'Science and Technology', 'Computer Science', '400', '+12025550122', FALSE),
(3, 6, '22/10784', 'Robert Johnson', 'Science and Technology', 'Computer Science', '300', '+12025550133', FALSE),
(4, 7, '22/11807', 'Mary Williams', 'Science and Technology', 'Mathematics', '400', '+12025550144', FALSE),
(5, 8, '22/10788', 'David Brown', 'Science and Technology', 'Mathematics', '200', '+12025550155', FALSE);

-- Insert Courses
INSERT INTO courses (id, course_code, course_title, department, unit, lecturer_id) VALUES
(1, 'CSC 401', 'Artificial Intelligence', 'Computer Science', 3, 1),
(2, 'CSC 403', 'Digital Image Processing', 'Computer Science', 3, 1),
(3, 'MTH 301', 'Advanced Calculus', 'Mathematics', 3, 2),
(4, 'CSC 302', 'Software Engineering', 'Computer Science', 3, 1);

-- Enroll Students in Courses
INSERT INTO student_courses (student_id, course_id) VALUES
-- CSC 401: John (1), Jane (2), Robert (3)
(1, 1), (2, 1), (3, 1),
-- CSC 403: John (1), Jane (2)
(1, 2), (2, 2),
-- MTH 301: Mary (4), David (5)
(4, 3), (5, 3),
-- CSC 302: Robert (3), John (1)
(3, 4), (1, 4);
