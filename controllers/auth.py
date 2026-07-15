from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user.role)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password for the selected role.', 'danger')
            return redirect(url_for('auth.login'))

        if role and user.role != role:
            flash(f'Logged in as {user.role.title()} using your account credentials.', 'info')
            
        login_user(user, remember=remember)
        return redirect_dashboard(user.role)
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user.role)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        matric = request.form.get('matric', '').strip()
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password, matric, full_name]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Create student user
        from models import Student
        user = User(username=username, email=email, role='student')
        user.set_password(password)
        
        student = Student(
            full_name=full_name,
            matric_number=matric,
            faculty='Self-Registered',
            department='General',
            level='100'
        )
        
        user.student_profile = student
        db.session.add(user)
        db.session.add(student)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/recovery', methods=['GET', 'POST'])
def recovery():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Mock email sending for final year project demonstration
            flash(f'Password reset instructions have been sent to {email}.', 'success')
        else:
            flash('Email address not found in our records.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('auth/recovery.html')

def redirect_dashboard(role):
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'lecturer':
        return redirect(url_for('lecturer.dashboard'))
    elif role == 'student':
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('index'))
