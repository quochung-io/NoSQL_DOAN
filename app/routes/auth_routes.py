from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.dao.user_dao import UserDAO
from app.auth import check_password, hash_password, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        try:
            user = UserDAO.get_by_username(username)
        except Exception as e:
            flash(f'Không thể kết nối tới CSDL Dgraph (Port 9080). Hãy đảm bảo Docker đang chạy container dgraph-alpha! Chi tiết lỗi: {e}', 'danger')
            return render_template('auth/login.html')

        if not user or not check_password(password, user.get('password_hash', '')):
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.', 'danger')
            return render_template('auth/login.html')

        if not user.get('is_active', True):
            flash('Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin.', 'danger')
            return render_template('auth/login.html')

        # Lưu session
        session['user'] = {
            'uid': user.get('uid'),
            'username': user.get('username'),
            'full_name': user.get('full_name'),
            'email': user.get('email'),
            'role': user.get('role'),
            'must_change_password': user.get('must_change_password', False)
        }

        flash(f'Xin chào, {user.get("full_name")}!', 'success')

        if user.get('must_change_password'):
            flash('Bạn cần đổi mật khẩu trong lần đăng nhập đầu tiên.', 'info')
            return redirect(url_for('auth.change_password'))

        return redirect(url_for('auth.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_session = session['user']
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        try:
            user = UserDAO.get_by_uid(user_session['uid'])
        except Exception as e:
            flash(f'Lỗi truy vấn CSDL: {e}', 'danger')
            return render_template('auth/change_password.html')

        if not check_password(old_password, user.get('password_hash', '')):
            flash('Mật khẩu hiện tại không đúng.', 'danger')
            return render_template('auth/change_password.html')

        if len(new_password) < 6:
            flash('Mật khẩu mới phải có tối thiểu 6 ký tự.', 'danger')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('Xác nhận mật khẩu mới không khớp.', 'danger')
            return render_template('auth/change_password.html')

        new_hash = hash_password(new_password)
        UserDAO.change_password(user['uid'], new_hash)
        session['user']['must_change_password'] = False
        flash('Đổi mật khẩu thành công!', 'success')
        return redirect(url_for('auth.dashboard'))

    return render_template('auth/change_password.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    role = session['user'].get('role')
    if role == 'student':
        return redirect(url_for('student.search'))
    elif role == 'lecturer':
        return redirect(url_for('lecturer.dashboard'))
    elif role == 'staff':
        return redirect(url_for('staff.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))
