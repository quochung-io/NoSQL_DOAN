from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.auth import login_required, role_required
from app.dao.lecturer_dao import LecturerDAO

lecturer_bp = Blueprint('lecturer', __name__)

@lecturer_bp.route('/dashboard')
@login_required
@role_required('lecturer')
def dashboard():
    user = session['user']
    try:
        lecturer = LecturerDAO.get_by_email(user.get('email'))
    except Exception as e:
        flash(f'Lỗi tải hồ sơ giảng viên: {e}', 'danger')
        lecturer = None

    if not lecturer:
        flash('Chưa tìm thấy hồ sơ giảng viên liên kết.', 'warning')
        return render_template('lecturer/dashboard.html', lecturer=None, channels=[], all_candidates=[])

    channels = lecturer.get('has_channel', [])
    
    try:
        all_lecturers = LecturerDAO.search_lecturers()
        faculties = LecturerDAO.get_all_faculties_and_majors()
    except Exception:
        all_lecturers = []
        faculties = []

    # Lọc bỏ chính mình
    other_lecturers = [g for g in all_lecturers if str(g.get('uid')) != str(lecturer['uid'])]
    
    offices = []
    for f in faculties:
        for off in f.get('has_office', []):
            offices.append({
                'uid': off['uid'],
                'name': f"{off['name']} ({f['name']})",
                'title': 'Văn phòng đơn vị'
            })

    all_candidates = other_lecturers + offices

    return render_template(
        'lecturer/dashboard.html',
        lecturer=lecturer,
        channels=channels,
        all_candidates=all_candidates
    )

@lecturer_bp.route('/escalation', methods=['POST'])
@login_required
@role_required('lecturer')
def update_escalation():
    user = session['user']
    try:
        lecturer = LecturerDAO.get_by_email(user.get('email'))
        target_uid = request.form.get('target_uid')

        if lecturer and target_uid:
            LecturerDAO.update_escalation(lecturer['uid'], target_uid)
            flash('Đã cập nhật người tiếp nhận thay thế khi vắng mặt thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi thiết lập người thay thế: {e}', 'danger')
    return redirect(url_for('lecturer.dashboard'))

@lecturer_bp.route('/channels/add', methods=['POST'])
@login_required
@role_required('lecturer')
def add_channel():
    user = session['user']
    try:
        lecturer = LecturerDAO.get_by_email(user.get('email'))
        if not lecturer:
            flash('Không tìm thấy giảng viên.', 'danger')
            return redirect(url_for('lecturer.dashboard'))

        ch_type = request.form.get('channel_type')
        ch_val = request.form.get('channel_value')
        vis = request.form.get('visibility', 'all_students')
        days = request.form.getlist('active_days')
        s_time = request.form.get('start_time', '08:00')
        e_time = request.form.get('end_time', '17:00')

        new_channel = {
            'channel_type': ch_type,
            'channel_value': ch_val,
            'visibility': vis,
            'active_days': days,
            'start_time': s_time,
            'end_time': e_time
        }

        LecturerDAO.add_channel(lecturer['uid'], new_channel)
        flash('Thêm kênh liên lạc mới thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi thêm kênh: {e}', 'danger')
    return redirect(url_for('lecturer.dashboard'))

@lecturer_bp.route('/channels/update/<channel_uid>', methods=['POST'])
@login_required
@role_required('lecturer')
def update_channel(channel_uid):
    ch_val = request.form.get('channel_value')
    vis = request.form.get('visibility')
    days = request.form.getlist('active_days')
    s_time = request.form.get('start_time')
    e_time = request.form.get('end_time')

    updates = {
        'channel_value': ch_val,
        'visibility': vis,
        'active_days': days,
        'start_time': s_time,
        'end_time': e_time
    }

    try:
        LecturerDAO.update_channel(channel_uid, updates)
        flash('Cập nhật kênh liên lạc thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi cập nhật kênh: {e}', 'danger')
    return redirect(url_for('lecturer.dashboard'))

@lecturer_bp.route('/channels/delete/<channel_uid>', methods=['POST'])
@login_required
@role_required('lecturer')
def delete_channel(channel_uid):
    try:
        LecturerDAO.delete_channel(channel_uid)
        flash('Đã xóa kênh liên lạc.', 'info')
    except Exception as e:
        flash(f'Lỗi xóa kênh: {e}', 'danger')
    return redirect(url_for('lecturer.dashboard'))
