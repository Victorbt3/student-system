"""demo_seed.py

Creates demo accounts (admin/lecturers/students), plus demo courses, and (optionally)
assigns students to courses.

It writes into the same DB used by the Flask app (SQLALCHEMY_DATABASE_URI).

Usage:
  python demo_seed.py

By default, it is safe to run multiple times (it will skip existing users/courses
by unique fields).
"""

from __future__ import annotations

from typing import Iterable

from config import Config
from app import create_app
from models import db, User, Admin, Lecturer, Student, Course


ADMIN_CREDENTIALS = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "full_name": "Default Admin",
    "employee_no": "ADM001",
    "phone_number": "0000000000",
}

LECTURERS = [
    {
        "username": "lecturer1",
        "email": "lecturer1@example.com",
        "password": "lecturer123",
        "staff_number": "LCT101",
        "full_name": "Dr. Richard Smith",
        "faculty": "Science and Technology",
        "department": "Computer Science",
        "phone_number": "+12025550143",
    },
    {
        "username": "lecturer2",
        "email": "lecturer2@example.com",
        "password": "lecturer123",
        "staff_number": "LCT102",
        "full_name": "Dr. Sarah Davis",
        "faculty": "Science and Technology",
        "department": "Mathematics",
        "phone_number": "+12025550188",
    },
]

STUDENTS = [
    {
        "username": "student1",
        "email": "student1@example.com",
        "password": "student123",
        "matric_number": "22/10120",
        "full_name": "John Doe",
        "faculty": "Science and Technology",
        "department": "Computer Science",
        "level": "400",
        "phone_number": "+12025550111",
    },
    {
        "username": "student2",
        "email": "student2@example.com",
        "password": "student123",
        "matric_number": "22/11383",
        "full_name": "Jane Doe",
        "faculty": "Science and Technology",
        "department": "Computer Science",
        "level": "400",
        "phone_number": "+12025550122",
    },
    {
        "username": "student3",
        "email": "student3@example.com",
        "password": "student123",
        "matric_number": "22/10784",
        "full_name": "Robert Johnson",
        "faculty": "Science and Technology",
        "department": "Computer Science",
        "level": "300",
        "phone_number": "+12025550133",
    },
    {
        "username": "student4",
        "email": "student4@example.com",
        "password": "student123",
        "matric_number": "22/11807",
        "full_name": "Mary Williams",
        "faculty": "Science and Technology",
        "department": "Mathematics",
        "level": "400",
        "phone_number": "+12025550144",
    },
    {
        "username": "student5",
        "email": "student5@example.com",
        "password": "student123",
        "matric_number": "22/10788",
        "full_name": "David Brown",
        "faculty": "Science and Technology",
        "department": "Mathematics",
        "level": "200",
        "phone_number": "+12025550155",
    },
]

COURSES = [
    {
        "course_code": "CSC 401",
        "course_title": "Artificial Intelligence",
        "department": "Computer Science",
        "unit": 3,
        "lecturer_staff_number": "LCT101",
    },
    {
        "course_code": "CSC 403",
        "course_title": "Digital Image Processing",
        "department": "Computer Science",
        "unit": 3,
        "lecturer_staff_number": "LCT101",
    },
    {
        "course_code": "MTH 301",
        "course_title": "Advanced Calculus",
        "department": "Mathematics",
        "unit": 3,
        "lecturer_staff_number": "LCT102",
    },
    {
        "course_code": "CSC 302",
        "course_title": "Software Engineering",
        "department": "Computer Science",
        "unit": 3,
        "lecturer_staff_number": "LCT101",
    },
]

# Map course_code -> list of student matric_numbers
ENROLLMENTS = {
    "CSC 401": ["22/10120", "22/11383", "22/10784"],
    "CSC 403": ["22/10120", "22/11383"],
    "MTH 301": ["22/11807", "22/10788"],
    "CSC 302": ["22/10784", "22/10120"],
}


