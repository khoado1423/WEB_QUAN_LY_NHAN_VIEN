from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        new_admin = User(username='admin', role='admin')
        new_admin.set_password('123456')
        db.session.add(new_admin)
        db.session.commit()
        print("Đã tạo tài khoản quản trị thành công! (User: admin / Pass: 123456)")
    else:
        print("Tài khoản admin đã tồn tại sẵn trong hệ thống.")