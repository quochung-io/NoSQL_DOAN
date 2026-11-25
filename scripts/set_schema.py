import os
# Khắc phục lỗi tương thích giữa pydgraph và protobuf phiên bản mới
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pydgraph

def get_client():
    host = os.environ.get('DGRAPH_HOST', 'localhost')
    port = os.environ.get('DGRAPH_GRPC_PORT', '9080')
    client_stub = pydgraph.DgraphClientStub(f'{host}:{port}')
    return pydgraph.DgraphClient(client_stub), client_stub

def set_schema(drop_all=False):
    client, client_stub = get_client()
    try:
        if drop_all:
            print("Đang xóa toàn bộ dữ liệu và schema cũ (Drop All)...")
            client.alter(pydgraph.Operation(drop_all=True))

        schema = """
        # Định danh & thông tin cơ bản
        code: string @index(exact) .
        name: string @index(term, exact) .
        full_name: string @index(term, exact) .
        email: string @index(exact) .
        phone: string .
        location: string .
        title: string .
        is_head: bool .
        credits: int .
        semester: string .
        room: string .
        description: string .
        
        # Tài khoản & xác thực
        username: string @index(exact) .
        password_hash: string .
        role: string @index(exact) .
        must_change_password: bool .
        is_active: bool .
        
        # Quan hệ cơ cấu tổ chức & đào tạo
        has_major: [uid] @reverse .
        has_office: [uid] @reverse .
        belongs_to: uid @reverse .
        offers: [uid] @reverse .
        of_subject: uid @reverse .
        taught_by: uid @reverse .
        
        # Kênh liên lạc & định tuyến
        channel_type: string @index(exact) . # email, phone, zalo, teams, office_hours
        channel_value: string .
        visibility: string @index(exact) .   # all_students, same_faculty, enrolled_only, hidden
        active_days: [string] .              # Mon, Tue, Wed, Thu, Fri, Sat
        start_time: string .                 # 08:00
        end_time: string .                   # 11:30
        has_channel: [uid] @reverse .
        
        # Chuỗi thay thế leo thang (Escalation)
        escalates_to: uid @reverse .
        
        # Chủ đề xử lý theo nhu cầu
        topic_name: string @index(term, exact) .
        handles: [uid] @reverse .
        
        # Quan hệ sinh viên & phân quyền ngữ cảnh
        enrolled_in: [uid] @reverse .
        in_faculty: uid @reverse .
        
        # Nhật ký truy cập (Audit Log)
        viewed_at: datetime @index(hour) .
        viewed_by: uid @reverse .
        target: uid @reverse .
        
        # Tin nhắn trò chuyện (Messenger Chat)
        message_text: string .
        sent_at: datetime @index(hour) .
        sender: uid @reverse .
        receiver: uid @reverse .

        # Định nghĩa các Types
        type Faculty {
            code
            name
            has_major
            has_office
        }
        
        type Major {
            code
            name
            offers
        }
        
        type Office {
            name
            phone
            email
            location
            has_channel
        }
        
        type Subject {
            code
            name
            credits
        }
        
        type Section {
            code
            semester
            room
            of_subject
            taught_by
        }
        
        type Lecturer {
            code
            name
            email
            title
            is_head
            belongs_to
            has_channel
            escalates_to
        }
        
        type Channel {
            channel_type
            channel_value
            visibility
            active_days
            start_time
            end_time
        }
        
        type Topic {
            topic_name
            description
            handles
        }
        
        type User {
            username
            password_hash
            full_name
            email
            phone
            role
            must_change_password
            is_active
            enrolled_in
            in_faculty
        }
        
        type AccessLog {
            viewed_at
            viewed_by
            target
        }

        type Message {
            message_text
            sent_at
            sender
            receiver
        }
        """

        op = pydgraph.Operation(schema=schema)
        client.alter(op)
        print(">>> THÀNH CÔNG: Đã khởi tạo Schema và Indexes trên Dgraph!")
    finally:
        client_stub.close()

if __name__ == '__main__':
    set_schema(drop_all=True)
