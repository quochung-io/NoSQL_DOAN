from app.db import dgraph_db

class RoutingDAO:
    @staticmethod
    def get_escalation_chain(lecturer_uid):
        """
        Truy vấn chuỗi thay thế leo thang qua quan hệ escalates_to bằng @recurse:
        Giảng viên -> Giảng viên trưởng bộ môn / Văn phòng khoa
        """
        q = f"""
        query {{
          chain(func: uid({lecturer_uid})) @recurse(depth: 5) {{
            uid
            name
            title
            email
            phone
            location
            escalates_to
            has_channel {{
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
        return res.get('chain', [])

    @staticmethod
    def get_colleague_substitutes(lecturer_uid):
        """
        Tìm đồng nghiệp cùng giảng dạy môn học đó để thay thế khẩn cấp
        """
        q = f"""
        query {{
          var(func: uid({lecturer_uid})) {{
            ~taught_by {{
              of_subject {{
                Subjects as uid
              }}
            }}
          }}

          colleagues(func: type(Lecturer)) @filter(not(uid({lecturer_uid}))) {{
            uid
            code
            name
            email
            title
            ~taught_by @filter(uid_in(of_subject, uid(Subjects))) {{
              of_subject {{
                code
                name
              }}
            }}
            has_channel {{
              channel_type
              channel_value
              visibility
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        raw = res.get('colleagues', [])
        return [c for c in raw if c.get('~taught_by')]

    @staticmethod
    def search_topics(keyword=''):
        if keyword:
            filter_exp = f'anyofterms(topic_name, "{keyword}")'
        else:
            filter_exp = 'type(Topic)'

        q = f"""
        query {{
          topics(func: {filter_exp}) @filter(type(Topic)) {{
            uid
            topic_name
            description
            handles {{
              uid
              code
              name
              title
              email
              phone
              location
              belongs_to {{
                name
                ~has_major {{
                  code
                  name
                }}
              }}
              has_channel {{
                channel_type
                channel_value
                visibility
                active_days
                start_time
                end_time
              }}
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        return res.get('topics', [])

    @staticmethod
    def create_topic(topic_name, description, handler_uids):
        """
        Tạo chủ đề xử lý mới. Hỗ trợ quan hệ nhiều - nhiều:
        Một chủ đề có thể gán cho NHIỀU giảng viên phụ trách.
        """
        mutation = {
            'uid': '_:new_topic',
            'dgraph.type': 'Topic',
            'topic_name': topic_name.strip(),
            'description': description.strip()
        }
        if handler_uids:
            mutation['handles'] = [{'uid': u} for u in handler_uids]

        res = dgraph_db.mutate(set_obj=mutation)
        return res.uids.get('new_topic')

    @staticmethod
    def update_topic(topic_uid, topic_name, description, handler_uids):
        """
        Cập nhật chủ đề và danh sách giảng viên phụ trách
        """
        mutation = {
            'uid': topic_uid,
            'topic_name': topic_name.strip(),
            'description': description.strip(),
            'handles': [{'uid': u} for u in handler_uids]
        }
        dgraph_db.mutate(set_obj=mutation)

    @staticmethod
    def delete_topic(topic_uid):
        mutation = {'uid': topic_uid}
        dgraph_db.mutate(del_obj=mutation)
