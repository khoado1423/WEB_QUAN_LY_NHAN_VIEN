from app import db
from datetime import date

class Schedule(db.Model):
    __tablename__ = 'schedules'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False, default=date.today)  # Ngày làm việc
    shift = db.Column(db.String(20), nullable=False)                     # Ca làm việc ('Ca sáng', 'Ca chiều')
    status = db.Column(db.String(50), nullable=False, default='Chưa làm') # Trạng thái công việc

    # Bổ sung tính năng Điểm danh & Nộp file báo cáo (PDF, Word, Excel)
    attendance_code = db.Column(db.String(50), nullable=True)            # Mã điểm danh do Admin tạo
    attendance_status = db.Column(db.String(50), default='Chưa điểm danh') # Trạng thái điểm danh
    report_file = db.Column(db.String(255), nullable=True)               # Đường dẫn file đính kèm

    def __repr__(self):
        return f'<Schedule Emp:{self.employee_id} Date:{self.work_date} Shift:{self.shift} Status:{self.status}>'