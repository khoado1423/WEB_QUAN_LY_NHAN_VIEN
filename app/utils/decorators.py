from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """
    Chặn truy cập nếu người dùng chưa đăng nhập hoặc không phải Admin.
    Dùng thay cho việc lặp lại:
        if getattr(current_user, 'role', None) != 'Admin': ...
    ở đầu mỗi route quản trị.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'Admin':
            flash('Bạn không có quyền truy cập chức năng này!', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
