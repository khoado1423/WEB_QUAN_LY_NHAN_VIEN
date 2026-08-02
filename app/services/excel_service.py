import pandas as pd
from app import db
from app.models.employee import Employee
from app.models.task import Task

def import_employees_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        count = 0
        for _, row in df.iterrows():
            code = str(row.get('employee_code', '')).strip()
            name = str(row.get('full_name', '')).strip()
            email = str(row.get('email', '')).strip()
            department = str(row.get('department', '')).strip()

            if code and not Employee.query.filter_by(employee_code=code).first():
                new_emp = Employee(employee_code=code, full_name=name, email=email, department=department)
                db.session.add(new_emp)
                count += 1
        db.session.commit()
        return True, f"Đã nhập thành công {count} nhân viên từ Excel!"
    except Exception as e:
        return False, f"Lỗi đọc file Excel nhân viên: {str(e)}"

def import_tasks_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        count = 0
        for _, row in df.iterrows():
            code = str(row.get('task_code', '')).strip()
            title = str(row.get('title', '')).strip()
            description = str(row.get('description', '')).strip()
            priority = str(row.get('priority', 'Trung bình')).strip()
            duration = float(row.get('duration', 1.0))

            if code and not Task.query.filter_by(task_code=code).first():
                new_task = Task(task_code=code, title=title, description=description, priority=priority, duration=duration)
                db.session.add(new_task)
                count += 1
        db.session.commit()
        return True, f"Đã nhập thành công {count} công việc từ Excel!"
    except Exception as e:
        return False, f"Lỗi đọc file Excel công việc: {str(e)}"