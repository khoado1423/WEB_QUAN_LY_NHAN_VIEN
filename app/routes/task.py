import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from app import db
from app.models.task import Task
from app.services.excel_service import import_tasks_from_excel
from sheets_helper import get_sheet_data, append_sheet_data

task_bp = Blueprint('task', __name__, url_prefix='/tasks')

@task_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '', type=str)
    if search:
        tasks = Task.query.filter(
            (Task.title.ilike(f'%{search}%')) | 
            (Task.task_code.ilike(f'%{search}%'))
        ).all()
    else:
        tasks = Task.query.all()
    return render_template('task/index.html', tasks=tasks, search=search)

@task_bp.route('/download-template')
@login_required
def download_template():
    try:
        # Lấy dữ liệu mới nhất từ tab "CongViec" trên Google Sheet mẫu
        sheet_values = get_sheet_data("CongViec")
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
            'task_code': ['CV001', 'CV002', 'CV003', 'CV004'],
            'title': ['Lập báo cáo doanh thu', 'Kiểm tra lỗi hệ thống', 'Họp định kỳ tuần', 'Tối ưu hóa cơ sở dữ liệu'],
            'description': ['Làm báo cáo tài chính tháng gửi ban giám đốc', 'Fix bug trên server production', 'Họp bàn tiến độ triển khai dự án mới', 'Index lại các bảng dữ liệu lớn'],
            'priority': ['Cao', 'Trung bình', 'Thấp', 'Cao'],
            'duration': [4.0, 2.0, 1.5, 3.0]
        }
        df = pd.DataFrame(data)

    instance_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../instance'))
    os.makedirs(instance_dir, exist_ok=True)
    file_path = os.path.join(instance_dir, 'mau_cong_viec.xlsx')
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True, download_name='mau_cong_viec.xlsx')

@task_bp.route('/import', methods=['POST'])
@login_required
def import_excel():
    if 'file' not in request.files:
        flash('Không tìm thấy file tải lên!', 'danger')
        return redirect(url_for('task.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Chưa chọn file Excel!', 'warning')
        return redirect(url_for('task.index'))
    
    if file:
        instance_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../instance'))
        os.makedirs(instance_dir, exist_ok=True)
        file_path = os.path.join(instance_dir, file.filename)
        file.save(file_path)
        
        success, message = import_tasks_from_excel(file_path)
        flash(message, 'success' if success else 'danger')

        # Đồng bộ dữ liệu vừa import lên Google Sheet mẫu (tab "CongViec")
        if success:
            try:
                df_imported = pd.read_excel(file_path)
                rows_to_sync = df_imported.astype(str).values.tolist()
                if rows_to_sync:
                    append_sheet_data("CongViec", rows_to_sync)
            except Exception as e:
                flash(f'Đã lưu vào database nhưng lỗi khi đồng bộ lên Google Sheet: {e}', 'warning')

        if os.path.exists(file_path):
            os.remove(file_path)
            
    return redirect(url_for('task.index'))

@task_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.task_code = request.form.get('task_code')
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        task.duration = float(request.form.get('duration', 1.0))
        
        db.session.commit()
        flash('Đã cập nhật thông tin công việc thành công!', 'success')
        return redirect(url_for('task.index'))
        
    return render_template('task/edit.html', task=task)

@task_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('Đã xóa công việc thành công!', 'success')
    return redirect(url_for('task.index'))

@task_bp.route('/delete-all', methods=['POST'])
@login_required
def delete_all():
    try:
        num_rows_deleted = db.session.query(Task).delete()
        db.session.commit()
        flash(f'Đã xóa toàn bộ {num_rows_deleted} công việc thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Lỗi khi xóa toàn bộ công việc (có thể vướng khóa ngoại lịch trình)!', 'danger')
    return redirect(url_for('task.index'))