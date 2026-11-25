from app.db import dgraph_db

class LecturerDAO:
    @staticmethod
    def search_lecturers(keyword='', faculty_code='', major_code='', subject_code=''):
        filters = ['type(Lecturer)']
        
        if keyword:
            filters.append(f'anyofterms(name, "{keyword}")')

        q = f"""
        query {{
          lecturers(func: {filters[0]}) @filter({' AND '.join(filters[1:]) if len(filters) > 1 else 'type(Lecturer)'}) {{
            uid
            code
            name
            email
            title
            is_head
            belongs_to {{
              uid
              code
              name
              ~has_major {{
                uid
                code
                name
              }}
            }}
            ~taught_by {{
              code
              of_subject {{
                code
                name
              }}
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        lecturers = res.get('lecturers', [])

        filtered = []
        for gv in lecturers:
            major = gv.get('belongs_to', {})
            fac_raw = major.get('~has_major')
            fac = fac_raw[0] if isinstance(fac_raw, list) and fac_raw else (fac_raw if isinstance(fac_raw, dict) else {})

            if faculty_code and fac.get('code') != faculty_code:
                continue
            if major_code and major.get('code') != major_code:
                continue
            if subject_code:
                taught_subjects = [s.get('of_subject', {}).get('code') for s in gv.get('~taught_by', []) if s.get('of_subject')]
                if subject_code not in taught_subjects:
                    continue

            gv['faculty'] = fac
            gv['major'] = major
            filtered.append(gv)

        return filtered

    @staticmethod
    def get_by_uid(uid):
        q = f"""
        query {{
          lecturer(func: uid({uid})) @filter(type(Lecturer)) {{
            uid
            code
            name
            email
            title
            is_head
            belongs_to {{
              uid
              code
              name
              ~has_major {{
                uid
                code
                name
              }}
            }}
            has_channel {{
              uid
              channel_type
              channel_value
              visibility
              active_days
              start_time
              end_time
            }}
            escalates_to {{
              uid
              name
              title
              email
              phone
              location
            }}
            ~taught_by {{
              uid
              code
              room
              semester
              of_subject {{
                code
                name
                credits
              }}
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        data = res.get('lecturer', [])
        return data[0] if data else None

    @staticmethod
    def get_by_email(email):
        q = f"""
        query {{
          lecturer(func: eq(email, "{email}")) @filter(type(Lecturer)) {{
            uid
            code
            name
            email
            title
            is_head
            belongs_to {{
              code
              name
            }}
            escalates_to {{
              uid
              name
              title
            }}
            has_channel {{
              uid
              channel_type
              channel_value
              visibility
              active_days
              start_time
              end_time
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        data = res.get('lecturer', [])
        return data[0] if data else None

    @staticmethod
    def update_escalation(lecturer_uid, target_uid):
        """
        Giảng viên tự thiết lập chuỗi người thay thế leo thang của chính mình
        """
        mutation = {
            'uid': lecturer_uid,
            'escalates_to': {'uid': target_uid}
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def update_channel(channel_uid, updates):
        mutation = {
            'uid': channel_uid,
            'dgraph.type': 'Channel',
            **updates
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def add_channel(lecturer_uid, channel_data):
        c_uid = '_:new_channel'
        c_node = {
            'uid': c_uid,
            'dgraph.type': 'Channel',
            **channel_data
        }
        link = {
            'uid': lecturer_uid,
            'has_channel': [{'uid': c_uid}]
        }
        dgraph_db.mutate(set_obj=[c_node, link])

    @staticmethod
    def delete_channel(channel_uid):
        del_node = {'uid': channel_uid}
        dgraph_db.mutate(del_obj=del_node)

    @staticmethod
    def get_all_faculties_and_majors():
        q = """
        query {
          faculties(func: type(Faculty)) {
            uid
            code
            name
            has_office {
              uid
              name
              location
              phone
              email
            }
            has_major {
              uid
              code
              name
            }
          }
        }
        """
        res = dgraph_db.query(q)
        return res.get('faculties', [])

    @staticmethod
    def get_all_subjects():
        q = """
        query {
          subjects(func: type(Subject), orderasc: code) {
            uid
            code
            name
            credits
          }
        }
        """
        res = dgraph_db.query(q)
        return res.get('subjects', [])
