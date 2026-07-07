import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
from controllers import auth_bp, admin_bp, lecturer_bp, student_bp, attendance_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # type: ignore
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(attendance_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            if current_user.role == 'lecturer':
                return redirect(url_for('lecturer.dashboard'))
            if current_user.role == 'student':
                return redirect(url_for('student.dashboard'))
        return render_template('index.html')

    @app.errorhandler(404)
    def not_found(error):
        return 'Page not found', 404

    with app.app_context():
        # ensure upload folders exist (avoid creating at import-time)
        try:
            Config.ensure_upload_dirs()
        except Exception:
            pass

        db.create_all()
        _create_default_admin()

    return app


def _create_default_admin():
    from models import Admin

    if User.query.filter_by(role='admin').first():
        return

    admin_user = User(username='admin', email='admin@example.com', role='admin')
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    db.session.flush()

    admin_profile = Admin(
        user_id=admin_user.id,
        full_name='Default Admin',
        employee_no='ADM001',
        phone_number='0000000000'
    )
    db.session.add(admin_profile)
    db.session.commit()
    print('Created default admin user: admin / admin123')


# Expose WSGI app for servers (e.g., Vercel)
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
