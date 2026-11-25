from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from app.auth import login_required
from app.dao.chat_dao import ChatDAO
from app.dao.lecturer_dao import LecturerDAO
from app.dao.user_dao import UserDAO

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def messenger():
    current_user = session['user']
    user_uid = current_user.get('uid')

    fac_code = None
    try:
        user_detail = UserDAO.get_by_uid(user_uid)
        if user_detail:
            fac_obj = user_detail.get('in_faculty')
            fac_code = fac_obj.get('code') if isinstance(fac_obj, dict) else (fac_obj[0].get('code') if fac_obj else None)
        
        # CHỈ lấy các cuộc hội thoại ĐÃ TỪNG NHẮN TIN (mặc định rỗng nếu chưa nhắn)
        contacts = ChatDAO.get_active_conversations(user_uid)
        support_contacts = ChatDAO.get_support_contacts(fac_code)
    except Exception as e:
        flash(f'Lỗi kết nối CSDL tin nhắn: {e}', 'danger')
        contacts = []
        support_contacts = {'admin': None, 'staff': None}

    # Nếu có query param ?with=<uid>
    selected_uid = request.args.get('with')
    selected_partner = None

    if selected_uid:
        for c in contacts:
            if str(c.get('uid')) == str(selected_uid):
                selected_partner = c
                break

        if not selected_partner:
            try:
                u = UserDAO.get_by_uid(selected_uid)
                if u:
                    role_vn = {
                        'admin': 'Quản Trị Viên',
                        'staff': 'Cán Bộ Khoa (Trưởng Khoa)',
                        'lecturer': 'Giảng Viên',
                        'student': 'Sinh Viên'
                    }.get(u.get('role'), u.get('role'))
                    
                    selected_partner = {
                        'uid': u['uid'],
                        'name': u.get('full_name'),
                        'sub_info': f"{role_vn} • @{u.get('username')}",
                        'email': u.get('email', ''),
                        'role': u.get('role')
                    }
                else:
                    gv = LecturerDAO.get_by_uid(selected_uid)
                    if gv:
                        selected_partner = {
                            'uid': gv['uid'],
                            'name': gv.get('name'),
                            'sub_info': f"{gv.get('title', 'Giảng viên')} • {gv.get('code')}",
                            'email': gv.get('email', ''),
                            'role': 'lecturer'
                        }
            except Exception:
                pass

    if not selected_partner and contacts:
        selected_partner = contacts[0]

    return render_template(
        'chat/messenger.html',
        contacts=contacts,
        selected_partner=selected_partner,
        support_contacts=support_contacts
    )

@chat_bp.route('/api/messages/<partner_uid>')
@login_required
def get_messages(partner_uid):
    current_user = session['user']
    try:
        messages = ChatDAO.get_conversation(current_user['uid'], partner_uid)
    except Exception as e:
        messages = []
    return jsonify({'messages': messages})

@chat_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    current_user = session['user']
    data = request.get_json() or {}
    receiver_uid = data.get('receiver_uid')
    text = data.get('text', '').strip()

    if not receiver_uid or not text:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400

    try:
        msg_id = ChatDAO.send_message(current_user['uid'], receiver_uid, text)
        return jsonify({'success': True, 'msg_id': msg_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
