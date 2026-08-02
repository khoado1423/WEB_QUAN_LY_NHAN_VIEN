import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from app import db
from app.models.employee import Employee
from app.services.excel_service import import_employees_from_excel
from sheets_helper import get_sheet_data, append_sheet_data

employee_bp = Blueprint('employee', __name__, url_prefix='/employees')

@employee_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '', type=str)
    if search:
        employees = Employee.query.filter(
            (Employee.full_name.ilike(f'%{search}%')) | 
            (Employee.employee_code.ilike(f'%{search}%'))
        ).all()
    else:
        employees = Employee.query.all()
    return render_template('employee/index.html', employees=employees, search=search)

@employee_bp.route('/download-template')
@login_required
def download_template():
    try:
        # Lấy dữ liệu mới nhất từ tab "NhanVien" trên Google Sheet mẫu
        sheet_values = get_sheet_data("NhanVien")
        if sheet_values and len(sheet_values) > 0:
            header = sheet_values[0]
            rows = sheet_values[1:]
            df = pd.DataFrame(rows, columns=header)
        else:
            flash('Không lấy được dữ liệu từ Google Sheet mẫu, dùng dữ liệu mặc định.', 'warning')
            raise ValueError("Sheet trống")
    except Exception as e:
        # Nếu lỗi kết nối Google Sheet, dùng dữ liệu cứng dự phòng để web không bị sập
        data = {
            'employee_code': ['NV001', 'NV002', 'NV003', 'NV004', 'NV005'],
            'full_name': ['Nguyễn Văn An', 'Trần Thị Bình', 'Lê Hoàng Cường', 'Phạm Thị Dung', 'Hoàng Văn Em'],
            'email': ['an.nguyen@company.com', 'binh.tran@company.com', 'cuong.le@company.com', 'dung.pham@company.com', 'em.hoang@company.com'],
            'department': ['Kỹ thuật', 'Nhân sự', 'Kinh doanh', 'Kế toán', 'Marketing']
        }
        df = pd.DataFrame(data)

    instance_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../instance'))
    os.makedirs(instance_dir, exist_ok=True)
    file_path = os.path.join(instance_dir, 'mau_nhan_vien.xlsx')
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True, download_name='mau_nhan_vien.xlsx')

@employee_bp.route('/import', methods=['POST'])
@login_required
def import_excel():
    if 'file' not in request.files:
        flash('Không tìm thấy file tải lên!', 'danger')
        return redirect(url_for('employee.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Chưa chọn file Excel!', 'warning')
        return redirect(url_for('employee.index'))
    
    if file:
        instance_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../instance'))
        os.makedirs(instance_dir, exist_ok=True)
        file_path = os.path.join(instance_dir, file.filename)
        file.save(file_path)
        
        success, message = import_employees_from_excel(file_path)
        flash(message, 'success' if success else 'danger')

        # Đồng bộ dữ liệu vừa import lên Google Sheet mẫu (tab "NhanVien")
        if success:
            try:
                df_imported = pd.read_excel(file_path)
                rows_to_sync = df_imported.astype(str).values.tolist()
                if rows_to_sync:
                    append_sheet_data("NhanVien", rows_to_sync)
            except Exception as e:
                flash(f'Đã lưu vào database nhưng lỗi khi đồng bộ lên Google Sheet: {e}', 'warning')

        if os.path.exists(file_path):
            os.remove(file_path)
    
    return redirect(url_for('employee.index'))

@employee_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    emp = Employee.query.get_or_404(id)
    if request.method == 'POST':
        emp.employee_code = request.form.get('employee_code')
        emp.full_name = request.form.get('full_name')
        emp.email = request.form.get('email')
        emp.department = request.form.get('department')
        
        db.session.commit()
        flash('Đã cập nhật thông tin nhân viên thành công!', 'success')
        return redirect(url_for('employee.index'))
        
    return render_template('employee/edit.html', emp=emp)

@employee_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    flash('Đã xóa nhân viên thành công!', 'success')
    return redirect(url_for('employee.index'))

@employee_bp.route('/delete-all', methods=['POST'])
@login_required
def delete_all():
    try:
        num_rows_deleted = db.session.query(Employee).delete()
        db.session.commit()
        flash(f'Đã xóa toàn bộ {num_rows_deleted} nhân viên thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Lỗi khi xóa toàn bộ dữ liệu nhân viên (có thể vướng khóa ngoại lịch trình)!', 'danger')
    return redirect(url_for('employee.index'))

from data_helper import get_all_employees

@employee_bp.route('/sync-from-sheet', methods=['POST'])
@login_required
def sync_from_sheet():
    try:
        sheet_rows = get_all_employees()
        success_count = 0
        update_count = 0
        for row in sheet_rows:
            code = str(row.get('employee_code', '')).strip()
            name = str(row.get('full_name', '')).strip()
            email = str(row.get('email', '')).strip()
            department = str(row.get('department', '')).strip()
            if not code:
                continue

            employee = Employee.query.filter_by(employee_code=code).first()
            if employee:
                employee.full_name = name
                employee.email = email
                employee.department = department
                update_count += 1
            else:
                new_emp = Employee(employee_code=code, full_name=name, email=email, department=department)
                db.session.add(new_emp)
                success_count += 1

        db.session.commit()
        flash(f'Đồng bộ thành công! Thêm mới: {success_count}, Cập nhật: {update_count} nhân viên.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi đồng bộ từ Google Sheet: {e}', 'danger')
    return redirect(url_for('employee.index'))