from app import db

class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(50), unique=True, nullable=False)  # Mã công việc
    title = db.Column(db.String(150), nullable=False)                 # Tên công việc
    description = db.Column(db.Text, nullable=True)                    # Mô tả
    priority = db.Column(db.String(20), default='Trung bình')            # Độ ưu tiên (Thấp, Trung bình, Cao)
    duration = db.Column(db.Float, nullable=True)                      # Thời lượng (giờ)

    # Quan hệ với bảng Schedule
    schedules = db.relationship('Schedule', backref='task', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Task {self.title}>'