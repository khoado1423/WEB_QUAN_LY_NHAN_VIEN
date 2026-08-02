"""
data_helper.py
Các hàm CRUD cho Nhân viên và Công việc, dùng Google Sheet thay cho Excel.
Yêu cầu: trong Google Sheet có 2 tab tên "NhanVien" và "CongViec",
mỗi tab có dòng đầu tiên là header đúng tên cột dưới đây.
"""

from sheets_helper import get_sheet_data, append_sheet_data, update_sheet_data

# ================== NHÂN VIÊN ==================
# Cột: employee_code | full_name | email | department

def get_all_employees():
    rows = get_sheet_data("NhanVien")
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]


def add_employee(employee_code, full_name, email, department):
    append_sheet_data("NhanVien", [[employee_code, full_name, email, department]])


def update_employee(row_index, employee_code, full_name, email, department):
    # row_index: số dòng thật trong Sheet (VD dòng 2 = nhân viên đầu tiên, vì dòng 1 là header)
    update_sheet_data(
        f"NhanVien!A{row_index}:D{row_index}",
        [[employee_code, full_name, email, department]]
    )


# ================== CÔNG VIỆC ==================
# Cột: task_code | title | description | priority | duration

def get_all_tasks():
    rows = get_sheet_data("CongViec")
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]


def add_task(task_code, title, description, priority, duration):
    append_sheet_data("CongViec", [[task_code, title, description, priority, duration]])


def update_task(row_index, task_code, title, description, priority, duration):
    update_sheet_data(
        f"CongViec!A{row_index}:E{row_index}",
        [[task_code, title, description, priority, duration]]
    )