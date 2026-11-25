import os
# Khắc phục lỗi tương thích giữa pydgraph và protobuf phiên bản mới
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import csv
import json
import bcrypt
import pydgraph

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_sample')

def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_client():
    host = os.environ.get('DGRAPH_HOST', 'localhost')
    port = os.environ.get('DGRAPH_GRPC_PORT', '9080')
    client_stub = pydgraph.DgraphClientStub(f'{host}:{port}')
    return pydgraph.DgraphClient(client_stub), client_stub

def seed():
    client, client_stub = get_client()
    txn = client.txn()
    try:
        print("1. Nạp Faculties...")
        faculties_map = {}
        with open(os.path.join(DATA_DIR, 'faculties.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid_ref = f'_:faculty_{row["code"]}'
                faculties_map[row['code']] = uid_ref

        print("2. Nạp Majors...")
        majors_map = {}
        majors_by_faculty = {}
        with open(os.path.join(DATA_DIR, 'majors.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid_ref = f'_:major_{row["code"]}'
                majors_map[row['code']] = uid_ref
                f_code = row['faculty_code']
                majors_by_faculty.setdefault(f_code, []).append(uid_ref)

        print("3. Nạp Offices...")
        offices_map = {}
        offices_by_faculty = {}
        with open(os.path.join(DATA_DIR, 'offices.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                uid_ref = f'_:office_{idx}'
                offices_map[row['name']] = uid_ref
                f_code = row['faculty_code']
                offices_by_faculty.setdefault(f_code, []).append(uid_ref)

        print("4. Nạp Subjects...")
        subjects_map = {}
        subjects_by_major = {}
        with open(os.path.join(DATA_DIR, 'subjects.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid_ref = f'_:subject_{row["code"]}'
                subjects_map[row['code']] = uid_ref
                m_code = row['major_code']
                subjects_by_major.setdefault(m_code, []).append(uid_ref)

        print("5. Nạp Lecturers...")
        lecturers_map = {}
        lecturers_by_major = {}
        dept_heads = {}
        with open(os.path.join(DATA_DIR, 'lecturers.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid_ref = f'_:lecturer_{row["code"]}'
                lecturers_map[row['code']] = {
                    'uid': uid_ref,
                    'code': row['code'],
                    'name': row['name'],
                    'email': row['email'],
                    'major_code': row['major_code'],
                    'title': row['title'],
                    'is_head': row['is_head'].lower() == 'true'
                }
                m_code = row['major_code']
                lecturers_by_major.setdefault(m_code, []).append(uid_ref)
                if row['is_head'].lower() == 'true':
                    dept_heads[m_code] = uid_ref

        print("6. Xây dựng Nodes & Mutations...")
        mutations = []

        # Faculty mutations
        with open(os.path.join(DATA_DIR, 'faculties.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                f_uid = faculties_map[row['code']]
                f_majors = [{'uid': m} for m in majors_by_faculty.get(row['code'], [])]
                f_offices = [{'uid': o} for o in offices_by_faculty.get(row['code'], [])]
                mutations.append({
                    'uid': f_uid,
                    'dgraph.type': 'Faculty',
                    'code': row['code'],
                    'name': row['name'],
                    'has_major': f_majors,
                    'has_office': f_offices
                })

        # Major mutations
        with open(os.path.join(DATA_DIR, 'majors.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                m_uid = majors_map[row['code']]
                m_subs = [{'uid': s} for s in subjects_by_major.get(row['code'], [])]
                mutations.append({
                    'uid': m_uid,
                    'dgraph.type': 'Major',
                    'code': row['code'],
                    'name': row['name'],
                    'offers': m_subs
                })

        # Office mutations (có channels riêng)
        with open(os.path.join(DATA_DIR, 'offices.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                o_uid = offices_map[row['name']]
                c_email = f'_:chan_off_email_{idx}'
                c_phone = f'_:chan_off_phone_{idx}'
                
                mutations.append({
                    'uid': c_email,
                    'dgraph.type': 'Channel',
                    'channel_type': 'email',
                    'channel_value': row['email'],
                    'visibility': 'all_students',
                    'active_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    'start_time': '08:00',
                    'end_time': '17:00'
                })
                mutations.append({
                    'uid': c_phone,
                    'dgraph.type': 'Channel',
                    'channel_type': 'phone',
                    'channel_value': row['phone'],
                    'visibility': 'all_students',
                    'active_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    'start_time': '08:30',
                    'end_time': '16:30'
                })

                mutations.append({
                    'uid': o_uid,
                    'dgraph.type': 'Office',
                    'name': row['name'],
                    'phone': row['phone'],
                    'email': row['email'],
                    'location': row['location'],
                    'has_channel': [{'uid': c_email}, {'uid': c_phone}]
                })

        # Subject mutations
        with open(os.path.join(DATA_DIR, 'subjects.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s_uid = subjects_map[row['code']]
                mutations.append({
                    'uid': s_uid,
                    'dgraph.type': 'Subject',
                    'code': row['code'],
                    'name': row['name'],
                    'credits': int(row['credits'])
                })

        # Lecturer mutations (with channels & escalation chain)
        faculty_office_cntt = offices_map.get('Văn phòng Khoa CNTT')
        faculty_office_kt = offices_map.get('Văn phòng Khoa Kinh tế')

        for gv_code, gv in lecturers_map.items():
            l_uid = gv['uid']
            m_code = gv['major_code']
            major_uid = majors_map[m_code]
            
            # Chuỗi thay thế leo thang (Escalates to):
            if gv['is_head']:
                if m_code in ['KTPM', 'KHMT', 'HTTT']:
                    escalate_target = faculty_office_cntt
                else:
                    escalate_target = faculty_office_kt
            else:
                escalate_target = dept_heads.get(m_code, faculty_office_cntt)

            # Tạo channels mẫu cho giảng viên
            ch_email = f'_:chan_gv_email_{gv_code}'
            mutations.append({
                'uid': ch_email,
                'dgraph.type': 'Channel',
                'channel_type': 'email',
                'channel_value': gv['email'],
                'visibility': 'all_students',
                'active_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                'start_time': '08:00',
                'end_time': '20:00'
            })

            ch_zalo = f'_:chan_gv_zalo_{gv_code}'
            mutations.append({
                'uid': ch_zalo,
                'dgraph.type': 'Channel',
                'channel_type': 'zalo',
                'channel_value': f'091{int(gv_code[2:]):07d}',
                'visibility': 'same_faculty',
                'active_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                'start_time': '09:00',
                'end_time': '18:00'
            })

            ch_phone = f'_:chan_gv_phone_{gv_code}'
            mutations.append({
                'uid': ch_phone,
                'dgraph.type': 'Channel',
                'channel_type': 'phone',
                'channel_value': f'098{int(gv_code[2:]):07d}',
                'visibility': 'enrolled_only',
                'active_days': ['Tue', 'Thu'],
                'start_time': '08:30',
                'end_time': '11:30'
            })

            ch_office = f'_:chan_gv_office_{gv_code}'
            mutations.append({
                'uid': ch_office,
                'dgraph.type': 'Channel',
                'channel_type': 'office_hours',
                'channel_value': 'Văn phòng Bộ môn - Bàn số ' + str(int(gv_code[2:]) % 10 + 1),
                'visibility': 'all_students',
                'active_days': ['Mon', 'Wed'],
                'start_time': '14:00',
                'end_time': '16:30'
            })

            lecturer_node = {
                'uid': l_uid,
                'dgraph.type': 'Lecturer',
                'code': gv['code'],
                'name': gv['name'],
                'email': gv['email'],
                'title': gv['title'],
                'is_head': gv['is_head'],
                'belongs_to': {'uid': major_uid},
                'has_channel': [
                    {'uid': ch_email},
                    {'uid': ch_zalo},
                    {'uid': ch_phone},
                    {'uid': ch_office}
                ]
            }
            if escalate_target:
                lecturer_node['escalates_to'] = {'uid': escalate_target}

            mutations.append(lecturer_node)

        # Section mutations
        sections_map = {}
        with open(os.path.join(DATA_DIR, 'sections.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec_uid = f'_:sec_{row["code"]}'
                sections_map[row['code']] = sec_uid
                sub_uid = subjects_map[row['subject_code']]
                gv_uid = lecturers_map[row['lecturer_code']]['uid']
                mutations.append({
                    'uid': sec_uid,
                    'dgraph.type': 'Section',
                    'code': row['code'],
                    'semester': row['semester'],
                    'room': row['room'],
                    'of_subject': {'uid': sub_uid},
                    'taught_by': {'uid': gv_uid}
                })

        # Topic mutations
        with open(os.path.join(DATA_DIR, 'topics.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                t_uid = f'_:topic_{idx}'
                h_type = row['handler_type']
                h_code = row['handler_code']
                
                target_uid = None
                if h_type == 'OFFICE':
                    target_uid = offices_map.get(h_code)
                elif h_type == 'LECTURER':
                    target_uid = lecturers_map.get(h_code, {}).get('uid')

                topic_node = {
                    'uid': t_uid,
                    'dgraph.type': 'Topic',
                    'topic_name': row['topic_name'],
                    'description': row['description']
                }
                if target_uid:
                    topic_node['handles'] = [{'uid': target_uid}]
                
                mutations.append(topic_node)

        # User accounts
        print("7. Tạo tài khoản User hệ thống...")
        mutations.append({
            'uid': '_:user_admin',
            'dgraph.type': 'User',
            'username': 'admin',
            'password_hash': hash_pw('Admin@123'),
            'full_name': 'Quản Trị Viên Hệ Thống',
            'email': 'admin@truong.edu.vn',
            'role': 'admin',
            'must_change_password': False,
            'is_active': True
        })

        mutations.append({
            'uid': '_:user_canbo_cntt',
            'dgraph.type': 'User',
            'username': 'canbo_cntt',
            'password_hash': hash_pw('Canbo@123'),
            'full_name': 'Cán Bộ Khoa CNTT',
            'email': 'vp.cntt@truong.edu.vn',
            'role': 'staff',
            'must_change_password': False,
            'is_active': True,
            'in_faculty': {'uid': faculties_map['CNTT']}
        })

        mutations.append({
            'uid': '_:user_canbo_kt',
            'dgraph.type': 'User',
            'username': 'canbo_kt',
            'password_hash': hash_pw('Canbo@123'),
            'full_name': 'Cán Bộ Khoa Kinh Tế',
            'email': 'vp.kt@truong.edu.vn',
            'role': 'staff',
            'must_change_password': False,
            'is_active': True,
            'in_faculty': {'uid': faculties_map['KT']}
        })

        for gv_code, gv in lecturers_map.items():
            u_gv = f'_:user_{gv_code}'
            mutations.append({
                'uid': u_gv,
                'dgraph.type': 'User',
                'username': f'gv_{gv_code.lower()}',
                'password_hash': hash_pw('Gv@123'),
                'full_name': gv['name'],
                'email': gv['email'],
                'role': 'lecturer',
                'must_change_password': False,
                'is_active': True
            })

        with open(os.path.join(DATA_DIR, 'students.csv'), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s_id = row['student_id']
                u_student = f'_:user_sv_{s_id}'
                fac_uid = faculties_map[row['faculty_code']]
                
                enrolled_sec_uids = []
                for sec_c in row['enrolled_sections'].split(';'):
                    sec_c = sec_c.strip()
                    if sec_c in sections_map:
                        enrolled_sec_uids.append({'uid': sections_map[sec_c]})

                mutations.append({
                    'uid': u_student,
                    'dgraph.type': 'User',
                    'username': f'sv_{s_id}',
                    'password_hash': hash_pw('Sv@123'),
                    'full_name': row['full_name'],
                    'email': row['email'],
                    'role': 'student',
                    'must_change_password': True,
                    'is_active': True,
                    'in_faculty': {'uid': fac_uid},
                    'enrolled_in': enrolled_sec_uids
                })

        print(f"8. Thực thi nạp {len(mutations)} Nodes/Edges vào Dgraph...")
        mu = pydgraph.Mutation(set_json=json.dumps(mutations).encode('utf-8'))
        response = txn.mutate(mu)
        txn.commit()
        print(">>> THÀNH CÔNG: Đã nạp toàn bộ dữ liệu mẫu vào Dgraph!")
        print(f"Tổng số UIDs tạo mới: {len(response.uids)}")

    except Exception as e:
        print(f"LỖI trong quá trình nạp dữ liệu: {e}")
        txn.discard()
        raise e
    finally:
        client_stub.close()

if __name__ == '__main__':
    seed()
