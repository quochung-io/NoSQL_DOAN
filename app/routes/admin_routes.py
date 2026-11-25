import io
import csv
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.auth import login_required, role_required, hash_password
from app.dao.user_dao import UserDAO
from app.dao.log_dao import LogDAO
from app.dao.lecturer_dao import LecturerDAO
from app.dao.routing_dao import RoutingDAO
from app.db import dgraph_db
from scripts.export_backup import export_json_backup
from scripts.restore_data import restore

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    try:
        users = UserDAO.get_all_users()
        recent_logs = LogDAO.get_recent_logs(limit=10)
        top_lecturers = LogDAO.get_view_statistics()[:5]
        topics = RoutingDAO.search_topics()
    except Exception as e:
        flash(f'Lỗi kết nối CSDL: {e}', 'danger')
        users, recent_logs, top_lecturers, topics = [], [], [], []

    return render_template(
        'admin/dashboard.html',
        total_users=len(users),
        recent_logs=recent_logs,
        top_lecturers=top_lecturers,
        total_topics=len(topics)
    )

@admin_bp.route('/users')
@login_required
@role_required('admin')
def user_list():
    try:
        role_filter = request.args.get('role', '')
        all_users = UserDAO.get_all_users()
        
        if role_filter:
            users = [u for u in all_users if u.get('role') == role_filter]
        else:
            users = all_users
    except Exception as e:
        flash(f'Lỗi kết nối CSDL khi tải danh sách người dùng: {e}', 'danger')
        users = []
        role_filter = ''
    return render_template('admin/users.html', users=users, selected_role=role_filter)

@admin_bp.route('/topics')
@login_required
@role_required('admin')
def manage_topics():
    try:
        topics = RoutingDAO.search_topics()
        lecturers = LecturerDAO.search_lecturers()
    except Exception as e:
        flash(f'Lỗi tải chủ đề: {e}', 'danger')
        topics, lecturers = [], []
    return render_template('admin/topics.html', topics=topics, lecturers=lecturers)

@admin_bp.route('/topics/add', methods=['POST'])
@login_required
@role_required('admin')
def add_topic():
    topic_name = request.form.get('topic_name')
    description = request.form.get('description', '')
    lecturer_uids = request.form.getlist('lecturer_uids')

    if topic_name:
        RoutingDAO.create_topic(topic_name, description, lecturer_uids)
        flash(f'Đã tạo chủ đề "{topic_name}" và phân công {len(lecturer_uids)} giảng viên thành công!', 'success')
    return redirect(url_for('admin.manage_topics'))

@admin_bp.route('/topics/update/<topic_uid>', methods=['POST'])
@login_required
@role_required('admin')
def update_topic(topic_uid):
    topic_name = request.form.get('topic_name')
    description = request.form.get('description', '')
    lecturer_uids = request.form.getlist('lecturer_uids')

    if topic_name:
        RoutingDAO.update_topic(topic_uid, topic_name, description, lecturer_uids)
        flash(f'Đã cập nhật chủ đề "{topic_name}" thành công!', 'success')
    return redirect(url_for('admin.manage_topics'))

@admin_bp.route('/topics/delete/<topic_uid>', methods=['POST'])
@login_required
@role_required('admin')
def delete_topic(topic_uid):
    RoutingDAO.delete_topic(topic_uid)
    flash('Đã xóa chủ đề.', 'info')
    return redirect(url_for('admin.manage_topics'))

@admin_bp.route('/users/toggle/<uid>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(uid):
    try:
        user = UserDAO.get_by_uid(uid)
        if user:
            UserDAO.toggle_active(uid, user.get('is_active', True))
            status_text = 'đã khóa' if user.get('is_active', True) else 'đã mở khóa'
            flash(f'Tài khoản {user.get("username")} {status_text} thành công.', 'success')
        else:
            flash('Không tìm thấy tài khoản người dùng.', 'warning')
    except Exception as e:
        flash(f'Lỗi thao tác: {e}', 'danger')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/reset-password/<uid>', methods=['POST'])
@login_required
@role_required('admin')
def reset_password(uid):
    try:
        user = UserDAO.get_by_uid(uid)
        if user:
            UserDAO.reset_password(uid, 'Sv@123')
            flash(f'Đã đặt lại mật khẩu cho {user.get("username")} thành "Sv@123" (bắt buộc đổi khi đăng nhập).', 'success')
        else:
            flash('Không tìm thấy tài khoản người dùng.', 'warning')
    except Exception as e:
        flash(f'Lỗi đặt lại mật khẩu: {e}', 'danger')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/import-students', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def import_students():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            flash('Vui lòng chọn một file CSV hợp lệ.', 'danger')
            return render_template('admin/import_students.html')

        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
            reader = csv.DictReader(stream)

            faculties = {f['code']: f['uid'] for f in LecturerDAO.get_all_faculties_and_majors()}
            mutations = []

            count = 0
            for row in reader:
                s_id = row['student_id']
                f_code = row.get('faculty_code')
                fac_uid = faculties.get(f_code)

                user_node = {
                    'uid': f'_:new_sv_{s_id}',
                    'dgraph.type': 'User',
                    'username': f'sv_{s_id}',
                    'password_hash': hash_password('Sv@123'),
                    'full_name': row['full_name'],
                    'email': row['email'],
                    'role': 'student',
                    'must_change_password': True,
                    'is_active': True
                }
                if fac_uid:
                    user_node['in_faculty'] = {'uid': fac_uid}

                mutations.append(user_node)
                count += 1

            if mutations:
                dgraph_db.mutate(set_obj=mutations)
                flash(f'Đã import thành công {count} tài khoản sinh viên từ CSV!', 'success')
            else:
                flash('File CSV không có dữ liệu.', 'warning')

            return redirect(url_for('admin.user_list'))
        except Exception as e:
            flash(f'Lỗi khi xử lý file CSV: {e}', 'danger')

    return render_template('admin/import_students.html')

@admin_bp.route('/backup', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def backup_restore():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'backup':
            try:
                filepath = export_json_backup()
                flash(f'Đã tạo bản sao lưu thành công tại: {filepath}', 'success')
            except Exception as e:
                flash(f'Lỗi sao lưu: {e}', 'danger')
        elif action == 'restore':
            try:
                restore()
                flash('Đã phục hồi CSDL đồ thị nguyên trạng thành công!', 'success')
            except Exception as e:
                flash(f'Lỗi phục hồi: {e}', 'danger')
        elif action == 'simulate_disaster':
            try:
                client = dgraph_db.get_client()
                client.alter(dgraph_db.pydgraph.Operation(drop_all=True))
                flash('CẢNH BÁO: Đã giả lập sự cố xóa sạch toàn bộ CSDL (Drop All)! Hãy bấm nút Phục hồi (Restore) để khôi phục.', 'danger')
            except Exception as e:
                flash(f'Lỗi giả lập: {e}', 'danger')

    return render_template('admin/backup.html')

@admin_bp.route('/logs')
@login_required
@role_required('admin')
def logs():
    try:
        recent_logs = LogDAO.get_recent_logs(limit=100)
        stats = LogDAO.get_view_statistics()
    except Exception as e:
        flash(f'Lỗi truy vấn nhật ký: {e}', 'danger')
        recent_logs, stats = [], []
    return render_template('admin/logs.html', logs=recent_logs, stats=stats)
