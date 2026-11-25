from datetime import datetime
from app.db import dgraph_db

class LogDAO:
    @staticmethod
    def record_access(student_uid, lecturer_uid):
        try:
            now_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            mutation = {
                'uid': '_:log_node',
                'dgraph.type': 'AccessLog',
                'viewed_at': now_str,
                'viewed_by': {'uid': student_uid},
                'target': {'uid': lecturer_uid}
            }
            dgraph_db.mutate(set_obj=mutation)
        except Exception as e:
            print(f"Lỗi ghi AccessLog: {e}")

    @staticmethod
    def get_recent_logs(limit=50):
        q = f"""
        query {{
          logs(func: type(AccessLog), orderdesc: viewed_at, first: {limit}) {{
            uid
            viewed_at
            viewed_by {{
              uid
              username
              full_name
              role
            }}
            target {{
              uid
              code
              name
              email
            }}
          }}
        }}
        """
        res = dgraph_db.query(q)
        logs = res.get('logs', [])
        
        # Chuẩn hóa an toàn cho template Jinja2
        for l in logs:
            vb = l.get('viewed_by')
            if isinstance(vb, list) and len(vb) > 0:
                l['viewer_username'] = vb[0].get('username', '-')
                l['viewer_name'] = vb[0].get('full_name', '-')
            elif isinstance(vb, dict):
                l['viewer_username'] = vb.get('username', '-')
                l['viewer_name'] = vb.get('full_name', '-')
            else:
                l['viewer_username'] = '-'
                l['viewer_name'] = '-'

            tg = l.get('target')
            if isinstance(tg, list) and len(tg) > 0:
                l['target_name'] = tg[0].get('name', '-')
                l['target_code'] = tg[0].get('code', '-')
                l['target_email'] = tg[0].get('email', '-')
            elif isinstance(tg, dict):
                l['target_name'] = tg.get('name', '-')
                l['target_code'] = tg.get('code', '-')
                l['target_email'] = tg.get('email', '-')
            else:
                l['target_name'] = '-'
                l['target_code'] = '-'
                l['target_email'] = '-'

        return logs

    @staticmethod
    def get_view_statistics():
        q = """
        query {
          lecturers(func: type(Lecturer)) {
            code
            name
            view_count: count(~target)
          }
        }
        """
        res = dgraph_db.query(q)
        items = res.get('lecturers', [])
        items.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        return items