def get_or_create_user(*, username: str, email: str, role: str, password: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user:
        # Keep existing password_hash to avoid accidental resets.
        # If you want to force password reset, change this behavior.
        return user

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def get_or_create_admin(payload: dict) -> Admin:
    # By unique employee_no and/or user role profile
    user = User.query.filter_by(username=payload["username"], role="admin").first()
    if not user:
        user = get_or_create_user(
            username=payload["username"],
            email=payload["email"],
            role="admin",
            password=payload["password"],
        )

    profile = Admin.query.filter_by(user_id=user.id).first()
    if profile:
        return profile

    profile = Admin(
        user_id=user.id,
        full_name=payload["full_name"],
        employee_no=payload["employee_no"],
        phone_number=payload["phone_number"],
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def get_or_create_lecturer(payload: dict) -> Lecturer:
    user = User.query.filter_by(username=payload["username"], role="lecturer").first()
    if not user:
        user = get_or_create_user(
            username=payload["username"],
            email=payload["email"],
            role="lecturer",
            password=payload["password"],
        )

    profile = Lecturer.query.filter_by(staff_number=payload["staff_number"]).first()
    if profile:
        return profile

    profile = Lecturer(
        user_id=user.id,
        staff_number=payload["staff_number"],
        full_name=payload["full_name"],
        faculty=payload["faculty"],
        department=payload["department"],
        phone_number=payload["phone_number"],
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def get_or_create_student(payload: dict) -> Student:
    user = User.query.filter_by(username=payload["username"], role="student").first()
    if not user:
        user = get_or_create_user(
            username=payload["username"],
            email=payload["email"],
            role="student",
            password=payload["password"],
        )

    # If the matric number exists, ensure it's tied to the same user.
    profile_by_matric = Student.query.filter_by(matric_number=payload["matric_number"]).first()
    if profile_by_matric:
        if profile_by_matric.user_id != user.id:
            # Keep DB consistent with the current username mapping.
            profile_by_matric.user_id = user.id
        return profile_by_matric

    # If user already has a student profile, just update it.
    profile_by_user = Student.query.filter_by(user_id=user.id).first()
    if profile_by_user:
        profile_by_user.matric_number = payload["matric_number"]
        profile_by_user.full_name = payload["full_name"]
        profile_by_user.faculty = payload["faculty"]
        profile_by_user.department = payload["department"]
        profile_by_user.level = payload["level"]
        profile_by_user.phone_number = payload["phone_number"]
        return profile_by_user

    profile = Student(
        user_id=user.id,
        matric_number=payload["matric_number"],
        full_name=payload["full_name"],
        faculty=payload["faculty"],
        department=payload["department"],
        level=payload["level"],
        phone_number=payload["phone_number"],
        profile_pic="default_profile.png",
        face_registered=False,
        registered_at=None,
    )
    db.session.add(profile)
    db.session.flush()
    return profile



def get_or_create_course(payload: dict) -> Course:
    course = Course.query.filter_by(course_code=payload["course_code"]).first()
    if course:
        return course

    lecturer = Lecturer.query.filter_by(staff_number=payload["lecturer_staff_number"]).first()
    if not lecturer:
        raise RuntimeError(
            f"Missing lecturer for course {payload['course_code']} "
            f"(staff_number={payload['lecturer_staff_number']})."
        )

    course = Course(
        course_code=payload["course_code"],
        course_title=payload["course_title"],
        department=payload["department"],
        unit=payload["unit"],
        lecturer_id=lecturer.id,
    )
    db.session.add(course)
    db.session.flush()
    return course


def apply_enrollments():
    for course_code, matric_numbers in ENROLLMENTS.items():
        course = Course.query.filter_by(course_code=course_code).first()
        if not course:
            continue

        students = Student.query.filter(Student.matric_number.in_(matric_numbers)).all()

        # Replace enrollment set for this demo.
        course.students = students


def main():
    app = create_app()
    with app.app_context():
        print(f"[demo_seed] DB URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

        db.create_all()

        # Admin + profiles
        get_or_create_admin(ADMIN_CREDENTIALS)

        for lec in LECTURERS:
            get_or_create_lecturer(lec)

        for stu in STUDENTS:
            get_or_create_student(stu)

        for c in COURSES:
            get_or_create_course(c)

        apply_enrollments()
        db.session.commit()

        print("[demo_seed] Done.")
        print("[demo_seed] Login test credentials:")
        print(f"  Admin:     admin / admin123")
        for lec in LECTURERS:
            print(f"  Lecturer:  {lec['username']} / {lec['password']} (role=lecturer)")
        for stu in STUDENTS:
            print(f"  Student:   {stu['username']} / {stu['password']} (role=student)")


if __name__ == "__main__":
    main()

