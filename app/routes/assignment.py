from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.task import Task

assignment_bp = Blueprint('assignment', __name__, url_prefix='/assignments')

@assignment_bp.route('/')
@login_required
def index():
    assignments = Assignment.query.all()
    employees = Employee.query.all()
    tasks = Task.query.all()
    return render_template('assignment/index.html', assignments=assignments, employees=employees, tasks=tasks)

@assignment_bp.route('/add', methods=['POST'])
@login_required
def add():
    employee_id = request.form.get('employee_id')
    task_id = request.form.get('task_id')
    status = request.form.get('status', 'Đang thực hiện')
    
    if not employee_id or not task_id:
        flash('Vui lòng chọn đầy đủ nhân viên và công việc!', 'warning')
        return redirect(url_for('assignment.index'))
        
    new_assignment = Assignment(employee_id=employee_id, task_id=task_id, status=status)
    db.session.add(new_assignment)
    db.session.commit()
    
    flash('Đã phân công công việc thành công!', 'success')
    return redirect(url_for('assignment.index'))

@assignment_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Đã xóa phân công thành công!', 'success')
    return redirect(url_for('assignment.index'))