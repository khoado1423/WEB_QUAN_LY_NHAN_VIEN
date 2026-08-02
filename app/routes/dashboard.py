from datetime import date, timedelta
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.employee import Employee
from app.models.task import Task
from app.models.schedule import Schedule

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    total_employees = Employee.query.count()
    total_tasks = Task.query.count()
    total_schedules = Schedule.query.count()

    employees = Employee.query.all()
    tasks = Task.query.all()
    
    today = date.today()

    week_offset = request.args.get('week_offset', 0, type=int)
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    
    week_days = [(start_of_week + timedelta(days=i)) for i in range(7)]

    schedules = Schedule.query.all()
    today_str = today.strftime('%Y-%m-%d')
    today_schedules = [s for s in schedules if s.work_date and s.work_date.strftime('%Y-%m-%d') == today_str]

    return render_template('dashboard/index.html',
                           total_employees=total_employees,
                           total_tasks=total_tasks,
                           total_schedules=total_schedules,
                           employees=employees,
                           tasks=tasks,
                           schedules=schedules,
                           today_schedules=today_schedules,
                           today=today,
                           week_offset=week_offset,
                           week_days=week_days)