"""
test_sheet.py
Chạy file này để kiểm tra kết nối Google Sheet đã hoạt động chưa.
Cách chạy: python test_sheet.py
"""
 
from dotenv import load_dotenv
load_dotenv()
 
import os
 
# Nếu chưa có GOOGLE_CREDENTIALS_JSON trong biến môi trường,
# tự động đọc từ file service_account.json ở local để test
if not os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    with open("service_account.json", "r", encoding="utf-8-sig") as f:
        os.environ["GOOGLE_CREDENTIALS_JSON"] = f.read()

        # DEBUG - xóa sau khi kiểm tra xong
print("Độ dài nội dung:", len(os.environ["GOOGLE_CREDENTIALS_JSON"]))
print("50 ký tự đầu:", os.environ["GOOGLE_CREDENTIALS_JSON"][:50])
 
from data_helper import get_all_employees, get_all_tasks
 
print("--- Danh sách nhân viên ---")
try:
    employees = get_all_employees()
    print(employees)
    print(f"=> Đọc được {len(employees)} nhân viên")
except Exception as e:
    print(f"LỖI khi đọc NhanVien: {e}")
 
print()
print("--- Danh sách công việc ---")
try:
    tasks = get_all_tasks()
    print(tasks)
    print(f"=> Đọc được {len(tasks)} công việc")
except Exception as e:
    print(f"LỖI khi đọc CongViec: {e}")
 