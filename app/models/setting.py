from app import db


class SystemSetting(db.Model):
    """
    Lưu cấu hình hệ thống dạng key-value (ví dụ: system_name).
    Cho phép mở rộng thêm cài đặt mới sau này mà không cần thêm cột vào bảng users.
    """
    __tablename__ = 'system_settings'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)

    @staticmethod
    def get(key, default=None):
        """Lấy giá trị cài đặt theo key. Trả về default nếu chưa tồn tại."""
        setting = SystemSetting.query.filter_by(key=key).first()
        return setting.value if setting and setting.value is not None else default

    @staticmethod
    def set(key, value):
        """Tạo mới hoặc cập nhật giá trị cài đặt theo key."""
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.session.add(setting)
        return setting

    def __repr__(self):
        return f'<SystemSetting {self.key}={self.value}>'
