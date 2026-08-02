import os
import subprocess
import sys
import importlib.util
from dotenv import load_dotenv
load_dotenv()

import os, json
if not os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    with open("service_account.json", "r", encoding="utf-8") as f:
        os.environ["GOOGLE_CREDENTIALS_JSON"] = f.read()

# -------------------------------------------------------------
# 1. KIỂM TRA VÀ TỰ ĐỘNG CÀI ĐẶT THƯ VIỆN (CHỈ CHẠY LẦN ĐẦU)
# -------------------------------------------------------------
def check_and_install_requirements():
    # Danh sách các thư viện cốt lõi cần kiểm tra
    required_packages = ["flask", "googleapiclient"]
    
    # Kiểm tra nếu THIẾU BẤT KỲ thư viện nào trong danh sách trên
    if any(importlib.util.find_spec(pkg) is None for pkg in required_packages):
        print("⚡ Lần đầu chạy project: Đang tự động cài đặt các thư viện cần thiết...")
        try:
            # Tự động gọi pip install -r requirements.txt
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Cài đặt thư viện hoàn tất!\n")
        except Exception as e:
            print(f"❌ Lỗi trong quá trình cài đặt thư viện: {e}")

# Thực thi kiểm tra cài đặt trước tiên
check_and_install_requirements()


# -------------------------------------------------------------
# 2. IMPORT CÁC MODULE CỦA ỨNG DỤNG (Sau khi đã đảm bảo đủ thư viện)
# -------------------------------------------------------------
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