from app import create_app, db
from app.models.user import User

app = create_app()

NEW_PASSWORD = '1234'  # Đổi mật khẩu bạn muốn ở đây

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password(NEW_PASSWORD)
        db.session.commit()
        print(f"Đã đặt lại mật khẩu cho tài khoản 'admin' thành: {NEW_PASSWORD}")
    else:
        print("Không tìm thấy tài khoản 'admin' nào trong database.")
        print("Danh sách tài khoản hiện có:")
        for u in User.query.all():
            print(f" - {u.username} (role: {u.role})")
