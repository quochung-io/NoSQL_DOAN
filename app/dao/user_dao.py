from app.db import dgraph_db
from app.auth import hash_password

class UserDAO:
    @staticmethod
    def get_by_username(username):
        safe_username = str(username).replace('"', '\\"')
        q = f"""
        query {{
          user(func: eq(username, "{safe_username}")) @filter(type(User)) {{
            uid
            username
            password_hash
            full_name
            email
            phone
            role
            must_change_password
            is_active
            in_faculty {{
              uid
              code
              name
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        users = res.get('user', [])
        return users[0] if users else None

    @staticmethod
    def get_by_uid(uid):
        q = f"""
        query {{
          user(func: uid({uid})) @filter(type(User)) {{
            uid
            username
            password_hash
            full_name
            email
            phone
            role
            must_change_password
            is_active
            in_faculty {{
              uid
              code
              name
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        users = res.get('user', [])
        return users[0] if users else None

    @staticmethod
    def change_password(uid, new_pw_hash):
        mutation = {
            'uid': uid,
            'password_hash': new_pw_hash,
            'must_change_password': False
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def update_phone(uid, phone):
        mutation = {
            'uid': uid,
            'phone': phone.strip()
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def get_all_users():
        q = """
        query {
          users(func: type(User), orderasc: role) {
            uid
            username
            full_name
            email
            phone
            role
            must_change_password
            is_active
            in_faculty {
              uid
              code
              name
            }
          }
        }
        """
        res = dgraph_db.query(q)
        users = res.get('users', [])
        
        # Chuẩn hóa an toàn tuyệt đối cho template Jinja2
        for u in users:
            fac = u.get('in_faculty')
            if isinstance(fac, list) and len(fac) > 0:
                u['faculty_code'] = fac[0].get('code', '-')
                u['faculty_name'] = fac[0].get('name', '-')
            elif isinstance(fac, dict):
                u['faculty_code'] = fac.get('code', '-')
                u['faculty_name'] = fac.get('name', '-')
            else:
                u['faculty_code'] = '-'
                u['faculty_name'] = '-'

        return users

    @staticmethod
    def toggle_active(uid, current_state):
        mutation = {
            'uid': uid,
            'is_active': not current_state
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def reset_password(uid, default_password):
        pw_hash = hash_password(default_password)
        mutation = {
            'uid': uid,
            'password_hash': pw_hash,
            'must_change_password': True
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def get_student_relations(username):
        """
        Truy vấn quan hệ đồ thị của sinh viên:
        - Faculty UID mà sinh viên trực thuộc
        - Tập hợp các Lecturer UIDs đang trực tiếp dạy sinh viên
        """
        safe_username = str(username).replace('"', '\\"')
        q = f"""
        query {{
          student(func: eq(username, "{safe_username}")) @filter(type(User)) {{
            uid
            in_faculty {{
              uid
              code
            }}
            enrolled_in {{
              code
              taught_by {{
                uid
                code
              }}
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        students = res.get('student', [])
        if not students:
            return {'faculty_uid': None, 'enrolled_lecturer_uids': set()}

        st = students[0]
        fac_uid = None
        fac = st.get('in_faculty')
        if isinstance(fac, list) and len(fac) > 0:
            fac_uid = fac[0].get('uid')
        elif isinstance(fac, dict):
            fac_uid = fac.get('uid')

        lecturer_uids = set()
        for sec in st.get('enrolled_in', []):
            tb = sec.get('taught_by')
            tb_list = [tb] if isinstance(tb, dict) else (tb or [])
            for gv in tb_list:
                if gv.get('uid'):
                    lecturer_uids.add(gv.get('uid'))

        return {
            'student_uid': st.get('uid'),
            'faculty_uid': fac_uid,
            'enrolled_lecturer_uids': lecturer_uids
        }

    @staticmethod
    def get_student_full_profile(username):
        """
        Lấy thông tin chi tiết hồ sơ cá nhân của sinh viên kèm các lớp học phần và giảng viên phụ trách
        """
        safe_username = str(username).replace('"', '\\"')
        q = f"""
        query {{
          student(func: eq(username, "{safe_username}")) @filter(type(User)) {{
            uid
            username
            full_name
            email
            phone
            role
            in_faculty {{
              uid
              code
              name
            }}
            enrolled_in {{
              uid
              code
              room
              semester
              of_subject {{
                code
                name
                credits
              }}
              taught_by {{
                uid
                code
                name
                title
                email
              }}
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        students = res.get('student', [])
        if not students:
            return None

        st = students[0]
        fac = st.get('in_faculty')
        if isinstance(fac, list) and len(fac) > 0:
            st['faculty_code'] = fac[0].get('code', '-')
            st['faculty_name'] = fac[0].get('name', '-')
        elif isinstance(fac, dict):
            st['faculty_code'] = fac.get('code', '-')
            st['faculty_name'] = fac.get('name', '-')
        else:
            st['faculty_code'] = '-'
            st['faculty_name'] = '-'

        return st
