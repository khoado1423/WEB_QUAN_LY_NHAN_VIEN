import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.schedule import Schedule
from app.models.employee import Employee
from app.models.task import Task
from app.models.user import User
from app.services.auto_scheduler import auto_assign_tasks, auto_assign_single_day
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedules')

# Danh sách định dạng file báo cáo được hỗ trợ
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@schedule_bp.route('/')
@login_required
def index():
    schedules = Schedule.query.all()
    return render_template('schedule/index.html', schedules=schedules)

@schedule_bp.route('/week', methods=['GET'])
@login_required
def week_schedule():
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.today().date()
    else:
        selected_date = datetime.today().date()
        
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    schedules = Schedule.query.filter(Schedule.work_date >= start_of_week, Schedule.work_date <= end_of_week).all()
    
    return render_template('schedule/week_schedule.html', 
                           schedules=schedules, 
                           start_of_week=start_of_week, 
                           end_of_week=end_of_week,
                           selected_date=selected_date,
                           timedelta=timedelta)

@schedule_bp.route('/add', methods=['POST'])
@login_required
def add():
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('schedule.index'))

    employee_id = request.form.get('employee_id')
    task_id = request.form.get('task_id')
    work_date_str = request.form.get('work_date')
    shift = request.form.get('shift')

    if not employee_id or not task_id or not work_date_str or not shift:
        flash('Vui lòng điền đầy đủ thông tin phân công!', 'warning')
        return redirect(request.referrer or url_for('schedule.index'))

    work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()

    existing = Schedule.query.filter_by(employee_id=employee_id, work_date=work_date, shift=shift).first()
    if existing:
        existing.task_id = task_id
        flash('Đã cập nhật công việc cho ca làm việc đã chọn!', 'success')
    else:
        new_schedule = Schedule(
            employee_id=employee_id,
            task_id=task_id,
            work_date=work_date,
            shift=shift
        )
        db.session.add(new_schedule)
        flash('Đã lưu phân công thành công!', 'success')

    db.session.commit()
    return redirect(request.referrer or url_for('schedule.index'))

@schedule_bp.route('/auto-assign-week', methods=['POST'])
@login_required
def auto_assign_week():
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền thực hiện chức năng này!', 'danger')
        return redirect(url_for('schedule.index'))

    start_date_str = request.form.get('start_date')
    start_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Định dạng ngày không hợp lệ!', 'danger')
            return redirect(url_for('schedule.index'))

    success, message = auto_assign_tasks(start_date=start_date)
    flash(message, 'success' if success else 'danger')
        
    return redirect(url_for('schedule.index'))

@schedule_bp.route('/auto-assign-day', methods=['POST'])
@login_required
def auto_assign_day():
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền thực hiện chức năng này!', 'danger')
        return redirect(url_for('schedule.index'))

    date_str = request.form.get('work_date')
    target_date = None
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Định dạng ngày không hợp lệ!', 'danger')
            return redirect(url_for('schedule.index'))

    success, message = auto_assign_single_day(target_date=target_date)
    flash(message, 'success' if success else 'danger')
        
    return redirect(url_for('schedule.index'))

@schedule_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Nhân viên chỉ có quyền xem lịch, không được phép chỉnh sửa!', 'danger')
        return redirect(url_for('schedule.index'))

    schedule = Schedule.query.get_or_404(id)
    employees = Employee.query.all()
    tasks = Task.query.all()
    
    if request.method == 'POST':
        schedule.employee_id = request.form.get('employee_id')
        schedule.task_id = request.form.get('task_id')
        
        work_date_str = request.form.get('work_date')
        if work_date_str:
            schedule.work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
            
        schedule.shift = request.form.get('shift')
        schedule.status = request.form.get('status', 'Chưa làm')
        
        db.session.commit()
        flash('Đã cập nhật lịch phân công thành công!', 'success')
        return redirect(url_for('schedule.index'))
        
    return render_template('schedule/edit.html', schedule=schedule, employees=employees, tasks=tasks)

@schedule_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền xóa dữ liệu!', 'danger')
        return redirect(url_for('schedule.index'))

    schedule = Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    flash('Đã xóa lịch phân công thành công!', 'success')
    return redirect(url_for('schedule.index'))

@schedule_bp.route('/delete-all', methods=['POST'])
@login_required
def delete_all():
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('schedule.index'))

    try:
        num_rows_deleted = db.session.query(Schedule).delete()
        db.session.commit()
        flash(f'Đã xóa toàn bộ {num_rows_deleted} lịch phân công thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Lỗi khi xóa toàn bộ dữ liệu lịch trình!', 'danger')
    return redirect(url_for('schedule.index'))

