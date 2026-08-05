import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from app import db
from app.models.employee import Employee
from sheets_helper import get_sheet_data, append_sheet_data
from data_helper import get_all_employees

employee_bp = Blueprint('employee', __name__, url_prefix='/employees')


def clean_val(val):
    """Hàm chuẩn hóa dữ liệu: Chuyển NaN / Chuỗi rỗng / 'nan' về None (NULL trong DB)"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ('nan', 'none', 'null'):
        return None
    return s


@employee_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '', type=str).strip()
    if search:
        employees = Employee.query.filter(
            (Employee.full_name.ilike(f'%{search}%')) | 
            (Employee.employee_code.ilike(f'%{search}%')) |
            (Employee.email.ilike(f'%{search}%'))
        ).all()
    else:
        employees = Employee.query.all()
    return render_template('employee/index.html', employees=employees, search=search)


@employee_bp.route('/download-template')
@login_required
def download_template():
    try:
        sheet_values = get_sheet_data("NhanVien")
        if sheet_values and len(sheet_values) > 0:
            header = sheet_values[0]
            rows = sheet_values[1:]
            df = pd.DataFrame(rows, columns=header)
        else:
            flash('Không lấy được dữ liệu từ Google Sheet mẫu, dùng dữ liệu mặc định.', 'warning')
            raise ValueError("Sheet trống")
    except Exception:
        data = {
            'employee_code': ['NV001', 'NV002', 'NV003', 'NV004', 'NV005'],
            'full_name': ['Nguyễn Văn An', 'Trần Thị Bình', 'Lê Hoàng Cường', 'Phạm Thị Dung', 'Hoàng Văn Em'],
            'email': ['an.nguyen@company.com', 'binh.tran@company.com', 'cuong.le@company.com', 'dung.pham@company.com', 'em.hoang@company.com'],
            'phone': ['0901234561', '0901234562', '0901234563', '0901234564', '0901234565'],
            'department': ['Kỹ thuật', 'Nhân sự', 'Kinh doanh', 'Kế toán', 'Marketing'],
            'position': ['Nhân viên', 'Nhân viên', 'Trưởng phòng', 'Nhân viên', 'Nhân viên']
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
        try:
            # Đọc file Excel trực tiếp bằng Pandas
            df = pd.read_excel(file)
            df.columns = [str(c).strip() for c in df.columns]

            success_count = 0
            update_count = 0

            for _, row in df.iterrows():
                # Tự động nhận diện các tên cột phổ biến trong file Excel
                code = clean_val(row.get('Mã NV') or row.get('employee_code') or row.get('Mã nhân viên'))
                name = clean_val(row.get('Họ và Tên') or row.get('full_name') or row.get('Họ tên'))
                email = clean_val(row.get('Email') or row.get('email') or row.get('Email liên hệ'))
                phone = clean_val(row.get('Số điện thoại') or row.get('phone') or row.get('SĐT'))
                department = clean_val(row.get('Phòng ban') or row.get('department'))
                position = clean_val(row.get('Chức vụ') or row.get('position'))

                # Bỏ qua dòng trống không có dữ liệu định danh
                if not code and not email and not name:
                    continue

                # Tim nhân viên theo Mã NV hoặc Email trong DB
                emp = None
                if code:
                    emp = Employee.query.filter_by(employee_code=code).first()
                if not emp and email:
                    emp = Employee.query.filter_by(email=email).first()

                # Kiểm tra tránh xung đột Email Unique nếu Email thuộc về 1 NV khác
                if email:
                    existing_email_emp = Employee.query.filter_by(email=email).first()
                    if existing_email_emp and (not emp or existing_email_emp.id != emp.id):
                        email = None  # Bỏ email để tránh crash UNIQUE constraint

                if emp:
                    # Cập nhật thông tin nhân viên cũ
                    if code: emp.employee_code = code
                    if name: emp.full_name = name
                    if email is not None or emp.email is None: emp.email = email
                    if hasattr(emp, 'phone') and phone: emp.phone = phone
                    if department: emp.department = department
                    if hasattr(emp, 'position') and position: emp.position = position
                    update_count += 1
                else:
                    # Tạo nhân viên mới
                    kwargs = {
                        'employee_code': code,
                        'full_name': name or 'Chưa nhập tên',
                        'email': email,
                        'department': department
                    }
                    if hasattr(Employee, 'phone'): kwargs['phone'] = phone
                    if hasattr(Employee, 'position'): kwargs['position'] = position

                    new_emp = Employee(**kwargs)
                    db.session.add(new_emp)
                    success_count += 1

            db.session.commit()
            flash(f'Import thành công! Thêm mới: {success_count}, Cập nhật: {update_count} nhân viên.', 'success')

            # Đồng bộ lên Google Sheet nếu cần
            try:
                file.seek(0)
                df_imported = pd.read_excel(file)
                rows_to_sync = df_imported.fillna('').astype(str).values.tolist()
                if rows_to_sync:
                    append_sheet_data("NhanVien", rows_to_sync)
            except Exception as sync_err:
                flash(f'Lưu Database thành công nhưng lỗi khi đồng bộ lên Google Sheet: {sync_err}', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi xử lý file Excel: {e}', 'danger')

    return redirect(url_for('employee.index'))


@employee_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    emp = Employee.query.get_or_404(id)
    if request.method == 'POST':
        new_email = clean_val(request.form.get('email'))
        
        # Kiểm tra trùng email nếu người dùng thay đổi
        if new_email and new_email != emp.email:
            existing = Employee.query.filter_by(email=new_email).first()
            if existing:
                flash('Email này đã được sử dụng bởi nhân viên khác!', 'danger')
                return render_template('employee/edit.html', emp=emp)

        emp.employee_code = clean_val(request.form.get('employee_code'))
        emp.full_name = clean_val(request.form.get('full_name'))
        emp.email = new_email
        emp.department = clean_val(request.form.get('department'))
        if hasattr(emp, 'phone'):
            emp.phone = clean_val(request.form.get('phone'))
        if hasattr(emp, 'position'):
            emp.position = clean_val(request.form.get('position'))
        
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
    except Exception:
        db.session.rollback()
        flash('Lỗi khi xóa toàn bộ dữ liệu nhân viên (có thể vướng khóa ngoại lịch trình)!', 'danger')
    return redirect(url_for('employee.index'))


@employee_bp.route('/sync-from-sheet', methods=['POST'])
@login_required
def sync_from_sheet():
    try:
        sheet_rows = get_all_employees()
        success_count = 0
        update_count = 0
        for row in sheet_rows:
            code = clean_val(row.get('employee_code'))
            name = clean_val(row.get('full_name'))
            email = clean_val(row.get('email'))
            department = clean_val(row.get('department'))
            phone = clean_val(row.get('phone'))
            position = clean_val(row.get('position'))

            if not code and not email:
                continue

            employee = None
            if code:
                employee = Employee.query.filter_by(employee_code=code).first()
            if not employee and email:
                employee = Employee.query.filter_by(email=email).first()

            if email:
                dup_email = Employee.query.filter_by(email=email).first()
                if dup_email and (not employee or dup_email.id != employee.id):
                    email = None

            if employee:
                if name: employee.full_name = name
                if email is not None: employee.email = email
                if department: employee.department = department
                if hasattr(employee, 'phone') and phone: employee.phone = phone
                if hasattr(employee, 'position') and position: employee.position = position
                update_count += 1
            else:
                kwargs = {
                    'employee_code': code,
                    'full_name': name or 'Chưa nhập tên',
                    'email': email,
                    'department': department
                }
                if hasattr(Employee, 'phone'): kwargs['phone'] = phone
                if hasattr(Employee, 'position'): kwargs['position'] = position

                new_emp = Employee(**kwargs)
                db.session.add(new_emp)
                success_count += 1

        db.session.commit()
        flash(f'Đồng bộ thành công! Thêm mới: {success_count}, Cập nhật: {update_count} nhân viên.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi đồng bộ từ Google Sheet: {e}', 'danger')
    return redirect(url_for('employee.index'))