from app import db

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(50), unique=True, nullable=False) # Mã nhân viên
    full_name = db.Column(db.String(100), nullable=False)                 # Họ tên
    email = db.Column(db.String(120), unique=True, nullable=False)        # Email
    phone = db.Column(db.String(20), nullable=True)                       # Số điện thoại
    department = db.Column(db.String(100), nullable=True)                 # Bộ phận
    position = db.Column(db.String(100), nullable=True)                   # Chức vụ

    # Quan hệ với bảng Schedule
    schedules = db.relationship('Schedule', backref='employee', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Employee {self.full_name}>'