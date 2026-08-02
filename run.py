import os
from app import create_app, db
from app.models.user import User
from sheets_helper import get_sheet_data, update_sheet_data, append_sheet_data

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()  # Tự động tạo cơ sở dữ liệu SQLite nếu chưa có

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            new_admin = User(username='admin', role='Admin')
            new_admin.set_password('1234')
            db.session.add(new_admin)
            db.session.commit()
            print("Đã tạo tài khoản quản trị mặc định! (User: admin / Pass: 1234)")
        else:
            print("Tài khoản admin đã tồn tại sẵn trong hệ thống.")

# Chạy phần khởi tạo này ngay khi file được import (kể cả khi Render/gunicorn gọi)
init_db()

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("\n-------------------------------------------------")
        print("🚀 Ứng dụng đang chạy tại: http://127.0.0.1:5000")
        print("-------------------------------------------------\n")
    app.run(debug=True)