@schedule_bp.route('/reports', methods=['GET'])
@login_required
def reports():
    status_filter = request.args.get('status', '')

    query = Schedule.query
    if status_filter:
        query = query.filter(Schedule.status == status_filter)

    schedules = query.all()
    
    total_schedules = Schedule.query.count()
    completed_schedules = Schedule.query.filter_by(status='Hoàn thành').count()
    pending_schedules = total_schedules - completed_schedules
    
    completion_rate = round((completed_schedules / total_schedules * 100), 1) if total_schedules > 0 else 0
    
    return render_template('schedule/reports.html', 
                           total=total_schedules, 
                           completed=completed_schedules, 
                           pending=pending_schedules,
                           completion_rate=completion_rate,
                           schedules=schedules,
                           status_filter=status_filter)

# ==========================================
# TÍNH NĂNG ĐIỂM DANH VÀ TẢI FILE BÁO CÁO
# ==========================================

@schedule_bp.route('/generate-attendance-code/<int:id>', methods=['POST'])
@login_required
def generate_attendance_code(id):
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('schedule.reports'))
    
    sch = Schedule.query.get_or_404(id)
    code_input = request.form.get('attendance_code')
    
    if code_input:
        sch.attendance_code = code_input.strip()
        db.session.commit()
        flash('Đã thiết lập mã điểm danh thành công!', 'success')
    else:
        flash('Vui lòng nhập mã điểm danh hợp lệ.', 'warning')
        
    return redirect(url_for('schedule.reports'))

@schedule_bp.route('/attendance/<int:id>', methods=['POST'])
@login_required
def attendance(id):
    sch = Schedule.query.get_or_404(id)
    entered_code = request.form.get('attendance_code')
    
    if not sch.attendance_code:
        flash('Ca làm này chưa được Admin thiết lập mã điểm danh!', 'warning')
        return redirect(url_for('schedule.reports'))
    
    if entered_code and entered_code.strip() == sch.attendance_code:
        sch.attendance_status = 'Đã điểm danh'
        db.session.commit()
        flash('Điểm danh thành công!', 'success')
    else:
        flash('Mã điểm danh không chính xác, vui lòng kiểm tra lại!', 'danger')
        
    return redirect(url_for('schedule.reports'))

@schedule_bp.route('/upload-report/<int:id>', methods=['POST'])
@login_required
def upload_report(id):
    sch = Schedule.query.get_or_404(id)
    
    if 'report_file' not in request.files:
        flash('Không tìm thấy tệp tin tải lên.', 'danger')
        return redirect(url_for('schedule.reports'))
    
    file = request.files['report_file']
    
    if file.filename == '':
        flash('Bạn chưa chọn tệp báo cáo.', 'warning')
        return redirect(url_for('schedule.reports'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"schedule_{sch.id}_{filename}"
        
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        sch.report_file = f"uploads/{unique_filename}"
        db.session.commit()
        
        flash('Nộp báo cáo và đính kèm file thành công!', 'success')
    else:
        flash('Định dạng file không được hỗ trợ! Chỉ chấp nhận file PDF, Word (.doc, .docx), Excel (.xls, .xlsx).', 'danger')
        
    return redirect(url_for('schedule.reports'))

# ==========================================
# CÀI ĐẶT HỆ THỐNG & TÀI KHOẢN (ĐÃ TỐI ƯU ĐẦY ĐỦ)
# ==========================================

@schedule_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if getattr(current_user, 'role', None) != 'Admin':
        flash('Bạn không có quyền truy cập trang cài đặt hệ thống!', 'danger')
        return redirect(url_for('schedule.index'))

    users = User.query.all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 1. Thêm tài khoản nhân viên mới
        if action == 'create_user':
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            
            if not new_username or not new_password:
                flash('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!', 'warning')
            elif User.query.filter_by(username=new_username).first():
                flash('Tên đăng nhập này đã tồn tại!', 'danger')
            else:
                new_user = User(username=new_username, role='Nhân viên')
                new_user.set_password(new_password)
                db.session.add(new_user)
                db.session.commit()
                flash(f'Đã thêm tài khoản nhân viên "{new_username}" thành công!', 'success')
                
            return redirect(url_for('schedule.settings'))
            
        # 2. Cập nhật thông tin hệ thống & Thay đổi mật khẩu Admin hiện tại
        system_name = request.form.get('system_name')
        admin_email = request.form.get('admin_email')
        new_admin_password = request.form.get('new_admin_password')
        
        if admin_email and hasattr(current_user, 'email'):
            current_user.email = admin_email
            
        if new_admin_password and new_admin_password.strip() != "":
            current_user.set_password(new_admin_password.strip())
            flash('Đã thay đổi mật khẩu tài khoản quản trị thành công!', 'success')
            
        db.session.commit()
        flash('Đã lưu cài đặt hệ thống thành công!', 'success')
        return redirect(url_for('schedule.settings'))

    return render_template('schedule/settings.html', users=users)