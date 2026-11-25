from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.auth import login_required, role_required
from app.dao.lecturer_dao import LecturerDAO
from app.dao.user_dao import UserDAO
from app.dao.routing_dao import RoutingDAO

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/dashboard')
@login_required
@role_required('staff', 'admin')
def dashboard():
    current_user = session['user']
    user_uid = current_user.get('uid')

    fac_code = None
    fac_name = 'Khoa'
    try:
        user_detail = UserDAO.get_by_uid(user_uid)
        fac_obj = user_detail.get('in_faculty') if user_detail else None
        fac_code = fac_obj.get('code') if isinstance(fac_obj, dict) else (fac_obj[0].get('code') if fac_obj else None)
        fac_name = fac_obj.get('name') if isinstance(fac_obj, dict) else (fac_obj[0].get('name') if fac_obj else 'Khoa')

        # 1. Danh sách Giảng viên thuộc khoa mình
        faculty_lecturers = LecturerDAO.search_lecturers(faculty_code=fac_code)

        # 2. Danh sách Sinh viên thuộc khoa mình
        all_users = UserDAO.get_all_users()
        faculty_students = [u for u in all_users if u.get('role') == 'student' and (u.get('faculty_code') == fac_code or not fac_code)]

        # 3. Quản lý Chủ đề: Lấy toàn bộ chủ đề
        topics = RoutingDAO.search_topics()
    except Exception as e:
        flash(f'Lỗi tải dữ liệu khoa: {e}', 'danger')
        faculty_lecturers, faculty_students, topics = [], [], []

    return render_template(
        'staff/dashboard.html',
        fac_code=fac_code,
        fac_name=fac_name,
        lecturers=faculty_lecturers,
        students=faculty_students,
        topics=topics,
        all_lecturers=faculty_lecturers
    )

@staff_bp.route('/topics/add', methods=['POST'])
@login_required
@role_required('staff', 'admin')
def add_topic():
    topic_name = request.form.get('topic_name')
    description = request.form.get('description', '')
    lecturer_uids = request.form.getlist('lecturer_uids')

    if topic_name:
        try:
            RoutingDAO.create_topic(topic_name, description, lecturer_uids)
            flash(f'Đã tạo chủ đề "{topic_name}" và phân công {len(lecturer_uids)} giảng viên phụ trách thành công!', 'success')
        except Exception as e:
            flash(f'Lỗi tạo chủ đề: {e}', 'danger')
    return redirect(url_for('staff.dashboard'))

@staff_bp.route('/topics/update/<topic_uid>', methods=['POST'])
@login_required
@role_required('staff', 'admin')
def update_topic(topic_uid):
    topic_name = request.form.get('topic_name')
    description = request.form.get('description', '')
    lecturer_uids = request.form.getlist('lecturer_uids')

    if topic_name:
        try:
            RoutingDAO.update_topic(topic_uid, topic_name, description, lecturer_uids)
            flash(f'Đã cập nhật chủ đề "{topic_name}" thành công!', 'success')
        except Exception as e:
            flash(f'Lỗi cập nhật chủ đề: {e}', 'danger')
    return redirect(url_for('staff.dashboard'))

@staff_bp.route('/topics/delete/<topic_uid>', methods=['POST'])
@login_required
@role_required('staff', 'admin')
def delete_topic(topic_uid):
    try:
        RoutingDAO.delete_topic(topic_uid)
        flash('Đã xóa chủ đề xử lý.', 'info')
    except Exception as e:
        flash(f'Lỗi xóa chủ đề: {e}', 'danger')
    return redirect(url_for('staff.dashboard'))
