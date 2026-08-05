from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Kiểm tra trạng thái phê duyệt tài khoản
            if user.role != 'Admin' and user.status != 'Active':
                flash('Tài khoản của bạn đang chờ Admin phê duyệt!', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')
            
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        form_data = request.form
        
        employee_id = request.form.get('employee_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # 1. Kiểm tra các trường bắt buộc
        if not employee_id:
            errors['employee_id'] = 'Vui lòng nhập Mã nhân viên!'
        if not full_name:
            errors['full_name'] = 'Vui lòng nhập Họ và Tên!'
            
        # 2. Kiểm tra Email
        if not email:
            errors['email'] = 'Vui lòng nhập Email!'
        elif User.query.filter_by(username=email).first():
            errors['email'] = 'Email/Tài khoản này đã được sử dụng!'

        # 3. Kiểm tra Mật khẩu
        if not password:
            errors['password'] = 'Vui lòng nhập Mật khẩu!'
        elif len(password) < 6:
            errors['password'] = 'Mật khẩu phải có ít nhất 6 ký tự!'

        # Nếu có lỗi -> Trả về form giữ nguyên dữ liệu + tô đỏ ô sai
        if errors:
            flash('Thông tin chưa hợp lệ, vui lòng kiểm tra lại các ô màu đỏ!', 'danger')
            return render_template('auth/register.html', errors=errors, form_data=form_data)

        # Tạo tài khoản mới với trạng thái Pending
        new_user = User(username=email, email=email, role='Nhân viên', status='Pending')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng chờ Admin phê duyệt để có thể đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', errors={}, form_data={})


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('auth.login'))