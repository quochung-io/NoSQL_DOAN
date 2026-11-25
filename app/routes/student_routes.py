from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from app.auth import login_required
from app.dao.lecturer_dao import LecturerDAO
from app.dao.user_dao import UserDAO
from app.dao.routing_dao import RoutingDAO
from app.dao.log_dao import LogDAO
from app.dao.graph_dao import GraphDAO
from app.services.visibility_service import VisibilityService
from app.services.routing_service import RoutingService

student_bp = Blueprint('student', __name__)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    current_user = session['user']
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        try:
            UserDAO.update_phone(current_user['uid'], phone)
            session['user']['phone'] = phone
            flash('Đã cập nhật số điện thoại liên hệ thành công!', 'success')
        except Exception as e:
            flash(f'Lỗi cập nhật: {e}', 'danger')
        return redirect(url_for('student.profile'))

    try:
        student_data = UserDAO.get_student_full_profile(current_user['username'])
    except Exception as e:
        flash(f'Lỗi tải hồ sơ sinh viên: {e}', 'danger')
        student_data = None

    if not student_data:
        student_data = {
            'username': current_user.get('username'),
            'full_name': current_user.get('full_name'),
            'email': current_user.get('email'),
            'phone': current_user.get('phone', ''),
            'faculty_name': 'Chưa cập nhật',
            'faculty_code': '-',
            'enrolled_in': []
        }

    return render_template('student/profile.html', student=student_data)

@student_bp.route('/search')
@login_required
def search():
    keyword = request.args.get('keyword', '').strip()
    faculty_code = request.args.get('faculty', '')
    major_code = request.args.get('major', '')
    subject_code = request.args.get('subject', '')

    try:
        lecturers = LecturerDAO.search_lecturers(
            keyword=keyword,
            faculty_code=faculty_code,
            major_code=major_code,
            subject_code=subject_code
        )
        faculties = LecturerDAO.get_all_faculties_and_majors()
        subjects = LecturerDAO.get_all_subjects()
    except Exception as e:
        flash(f'Lỗi kết nối CSDL: {e}', 'danger')
        lecturers, faculties, subjects = [], [], []

    return render_template(
        'student/search.html',
        lecturers=lecturers,
        faculties=faculties,
        subjects=subjects,
        selected_faculty=faculty_code,
        selected_major=major_code,
        selected_subject=subject_code,
        keyword=keyword
    )

@student_bp.route('/lecturer/<uid>')
@login_required
def lecturer_detail(uid):
    try:
        lecturer = LecturerDAO.get_by_uid(uid)
    except Exception as e:
        flash(f'Lỗi truy vấn CSDL: {e}', 'danger')
        return redirect(url_for('student.search'))

    if not lecturer:
        flash('Không tìm thấy thông tin giảng viên.', 'danger')
        return redirect(url_for('student.search'))

    current_user = session['user']
    user_role = current_user.get('role')

    # Ghi nhận nhật ký truy cập (AccessLog)
    LogDAO.record_access(current_user['uid'], uid)

    # Lấy thông tin quan hệ đồ thị của sinh viên để phân quyền xem
    try:
        student_relations = UserDAO.get_student_relations(current_user['username'])
    except Exception:
        student_relations = {'faculty_uid': None, 'enrolled_lecturer_uids': set()}

    # Lấy UID khoa của giảng viên
    major = lecturer.get('belongs_to', {})
    fac_raw = major.get('~has_major')
    fac = fac_raw[0] if isinstance(fac_raw, list) and fac_raw else (fac_raw if isinstance(fac_raw, dict) else {})
    lecturer_fac_uid = fac.get('uid')

    # Lọc danh sách kênh liên lạc theo visibility & giờ làm việc
    raw_channels = lecturer.get('has_channel', [])
    filtered_channels = VisibilityService.filter_channels(
        channels=raw_channels,
        student_relations=student_relations,
        lecturer_faculty_uid=lecturer_fac_uid,
        lecturer_uid=uid,
        viewer_role=user_role
    )

    return render_template(
        'student/lecturer_detail.html',
        lecturer=lecturer,
        channels=filtered_channels,
        faculty=fac
    )

@student_bp.route('/lecturer/<uid>/fallback')
@login_required
def lecturer_fallback(uid):
    try:
        lecturer = LecturerDAO.get_by_uid(uid)
        if not lecturer:
            flash('Không tìm thấy giảng viên.', 'danger')
            return redirect(url_for('student.search'))
        fallback_plan = RoutingService.get_full_fallback_plan(uid)
    except Exception as e:
        flash(f'Lỗi tải phương án thay thế: {e}', 'danger')
        return redirect(url_for('student.search'))

    return render_template(
        'student/fallback_plan.html',
        lecturer=lecturer,
        colleagues=fallback_plan.get('colleagues', []),
        escalation_targets=fallback_plan.get('escalation_targets', [])
    )

@student_bp.route('/topics')
@login_required
def topic_search():
    keyword = request.args.get('keyword', '').strip()
    try:
        topics = RoutingDAO.search_topics(keyword=keyword)
    except Exception as e:
        flash(f'Lỗi tìm kiếm chủ đề: {e}', 'danger')
        topics = []
    return render_template('student/topic_search.html', topics=topics, keyword=keyword)

@student_bp.route('/graph')
@login_required
def graph_explorer():
    return render_template('student/graph_explorer.html')

@student_bp.route('/api/graph-data')
@login_required
def api_graph_data():
    try:
        data = GraphDAO.get_network_graph()
    except Exception as e:
        data = {'nodes': [], 'edges': []}
    return jsonify(data)
