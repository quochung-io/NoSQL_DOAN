from datetime import datetime
from app.db import dgraph_db
from app.dao.user_dao import UserDAO
from app.dao.lecturer_dao import LecturerDAO

class ChatDAO:
    @staticmethod
    def send_message(sender_uid, receiver_uid, content):
        if not content or not content.strip():
            return None

        now_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        mutation = {
            'uid': '_:new_msg',
            'dgraph.type': 'Message',
            'message_text': content.strip(),
            'sent_at': now_str,
            'sender': {'uid': sender_uid},
            'receiver': {'uid': receiver_uid}
        }
        res = dgraph_db.mutate(set_obj=mutation)
        return res.uids.get('new_msg')

    @staticmethod
    def get_conversation(user1_uid, user2_uid, limit=50):
        """
        Lấy lịch sử tin nhắn giữa 2 người dùng (cả chiều gửi và nhận)
        """
        q = f"""
        query {{
          sent(func: type(Message), orderasc: sent_at) @filter(uid_in(sender, {user1_uid}) AND uid_in(receiver, {user2_uid})) {{
            uid
            message_text
            sent_at
            sender {{
              uid
              username
              full_name
            }}
            receiver {{
              uid
              username
              full_name
            }}
          }}

          received(func: type(Message), orderasc: sent_at) @filter(uid_in(sender, {user2_uid}) AND uid_in(receiver, {user1_uid})) {{
            uid
            message_text
            sent_at
            sender {{
              uid
              username
              full_name
            }}
            receiver {{
              uid
              username
              full_name
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        all_msgs = res.get('sent', []) + res.get('received', [])
        all_msgs.sort(key=lambda m: m.get('sent_at', ''))

        normalized = []
        for m in all_msgs:
            sender_obj = m.get('sender')
            s_uid = sender_obj.get('uid') if isinstance(sender_obj, dict) else (sender_obj[0].get('uid') if sender_obj else None)
            s_name = sender_obj.get('full_name') if isinstance(sender_obj, dict) else (sender_obj[0].get('full_name') if sender_obj else '')

            normalized.append({
                'uid': m.get('uid'),
                'text': m.get('message_text'),
                'sent_at': m.get('sent_at'),
                'sender_uid': s_uid,
                'sender_name': s_name,
                'is_mine': (str(s_uid) == str(user1_uid))
            })
        return normalized[-limit:]

    @staticmethod
    def get_active_conversations(current_user_uid):
        """
        CHỈ lấy danh sách những người ĐÃ TỪNG NHẮN TIN với current_user_uid.
        Ban đầu mặc định là RỖNG (không có gì) nếu chưa nhắn tin cho ai.
        """
        q = f"""
        query {{
          sent(func: type(Message)) @filter(uid_in(sender, {current_user_uid})) {{
            receiver {{
              uid
            }}
            sent_at
            message_text
          }}

          received(func: type(Message)) @filter(uid_in(receiver, {current_user_uid})) {{
            sender {{
              uid
            }}
            sent_at
            message_text
          }}
        }}
        """
        res = dgraph_db.query(q)
        partner_uids = set()
        last_messages = {}

        # Duyệt tin đã gửi
        for m in res.get('sent', []):
            rec = m.get('receiver')
            r_uid = rec.get('uid') if isinstance(rec, dict) else (rec[0].get('uid') if rec else None)
            if r_uid and str(r_uid) != str(current_user_uid):
                partner_uids.add(r_uid)
                if r_uid not in last_messages or m.get('sent_at', '') > last_messages[r_uid]['sent_at']:
                    last_messages[r_uid] = {
                        'text': m.get('message_text', ''),
                        'sent_at': m.get('sent_at', '')
                    }

        # Duyệt tin nhận được
        for m in res.get('received', []):
            snd = m.get('sender')
            s_uid = snd.get('uid') if isinstance(snd, dict) else (snd[0].get('uid') if snd else None)
            if s_uid and str(s_uid) != str(current_user_uid):
                partner_uids.add(s_uid)
                if s_uid not in last_messages or m.get('sent_at', '') > last_messages[s_uid]['sent_at']:
                    last_messages[s_uid] = {
                        'text': m.get('message_text', ''),
                        'sent_at': m.get('sent_at', '')
                    }

        # Lấy thông tin chi tiết của các đối tác trò chuyện
        contacts = []
        for p_uid in partner_uids:
            # Kiểm tra xem có phải là User không
            u = UserDAO.get_by_uid(p_uid)
            if u:
                role_vn = {
                    'admin': 'Quản Trị Viên',
                    'staff': 'Cán Bộ Khoa (Trưởng Khoa)',
                    'lecturer': 'Giảng Viên',
                    'student': 'Sinh Viên'
                }.get(u.get('role'), u.get('role', 'Người dùng'))

                contacts.append({
                    'uid': u['uid'],
                    'name': u.get('full_name'),
                    'sub_info': f"{role_vn} • @{u.get('username')}",
                    'email': u.get('email', ''),
                    'role': u.get('role'),
                    'last_message': last_messages.get(p_uid, {}).get('text', ''),
                    'last_time': last_messages.get(p_uid, {}).get('sent_at', '')
                })
            else:
                # Nếu đối tác là node Lecturer
                gv = LecturerDAO.get_by_uid(p_uid)
                if gv:
                    contacts.append({
                        'uid': gv['uid'],
                        'name': gv.get('name'),
                        'sub_info': f"{gv.get('title', 'Giảng viên')} • {gv.get('code')}",
                        'email': gv.get('email', ''),
                        'role': 'lecturer',
                        'last_message': last_messages.get(p_uid, {}).get('text', ''),
                        'last_time': last_messages.get(p_uid, {}).get('sent_at', '')
                    })

        # Sắp xếp theo tin nhắn mới nhất
        contacts.sort(key=lambda c: c.get('last_time', ''), reverse=True)
        return contacts

    @staticmethod
    def get_support_contacts(current_user_faculty_code=None):
        """
        Lấy thông tin Admin và Cán bộ khoa (Trưởng khoa) để hiển thị nút liên hệ nhanh
        """
        q = """
        query {
          admins(func: eq(role, "admin")) @filter(type(User)) {
            uid
            username
            full_name
            email
            role
          }
          staffs(func: eq(role, "staff")) @filter(type(User)) {
            uid
            username
            full_name
            email
            role
            in_faculty {
              code
              name
            }
          }
        }
        """
        res = dgraph_db.query(q)
        admin_user = res.get('admins', [None])[0]
        staff_users = res.get('staffs', [])

        # Nếu có mã khoa thì ưu tiên chọn cán bộ khoa đó
        matched_staff = None
        if current_user_faculty_code:
            for s in staff_users:
                fac = s.get('in_faculty')
                f_code = fac.get('code') if isinstance(fac, dict) else (fac[0].get('code') if fac else '')
                if f_code == current_user_faculty_code:
                    matched_staff = s
                    break

        if not matched_staff and staff_users:
            matched_staff = staff_users[0]

        return {
            'admin': admin_user,
            'staff': matched_staff
        }
