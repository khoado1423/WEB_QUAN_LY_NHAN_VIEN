import pandas as pd
from app import db
from app.models.employee import Employee

def import_employees_from_excel(file_path):
    try:
        # Đọc file excel bằng pandas
        df = pd.read_excel(file_path)
        
        # Các cột yêu cầu trong file excel
        required_columns = ['Mã nhân viên', 'Họ tên', 'Email', 'Số điện thoại', 'Bộ phận', 'Chức vụ']
        
        # Kiểm tra xem file excel có đủ cột không
        for col in required_columns:
            if col not in df.columns:
                return False, f"Thiếu cột bắt buộc trong file Excel: {col}"

        success_count = 0
        update_count = 0

        for _, row in df.iterrows():
            emp_code = str(row['Mã nhân viên']).strip()
            full_name = str(row['Họ tên']).strip()
            email = str(row['Email']).strip()
            phone = str(row['Số điện thoại']).strip() if pd.notna(row['Số điện thoại']) else ""
            department = str(row['Bộ phận']).strip() if pd.notna(row['Bộ phận']) else ""
            position = str(row['Chức vụ']).strip() if pd.notna(row['Chức vụ']) else ""

            # Kiểm tra xem nhân viên đã tồn tại theo mã chưa
            employee = Employee.query.filter_by(employee_code=emp_code).first()
            
            if employee:
                # Cập nhật thông tin nếu đã tồn tại
                employee.full_name = full_name
                employee.email = email
                employee.phone = phone
                employee.department = department
                employee.position = position
                update_count += 1
            else:
                # Thêm mới nếu chưa có
                new_emp = Employee(
                    employee_code=emp_code,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    department=department,
                    position=position
                )
                db.session.add(new_emp)
                success_count += 1

        db.session.commit()
        return True, f"Import thành công! Thêm mới: {success_count}, Cập nhật: {update_count} nhân viên."
    
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi xử lý file Excel: {str(e)}"