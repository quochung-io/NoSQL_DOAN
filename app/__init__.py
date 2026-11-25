from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Đăng ký Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import student_bp
    from app.routes.lecturer_routes import lecturer_bp
    from app.routes.staff_routes import staff_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.chat_routes import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chat_bp, url_prefix='/chat')

    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        if 'user' in session:
            role = session['user'].get('role')
            if role == 'student':
                return redirect(url_for('student.search'))
            elif role == 'lecturer':
                return redirect(url_for('lecturer.dashboard'))
            elif role == 'staff':
                return redirect(url_for('staff.dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    return app
