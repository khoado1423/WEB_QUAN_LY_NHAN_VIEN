from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Đăng ký user_loader cho Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Đăng ký các Blueprint
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employee import employee_bp
    from app.routes.task import task_bp
    from app.routes.schedule import schedule_bp
    from app.routes.assignment import assignment_bp  

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(assignment_bp)  

    # Bơm system_name vào MỌI template (sidebar, tiêu đề trang...)
    # để khi Admin đổi Tên hệ thống ở trang Cài đặt, nó cập nhật ở khắp nơi.
    @app.context_processor
    def inject_system_name():
        from app.models.setting import SystemSetting
        return dict(system_name=SystemSetting.get('system_name', 'Employee Task Scheduler'))

    return app

# Nạp các model database để Flask-Migrate nhận diện
from app.models import user, employee, task, schedule, assignment, setting
