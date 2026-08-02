from app import db
from app.models.employee import Employee
from app.models.task import Task
from app.models.schedule import Schedule
from datetime import date, timedelta
import random

def auto_assign_tasks(start_date=None):
    """
    Phân công tự động từ Thứ Hai đến Thứ Bảy dựa vào start_date (ngày Thứ Hai).
    Nếu không truyền start_date, mặc định lấy ngày hôm nay làm mốc.
    Chủ Nhật (ngày thứ 7 trong vòng lặp) sẽ được bỏ trống làm dự phòng.
    """
    try:
        employees = Employee.query.all()
        tasks = Task.query.all()

        if not employees:
            return False, "Chưa có nhân viên nào trong hệ thống để phân công!"
        if not tasks:
            return False, "Chưa có công việc nào trong hệ thống để phân công!"

        if not start_date:
            start_date = date.today()

        shifts = ['Ca sáng', 'Ca chiều']
        total_assigned = 0

        # Lặp qua 6 ngày từ Thứ 2 (0) đến Thứ 7 (5). Chủ Nhật (index 6) bỏ qua để dự phòng.
        for i in range(6):
            current_date = start_date + timedelta(days=i)
            
            # Xóa lịch CŨ CỦA TỪNG NGÀY TRONG TUẦN để tránh trùng lặp khi bấm chạy lại
            Schedule.query.filter_by(work_date=current_date).delete()
            db.session.commit()

            # Phân công ca cho từng nhân viên trong ngày current_date
            for emp in employees:
                for shift in shifts:
                    random_task = random.choice(tasks)
                    
                    new_schedule = Schedule(
                        employee_id=emp.id,
                        task_id=random_task.id,
                        work_date=current_date,
                        shift=shift,
                        status='Chưa làm'
                    )
                    db.session.add(new_schedule)
                    total_assigned += 1

        db.session.commit()
        return True, f"Đã phân công tự động thành công cho cả tuần (Thứ 2 - Thứ 7) với tổng số {total_assigned} ca làm việc!"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi hệ thống khi phân lịch tự động theo tuần: {str(e)}"


def auto_assign_single_day(target_date=None):
    """
    Phân công tự động CHỈ CHO ĐÚNG MỘT NGÀY ĐƯỢC CHỌN (target_date).
    """
    try:
        employees = Employee.query.all()
        tasks = Task.query.all()

        if not employees:
            return False, "Chưa có nhân viên nào trong hệ thống để phân công!"
        if not tasks:
            return False, "Chưa có công việc nào trong hệ thống để phân công!"

        if not target_date:
            target_date = date.today()

        shifts = ['Ca sáng', 'Ca chiều']
        total_assigned = 0

        # Xóa lịch cũ của đúng ngày được chọn để tránh trùng lặp
        Schedule.query.filter_by(work_date=target_date).delete()
        db.session.commit()

        # Phân công ca cho từng nhân viên chỉ trong ngày target_date
        for emp in employees:
            for shift in shifts:
                random_task = random.choice(tasks)
                
                new_schedule = Schedule(
                    employee_id=emp.id,
                    task_id=random_task.id,
                    work_date=target_date,
                    shift=shift,
                    status='Chưa làm'
                )
                db.session.add(new_schedule)
                total_assigned += 1

        db.session.commit()
        return True, f"Đã phân công tự động thành công cho ngày {target_date.strftime('%d/%m/%Y')} với tổng số {total_assigned} ca làm việc!"

    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi hệ thống khi phân lịch tự động theo ngày: {str(e)}"