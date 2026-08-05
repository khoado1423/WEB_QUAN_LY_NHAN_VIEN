import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from app import db
from app.models.task import Task
from sheets_helper import get_sheet_data, append_sheet_data
from data_helper import get_all_tasks

task_bp = Blueprint('task', __name__, url_prefix='/tasks')


def clean_val(val):
    """Hàm chuẩn hóa dữ liệu: Chuyển NaN / Chuỗi rỗng / 'nan' về None (NULL trong DB)"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ('nan', 'none', 'null'):
        return None
    return s


@task_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '', type=str).strip()
    
    query = Task.query
    if search:
        query = query.filter(
            (Task.title.ilike(f'%{search}%')) | 
            (Task.task_code.ilike(f'%{search}%'))
        )
    
    all_tasks = query.order_by(Task.id.desc()).all()
    
    # Tối ưu: Lọc bỏ trùng lặp, 1 công việc chỉ hiển thị 1 lần duy nhất trên giao diện
    seen_keys = set()
    unique_tasks = []
    for task in all_tasks:
        key = clean_val(task.task_code) or clean_val(task.title) or str(task.id)
        key_lower = key.lower()
        if key_lower not in seen_keys:
            seen_keys.add(key_lower)
            unique_tasks.append(task)
            
    return render_template('task/index.html', tasks=unique_tasks, search=search)


@task_bp.route('/download-template')
@login_required
def download_template():
    try:
        sheet_values = get_sheet_data("CongViec")
        if sheet_values and len(sheet_values) > 0:
            header = sheet_values[0]
            rows = sheet_values[1:]
            df = pd.DataFrame(rows, columns=header)
        else:
            flash('Không lấy được dữ liệu từ Google Sheet mẫu, dùng dữ liệu mặc định.', 'warning')
            raise ValueError("Sheet trống")
    except Exception:
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
        try:
            # Đọc file Excel trực tiếp bằng Pandas
            df = pd.read_excel(file)
            df.columns = [str(c).strip() for c in df.columns]

            success_count = 0
            update_count = 0

            for _, row in df.iterrows():
                code = clean_val(row.get('Mã CV') or row.get('task_code') or row.get('Mã công việc'))
                title = clean_val(row.get('Tên công việc') or row.get('title') or row.get('Tên CV'))
                description = clean_val(row.get('Mô tả') or row.get('description'))
                priority = clean_val(row.get('Độ ưu tiên') or row.get('priority')) or 'Trung bình'
                
                try:
                    dur_raw = row.get('Thời lượng') or row.get('duration') or row.get('Số giờ')
                    duration = float(dur_raw) if dur_raw and not pd.isna(dur_raw) else 1.0
                except (ValueError, TypeError):
                    duration = 1.0

                if not code and not title:
                    continue

                # Tìm công việc đã tồn tại theo Mã CV hoặc Tên CV
                task = None
                if code:
                    task = Task.query.filter_by(task_code=code).first()
                if not task and title:
                    task = Task.query.filter_by(title=title).first()

                if task:
                    # Cập nhật thông tin công việc đã có
                    if code: task.task_code = code
                    if title: task.title = title
                    if description: task.description = description
                    task.priority = priority
                    task.duration = duration
                    update_count += 1
                else:
                    # Thêm công việc mới
                    new_task = Task(
                        task_code=code,
                        title=title or 'Công việc chưa đặt tên',
                        description=description,
                        priority=priority,
                        duration=duration
                    )
                    db.session.add(new_task)
                    success_count += 1

            db.session.commit()
            flash(f'Import thành công! Thêm mới: {success_count}, Cập nhật: {update_count} công việc.', 'success')

            # Đồng bộ lên Google Sheet nếu cần
            try:
                file.seek(0)
                df_imported = pd.read_excel(file)
                rows_to_sync = df_imported.fillna('').astype(str).values.tolist()
                if rows_to_sync:
                    append_sheet_data("CongViec", rows_to_sync)
            except Exception as sync_err:
                flash(f'Lưu Database thành công nhưng lỗi khi đồng bộ lên Google Sheet: {sync_err}', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi xử lý file Excel công việc: {e}', 'danger')

    return redirect(url_for('task.index'))


@task_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.task_code = clean_val(request.form.get('task_code'))
        task.title = clean_val(request.form.get('title'))
        task.description = clean_val(request.form.get('description'))
        task.priority = clean_val(request.form.get('priority')) or 'Trung bình'
        
        try:
            task.duration = float(request.form.get('duration', 1.0))
        except (ValueError, TypeError):
            task.duration = 1.0
        
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
    except Exception:
        db.session.rollback()
        flash('Lỗi khi xóa toàn bộ công việc (có thể vướng khóa ngoại lịch trình)!', 'danger')
    return redirect(url_for('task.index'))


@task_bp.route('/sync-from-sheet', methods=['POST'])
@login_required
def sync_from_sheet():
    try:
        sheet_rows = get_all_tasks()
        success_count = 0
        update_count = 0
        for row in sheet_rows:
            code = clean_val(row.get('task_code'))
            title = clean_val(row.get('title'))
            description = clean_val(row.get('description'))
            priority = clean_val(row.get('priority')) or 'Trung bình'
            
            try:
                duration = float(row.get('duration', 1.0))
            except (ValueError, TypeError):
                duration = 1.0

            if not code and not title:
                continue

            task = None
            if code:
                task = Task.query.filter_by(task_code=code).first()
            if not task and title:
                task = Task.query.filter_by(title=title).first()

            if task:
                if code: task.task_code = code
                if title: task.title = title
                if description: task.description = description
                task.priority = priority
                task.duration = duration
                update_count += 1
            else:
                new_task = Task(
                    task_code=code,
                    title=title or 'Công việc chưa đặt tên',
                    description=description,
                    priority=priority,
                    duration=duration
                )
                db.session.add(new_task)
                success_count += 1

        db.session.commit()
        flash(f'Đồng bộ thành công! Thêm mới: {success_count}, Cập nhật: {update_count} công việc.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi đồng bộ từ Google Sheet: {e}', 'danger')
    return redirect(url_for('task.index'))