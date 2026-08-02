from app import db
from datetime import datetime

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    assigned_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Đang thực hiện') # Đang thực hiện, Hoàn thành, Tạm hoãn
    
    # Quan hệ
    employee = db.relationship('Employee', backref=db.backref('assignments', cascade='all, delete-orphan'))
    task = db.relationship('Task', backref=db.backref('assignments', cascade='all, delete-orphan'))