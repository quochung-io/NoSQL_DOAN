from app.db import dgraph_db

class GraphDAO:
    @staticmethod
    def get_network_graph():
        """
        Truy vấn toàn bộ cây cơ cấu: Khoa -> Ngành -> Giảng viên -> Môn học
        và chuyển đổi sang định dạng nodes & edges của vis.js
        """
        q = """
        query {
          faculties(func: type(Faculty)) {
            uid
            code
            name
            has_major {
              uid
              code
              name
              ~belongs_to {
                uid
                code
                name
                title
                ~taught_by {
                  of_subject {
                    uid
                    code
                    name
                  }
                }
              }
            }
          }
        }
        """
        res = dgraph_db.query(q)
        faculties = res.get('faculties', [])

        nodes_map = {}
        edges = []

        for f in faculties:
            f_id = f['uid']
            if f_id not in nodes_map:
                nodes_map[f_id] = {
                    'id': f_id,
                    'label': f"{f['name']}\n({f['code']})",
                    'group': 'faculty',
                    'color': '#1E3A8A', # Dark blue
                    'font': {'color': '#ffffff'}
                }

            for m in f.get('has_major', []):
                m_id = m['uid']
                if m_id not in nodes_map:
                    nodes_map[m_id] = {
                        'id': m_id,
                        'label': f"{m['name']}\n({m['code']})",
                        'group': 'major',
                        'color': '#0284C7', # Light blue
                        'font': {'color': '#ffffff'}
                    }
                edges.append({'from': f_id, 'to': m_id, 'label': 'has_major'})

                for gv in m.get('~belongs_to', []):
                    gv_id = gv['uid']
                    if gv_id not in nodes_map:
                        nodes_map[gv_id] = {
                            'id': gv_id,
                            'label': f"{gv['name']}\n({gv['code']})",
                            'group': 'lecturer',
                            'color': '#10B981', # Green
                            'font': {'color': '#ffffff'}
                        }
                    edges.append({'from': m_id, 'to': gv_id, 'label': 'belongs_to'})

                    for sec in gv.get('~taught_by', []):
                        sub = sec.get('of_subject')
                        if sub:
                            s_id = sub['uid']
                            if s_id not in nodes_map:
                                nodes_map[s_id] = {
                                    'id': s_id,
                                    'label': f"{sub['name']}\n({sub['code']})",
                                    'group': 'subject',
                                    'color': '#F59E0B', # Amber/Yellow
                                    'font': {'color': '#000000'}
                                }
                            edges.append({'from': gv_id, 'to': s_id, 'label': 'teaches'})

        return {
            'nodes': list(nodes_map.values()),
            'edges': edges
        }
