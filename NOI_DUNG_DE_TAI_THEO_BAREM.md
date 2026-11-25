# BÁO CÁO TOÀN DIỆN ĐỀ TÀI CƠ SỞ DỮ LIỆU NOSQL (THEO BAREM ĐIỂM)

**Tên đề tài:** Tìm hiểu công cụ Dgraph Ratel để quản trị CSDL đồ thị cho hệ thống tra cứu và định tuyến liên lạc giảng viên. Xây dựng ứng dụng minh họa.  
**Công nghệ chính:** Dgraph (Zero, Alpha), Dgraph Ratel, Python (Flask), pydgraph (gRPC), Bootstrap 5, vis.js.  
**Thư mục dự án:** `D:\Năm 4\NoSQL`

---

## BẢNG TỔNG HỢP ĐỐI CHIẾU TIÊU CHÍ VÀ ĐIỂM SỐ

| STT | Nội dung tiêu chí (Barem) | Điểm | Mức độ đáp ứng trong Project |
| :---: | :--- | :---: | :--- |
| **1** | Tìm hiểu lý thuyết và cài đặt Tool theo yêu cầu đề tài | **0,5** | Khớp 100% - Kiến trúc Dgraph, cài Docker Compose |
| **2** | Trình bày chi tiết các chức năng của Tool đã tìm hiểu | **0,5** | Khớp 100% - Trình bày 4 phân hệ Ratel (Console, Schema, Cluster, Data) |
| **3** | So sánh điểm mạnh, điểm yếu của Tool với một GUI Tool khác | **0,5** | Khớp 100% - So sánh chi tiết Dgraph Ratel với Neo4j Browser |
| **4** | Nêu bật điểm mạnh của Tool với các loại ứng dụng Database nào | **0,5** | Khớp 100% - Định tuyến nhiều tầng, quan hệ N-N, phân quyền ReBAC |
| **5** | Xây dựng Database cho ứng dụng cụ thể (Tạo DB, Insert, Truy vấn cơ bản, Nâng cao) | **2,0** | Khớp 100% - 11 Types, 30+ Predicates, 8 CSV mẫu, DQL đầy đủ |
| **6** | Import/Export dữ liệu; Backup và Restore dữ liệu | **0,5** | Khớp 100% - Import CSV, Export JSON, Kịch bản khắc phục thảm họa |
| **7** | Triển khai truy vấn dữ liệu cơ bản và nâng cao trên GUI Tool | **1,0** | Khớp 100% - Bộ DQL chạy trên Ratel Console, xem Graph & JSON |
| **8** | Triển khai Database kết nối CSDL với phần mềm ứng dụng | **0,5** | Khớp 100% - Kết nối Flask qua pydgraph gRPC port 9080 |
| **9** | Demo ứng dụng (User, Thao tác DB, Nghiệp vụ bài toán, Tính năng hỗ trợ) | **2,0** | Khớp 100% - Đủ 4 roles, Messenger chat, Hồ sơ SV, vis.js |
| **10** | Quyển báo cáo, slide thuyết trình, source code, phân công nhóm | **Đạt** | Cung cấp khung tài liệu, phân chia công việc chuẩn chỉnh |

---

## MỤC 1: TÌM HIỂU LÝ THUYẾT VÀ CÀI ĐẶT TOOL THEO YÊU CẦU ĐỀ TÀI (0,5 ĐIỂM)

### 1.1. Lý thuyết Cơ sở dữ liệu Đồ thị (Graph Database)
- **Khái niệm:** CSDL đồ thị là hệ quản trị CSDL NoSQL sử dụng cấu trúc đồ thị bao gồm các Đỉnh (Nodes/Vertices), Cạnh (Edges/Relationships) và Thuộc tính (Properties/Predicates) để biểu diễn và lưu trữ dữ liệu.
- **Ưu thế vượt trội so với RDBMS:** Trong RDBMS truyền thống, việc biểu diễn quan hệ nhiều - nhiều đòi hỏi bảng trung gian (Junction table) và các phép `JOIN` tốn kém chi phí tính toán khi duyệt qua nhiều cấp bậc. CSDL đồ thị xử lý duyệt quan hệ theo con trỏ trực tiếp (*Index-free adjacency*), giúp thời gian truy vấn đường đi nhiều tầng (Multi-hop) chỉ ở mức $O(k)$ thay vì bùng nổ theo cấp số nhân.

### 1.2. Kiến trúc Hệ quản trị CSDL Dgraph
Dgraph là CSDL đồ thị phân tán mã nguồn mở, hỗ trợ mở rộng ngang (Horizontal scalability), bao gồm 2 thành phần lõi:
1. **Dgraph Zero:** Điều phối cụm (Cluster), kiểm soát giao thức đồng thuận Raft, tự động phân vùng shard dữ liệu và cấp phát mã định danh `UID` cho các node mới.
2. **Dgraph Alpha:** Trực tiếp lưu trữ các bộ ba ngữ nghĩa (Subject - Predicate - Object), quản lý các chỉ mục tìm kiếm và xử lý các câu truy vấn DQL (Dgraph Query Language) / GraphQL.

### 1.3. Cài đặt CSDL Dgraph và GUI Tool Ratel qua Docker
Hệ thống được đóng gói hoàn chỉnh trong file [docker-compose.yml](file:///D:/Năm%204/NoSQL/docker-compose.yml):
```yaml
services:
  zero:
    image: dgraph/dgraph:v23.1.0
    container_name: dgraph-zero
    volumes:
      - dgraph_zero_data:/dgraph
    ports:
      - "5080:5080"
      - "6080:6080"
    restart: unless-stopped
    command: dgraph zero --my=zero:5080

  alpha:
    image: dgraph/dgraph:v23.1.0
    container_name: dgraph-alpha
    volumes:
      - dgraph_alpha_data:/dgraph
    ports:
      - "8080:8080"   # Cổng HTTP API & Ratel kết nối
      - "9080:9080"   # Cổng gRPC API cho ứng dụng Flask
    restart: unless-stopped
    command: dgraph alpha --my=alpha:7080 --zero=zero:5080 --security "whitelist=0.0.0.0/0"
    depends_on:
      - zero

  ratel:
    image: dgraph/ratel:latest
    container_name: dgraph-ratel
    ports:
      - "8000:8000"   # Cổng Web UI của Ratel
    restart: unless-stopped
    depends_on:
      - alpha

volumes:
  dgraph_zero_data:
  dgraph_alpha_data:
```
- **Lệnh khởi động:** `docker compose up -d`
- **Địa chỉ truy cập Ratel:** `http://localhost:8000` (kết nối Alpha tại `http://localhost:8080`).

---

## MỤC 2: TRÌNH BÀY CHI TIẾT CÁC CHỨC NĂNG CỦA TOOL RATEL (0,5 ĐIỂM)

Dgraph Ratel cung cấp giao diện quản trị đồ thị trực quan với 4 phân hệ chính (kèm hướng dẫn chụp ảnh minh chứng):

1. **Phân hệ Console (Thực thi truy vấn):**
   - Hỗ trợ viết và thực thi cả truy vấn đọc (Query) và truy vấn ghi (Mutation) bằng ngôn ngữ DQL.
   - **Graph View:** Trực quan hóa kết quả dưới dạng mạng lưới các Node tròn có thể kéo thả, phóng to, thu nhỏ và hiển thị thuộc tính khi click.
   - **JSON View:** Hiển thị cây cấu trúc JSON nguyên bản trả về từ Dgraph Alpha.
   - *(Vị trí chụp ảnh báo cáo: Chạy câu truy vấn cây học phần và chụp màn hình chế độ Graph View).*
2. **Phân hệ Schema (Quản trị lược đồ):**
   - Danh sách toàn bộ các Predicates và Types trong hệ thống.
   - Hỗ trợ tạo mới predicate, chọn kiểu dữ liệu (`string`, `int`, `datetime`, `uid`, `bool`).
   - Cấu hình chỉ mục Indexes trực tiếp bằng checkbox: `exact`, `term`, `trigram`, `hour`, `@reverse`.
   - *(Vị trí chụp ảnh báo cáo: Mở tab Schema hiển thị các index của predicate `name`, `code`, `role`).*
3. **Phân hệ Cluster (Giám sát cụm):**
   - Giám sát tình trạng hoạt động (Health check) của các nhóm Raft Group, node Zero và node Alpha.
   - Theo dõi phân bổ Shard và dung lượng lưu trữ của từng Group.
   - *(Vị trí chụp ảnh báo cáo: Mở tab Cluster chụp cây trạng thái xanh của cụm Zero và Alpha).*
4. **Phân hệ Data Management & System:**
   - Hỗ trợ thao tác xóa dữ liệu (Drop Data / Drop All) khi cần khởi tạo lại hệ thống.
   - Tích hợp công cụ Import/Export dữ liệu cấp quản trị.

---

## MỤC 3: SO SÁNH ĐIỂM MẠNH, ĐIỂM YẾU CỦA RATEL VỚI GUI TOOL KHÁC (0,5 ĐIỂM)

So sánh đối chiếu giữa **Dgraph Ratel** và **Neo4j Browser** (GUI Tool phổ biến nhất của CSDL đồ thị):

| Tiêu chí so sánh | Dgraph Ratel | Neo4j Browser | Đánh giá & Nhận xét |
| :--- | :--- | :--- | :--- |
| **Ngôn ngữ truy vấn** | **DQL** (dựa trên chuẩn GraphQL) | **Cypher** (mô phỏng SQL với cú pháp ASCII-Art) | DQL dễ tiếp cận hơn với lập trình viên Web; Cypher trực quan hơn về mặt vẽ đường đi |
| **Quản trị Schema** | **Có giao diện riêng biệt**, xem và tạo index bằng click chuột trực quan | Hạn chế, chủ yếu quản lý ràng buộc thông qua câu lệnh Cypher | Ratel vượt trội trong việc kiểm soát Schema và quản lý Types |
| **Quản trị Cụm (Cluster)** | Tích hợp sẵn tab giám sát các Shard, nhóm Raft, Zero và Alpha | Cần công cụ riêng (Neo4j Desktop / Ops Manager) | Ratel hỗ trợ theo dõi kiến trúc phân tán tốt hơn ngay trên trình duyệt |
| **Trực quan hóa đồ thị** | Cơ bản, hiển thị bóng tròn và nhãn cạnh, tùy biến màu sắc hạn chế | Rất mạnh, cho phép đổi màu, kích thước node và icon theo nhãn (Label) | Neo4j Browser có khả năng tùy biến hiển thị đẹp mắt hơn |
| **Hỗ trợ Mutation/Ghi** | Có tab riêng để chạy mutation JSON/RDF trực tiếp | Chạy lệnh `CREATE`, `MERGE` chung trong cửa sổ dòng lệnh | Ratel phân tách rõ ràng giữa đọc và ghi dữ liệu |

---

## MỤC 4: NÊU BẬT THẾ MẠNH CỦA TOOL VỚI CÁC LOẠI ỨNG DỤNG DATABASE (0,5 ĐIỂM)

Dgraph và Ratel phát huy thế mạnh vượt trội đối với các bài toán:

1. **Ứng dụng quan hệ nhiều - nhiều phức tạp (Many-to-Many):**
   - Bài toán quản lý đào tạo: Giảng viên phụ trách nhiều Môn $\leftrightarrow$ Môn có nhiều Lớp HP $\leftrightarrow$ Lớp HP có nhiều Sinh viên $\leftrightarrow$ Sinh viên thuộc Khoa.
   - Quản lý chủ đề xử lý: Một chủ đề có nhiều giảng viên phụ trách và một giảng viên giải quyết nhiều chủ đề.
2. **Ứng dụng định tuyến đệ quy nhiều tầng (Multi-hop Routing):**
   - Duyệt chuỗi leo thang thay thế (`escalates_to` depth 5) khi sinh viên không liên lạc được với giảng viên (Giảng viên $\rightarrow$ Trưởng bộ môn $\rightarrow$ Văn phòng Khoa $\rightarrow$ Phòng Đào tạo). DQL xử lý bằng chỉ thị `@recurse` cực nhanh, không gây quá tải tài nguyên như các câu truy vấn lồng nhau của SQL.
3. **Phân quyền truy cập dựa trên mối quan hệ (ReBAC - Relationship-based Access Control):**
   - Phân quyền động: Kênh liên lạc hiển thị hay ẩn phụ thuộc vào mối quan hệ trong đồ thị giữa Sinh viên và Giảng viên (`same_faculty`, `enrolled_only`).
4. **Hệ thống mạng xã hội và nhắn tin tức thời:**
   - Dgraph tối ưu cho việc biểu diễn các mối liên kết bạn bè, danh sách chat và tin nhắn giữa nhiều thực thể trong mạng lưới.

---

## MỤC 5: XÂY DỰNG DATABASE CHO ỨNG DỤNG CỤ THỂ (2,0 ĐIỂM)

### 5.1. Tạo Database và Lược đồ Schema (0,5 điểm)
Triển khai trong [scripts/set_schema.py](file:///D:/Năm%204/NoSQL/scripts/set_schema.py) với 11 Types và các Predicates có chỉ mục:
- **Node Types:** `Faculty`, `Major`, `Office`, `Lecturer`, `Subject`, `Section`, `Channel`, `Topic`, `User`, `AccessLog`, `Message`.
- **Chỉ mục Index tối ưu hóa:**
  - `name`, `full_name`: `@index(term, exact)` $\rightarrow$ phục vụ tìm kiếm gần đúng và chính xác.
  - `code`, `username`, `email`, `role`, `visibility`: `@index(exact)` $\rightarrow$ phục vụ lọc và đăng nhập.
  - `viewed_at`, `sent_at`: `@index(hour)` $\rightarrow$ phục vụ thống kê nhật ký và tin nhắn.
  - Các quan hệ: `@reverse` $\rightarrow$ cho phép truy vấn ngược 2 chiều không tốn chi phí (ví dụ từ Môn học tra ngược ra Giảng viên phụ trách qua `~taught_by`).

### 5.2. Nạp Dữ liệu Mẫu Đầy đủ cho Ứng dụng (0,5 điểm)
Dữ liệu học tập được thiết kế chuẩn mực trong thư mục [data_sample/](file:///D:/Năm%204/NoSQL/data_sample/):
- **2 Khoa:** Khoa Công nghệ Thông tin, Khoa Kinh tế & QTKD.
- **5 Ngành:** Kỹ thuật Phần mềm, Khoa học Máy tính, Hệ thống Thông tin, Quản trị Kinh doanh, Tài chính Ngân hàng.
- **25 Giảng viên:** Đầy đủ học hàm, học vị, chức danh Trưởng bộ môn, email, số điện thoại, lịch trực văn phòng.
- **25 Môn học & 50 Lớp học phần:** Phân bổ đầy đủ giảng viên, phòng học, học kỳ.
- **20 Sinh viên:** Đã liên kết quan hệ Khoa (`in_faculty`) và các lớp học phần đang theo học (`enrolled_in`).
- **10 Chủ đề xử lý:** Hoãn thi, phúc khảo, đăng ký đồ án, cố vấn học tập,...
- Nạp tự động qua script [scripts/seed_data.py](file:///D:/Năm%204/NoSQL/scripts/seed_data.py) với mật khẩu người dùng được băm an toàn bằng **bcrypt**.

### 5.3. Dữ liệu Đáp ứng Truy vấn Cơ bản (0,5 điểm)
- Lấy toàn bộ Khoa và Ngành trực thuộc.
- Tìm kiếm giảng viên theo từ khóa tên (`allofterms`).
- Lấy danh sách lớp học phần của một môn học.
- Lấy toàn bộ kênh liên lạc của giảng viên.

### 5.4. Dữ liệu Đáp ứng Truy vấn Nâng cao (0,5 điểm)
- Truy vấn đệ quy chuỗi leo thang người thay thế (`@recurse`).
- Truy vấn kiểm tra quan hệ đồ thị giữa Sinh viên và Giảng viên để mở khóa các kênh `enrolled_only`.
- Định tuyến theo chủ đề nhu cầu (`Topic` $\rightarrow$ `handles` quan hệ N - N).
- Truy vấn toàn bộ mạng lưới cấu trúc phục vụ trực quan hóa trên vis.js.

---

## MỤC 6: IMPORT/EXPORT DỮ LIỆU; BACKUP VÀ RESTORE DỮ LIỆU (0,5 ĐIỂM)

1. **Import dữ liệu:**
   - Dữ liệu CSV từ `data_sample/` được script [seed_data.py](file:///D:/Năm%204/NoSQL/scripts/seed_data.py) chuyển đổi thành các Node và Edge, đẩy vào Dgraph qua Mutation gRPC.
   - Chức năng Import tài khoản sinh viên từ file CSV trên giao diện web Admin (`/admin/import-students`).
2. **Export / Sao lưu dữ liệu (Backup):**
   - Triển khai trong [scripts/export_backup.py](file:///D:/Năm%204/NoSQL/scripts/export_backup.py) hoặc nút bấm trên giao diện Web Admin (`/admin/backup`).
   - Dữ liệu toàn bộ node và edge được trích xuất ra file `backup_data.json`.
3. **Phục hồi dữ liệu (Restore) & Giả lập khắc phục sự cố:**
   - Triển khai kịch bản kiểm thử thảm họa:
     - *Bước 1:* Bấm **Xuất bản sao lưu (Backup)** $\rightarrow$ ghi nhận tệp dự phòng.
     - *Bước 2:* Bấm **Giả lập sự cố (Drop All)** $\rightarrow$ xóa sạch dữ liệu trên Dgraph.
     - *Bước 3:* Bấm **Phục hồi (Restore)** $\rightarrow$ script [restore_data.py](file:///D:/Năm%204/NoSQL/scripts/restore_data.py) tự động tái lập Schema, Indexes và nạp lại toàn bộ dữ liệu nguyên trạng ban đầu.

---

## MỤC 7: TRIỂN KHAI TRUY VẤN DỮ LIỆU TRÊN GUI TOOL RATEL (1,0 ĐIỂM)

*(Toàn bộ mã lệnh DQL đã được lưu sẵn trong file [scripts/dql_queries.dql](file:///D:/Năm%204/NoSQL/scripts/dql_queries.dql) để copy vào Ratel).*

### 7.1. Truy vấn Cơ bản trên Ratel (0,5 điểm)
```dql
# Truy vấn tìm kiếm giảng viên theo tên (sử dụng allofterms)
query SearchLecturer {
  lecturers(func: allofterms(name, "Nguyễn Văn")) @filter(type(Lecturer)) {
    uid
    code
    name
    email
    title
    belongs_to {
      major_name: name
    }
    has_channel {
      channel_type
      channel_value
      visibility
    }
  }
}
```

### 7.2. Truy vấn Nâng cao trên Ratel (0,5 điểm)
```dql
# Truy vấn đệ quy chuỗi leo thang người thay thế (Multi-hop Escalation)
query GetEscalationChain {
  escalation(func: eq(code, "GV02")) @filter(type(Lecturer)) @recurse(depth: 5) {
    name
    title
    email
    phone
    location
    escalates_to
    has_channel {
      channel_type
      channel_value
      visibility
    }
  }
}
```

---

## MỤC 8: KẾT NỐI CSDL VỚI PHẦN MỀM ỨNG DỤNG (0,5 ĐIỂM)

- **Công nghệ kết nối:** Python Flask kết nối với Dgraph Alpha thông qua thư viện chính thức `pydgraph` giao tiếp qua cổng gRPC `9080`.
- **Quản lý kết nối tập trung (`app/db.py`):**
  - Cung cấp đối tượng Singleton `dgraph_db` quản lý `DgraphClient` và `DgraphClientStub`.
  - Đóng gói các hàm thực thi truy vấn `query(query_str)` và ghi dữ liệu `mutate(set_obj, del_obj)` an toàn, tự động đóng/hủy transaction (`txn.discard()`).
- **Kiến trúc phân tầng chuyên nghiệp (DAO Pattern):**
  - `UserDAO`: Xác thực tài khoản, băm bcrypt, phân quyền, truy vấn quan hệ sinh viên.
  - `LecturerDAO`: Tìm kiếm giảng viên đa tiêu chí, quản lý kênh, giờ tiếp sinh viên.
  - `RoutingDAO`: Định tuyến leo thang `@recurse`, tìm đồng nghiệp dạy cùng môn, xử lý chủ đề N - N.
  - `ChatDAO`: Quản lý tin nhắn tức thời, lưu trữ lịch sử chat giữa các người dùng.
  - `LogDAO`: Ghi nhận và thống kê nhật ký truy cập `AccessLog`.
  - `GraphDAO`: Trích xuất cây đồ thị Khoa - Ngành - Giảng viên - Môn học để trực quan hóa trên web.

---

## MỤC 9: DEMO ỨNG DỤNG THEO MÔ TẢ BÀI TOÁN (2,0 ĐIỂM)

### 9.1. Quản trị Người dùng (0,5 điểm)
- Hệ thống hỗ trợ đầy đủ 4 nhóm vai trò (Roles) với tài khoản có sẵn:
  - **Admin:** `admin` / `Admin@123`
  - **Cán bộ khoa (Trưởng khoa):** `canbo_cntt` / `Canbo@123`
  - **Giảng viên:** `gv_gv01` / `Gv@123`
  - **Sinh viên:** `sv_20210001` / `Sv@123`
- Cơ chế bảo mật: Mật khẩu băm bằng **bcrypt**, tài khoản sinh viên mới cấp có cờ `must_change_password = true` bắt buộc phải đổi mật khẩu ngay lần đầu đăng nhập.
- Admin có thể khóa/mở khóa tài khoản, reset mật khẩu về mặc định và import sinh viên từ file CSV.

### 9.2. Thao tác trên CSDL (0,5 điểm)
- Thêm mới, chỉnh sửa, xóa kênh liên lạc và cập nhật khung giờ tiếp sinh viên.
- Admin và Cán bộ khoa tạo mới, chỉnh sửa và xóa chủ đề xử lý; phân công nhiều giảng viên phụ trách chủ đề (N - N).
- Thao tác Backup JSON, Giả lập sự cố xóa sạch CSDL và Phục hồi Restore trực tiếp trên giao diện web.

### 9.3. Chức năng Quản lý Nghiệp vụ Bài toán (0,5 điểm)
- **Sinh viên:** 
  - Xem toàn bộ danh sách giảng viên toàn trường để tra cứu và lựa chọn người liên lạc.
  - Hệ thống tự động lọc mức hiển thị kênh dựa trên cấu trúc đồ thị:
    - `all_students`: Mọi sinh viên đều thấy.
    - `same_faculty`: Chỉ sinh viên cùng khoa mới xem được.
    - `enrolled_only`: Chỉ sinh viên đang học lớp học phần của giảng viên mới xem được.
    - `hidden`: Ẩn hoàn toàn với sinh viên.
  - Kiểm tra trạng thái khả dụng thời gian thực (Đang trong giờ hay Ngoài giờ làm việc).
  - Bấm **"Không liên lạc được? Xem chuỗi thay thế"**: hiển thị chuỗi leo thang (Trưởng bộ môn $\rightarrow$ Văn phòng khoa) và các đồng nghiệp dạy cùng môn học.
  - **Tìm theo nhu cầu:** Nhập từ khóa (hoãn thi, phúc khảo, đồ án...) $\rightarrow$ hệ thống trả về chính xác đơn vị/giảng viên giải quyết.
- **Giảng viên:** 
  - Tự quản lý kênh liên lạc và giờ tiếp sinh viên.
  - Tự thiết lập người tiếp nhận thay thế khi vắng mặt (`escalates_to`).
- **Cán bộ khoa (Trưởng khoa):** 
  - Xem danh sách giảng viên và sinh viên thuộc khoa mình phụ trách.
  - Quản lý phân công giảng viên trong khoa cho các chủ đề xử lý (N - N).
- **Admin:** 
  - Xem toàn bộ người dùng toàn trường (có tab lọc theo từng vai trò).
  - Quản lý chủ đề xử lý và phân công giảng viên trên toàn trường.

### 9.4. Các Chức năng Hỗ trợ Nâng cao (0,5 điểm)
1. **Hệ thống Tin nhắn Thời gian thực (Phong cách Facebook Messenger - `/chat`):**
   - Hỗ trợ cả 4 nhóm vai trò có thể nhắn tin hai chiều cho nhau.
   - Danh sách cuộc trò chuyện ban đầu sạch sẽ (chỉ hiển thị những người đã từng phát sinh tin nhắn).
   - Thanh liên hệ nhanh với **Admin** và **Cán bộ khoa (Trưởng khoa)** ngay trên đầu trang chat.
   - Khung chat chia 2 cột chuẩn Messenger: có chấm xanh online, bong bóng chat xanh/trắng, mốc giờ, tự động cuộn (auto-scroll) và cập nhật tin nhắn mới mỗi 3 giây.
2. **Trang Hồ sơ Sinh viên (`/student/profile`):**
   - Xem thông tin cá nhân và cập nhật số điện thoại liên lạc.
   - Bảng tổng hợp các Lớp học phần đang học kỳ này kèm tên Giảng viên trực tiếp giảng dạy và nút bấm nhanh **"Nhắn tin ngay"**.
3. **Nhật ký Truy cập (Audit Trail - `AccessLog`):**
   - Tự động ghi nhận mỗi khi người dùng tra cứu thẻ giảng viên (thời gian, người xem, giảng viên được xem).
   - Biểu đồ thống kê top các giảng viên được tra cứu nhiều nhất.
4. **Trực quan hóa Đồ thị Tương tác (vis.js - `/student/graph`):**
   - Trực quan hóa cấu trúc mạng lưới: Khoa (Xanh đậm) $\rightarrow$ Ngành (Xanh dương) $\rightarrow$ Giảng viên (Xanh lá) $\rightarrow$ Môn học (Vàng cam).
   - Hỗ trợ kéo thả, phóng to, thu nhỏ và phân bổ vật lý tự nhiên (Physics simulation).

---

## MỤC 10: QUYỂN BÁO CÁO, SLIDE THUYẾT TRÌNH VÀ PHÂN CHIA CÔNG VIỆC

### 10.1. Cấu trúc Quyển Báo cáo (Word)
- **Trang bìa & Lời cảm ơn:** Theo mẫu chuẩn của khoa.
- **Chương 1: Tổng quan đề tài & Lý thuyết CSDL đồ thị:** Giới thiệu bài toán định tuyến giảng viên, kiến trúc Dgraph và công cụ Dgraph Ratel.
- **Chương 2: Tìm hiểu công cụ Dgraph Ratel & So sánh:** Trình bày chi tiết 4 phân hệ Ratel, bảng so sánh Ratel với Neo4j Browser, thế mạnh bài toán.
- **Chương 3: Thiết kế Hệ thống & CSDL Đồ thị:** Lược đồ Schema Dgraph (11 Types, 30+ Predicates), mô hình quan hệ ER đồ thị, quy mô dữ liệu mẫu.
- **Chương 4: Triển khai Truy vấn trên Ratel & Xây dựng Ứng dụng Flask:** Trình bày các câu lệnh DQL cơ bản/nâng cao (kèm ảnh chụp Ratel), kiến trúc ứng dụng web, phân quyền 4 vai trò, hệ thống Messenger chat, trực quan hóa vis.js.
- **Chương 5: Kết luận & Hướng phát triển:** Đánh giá mức độ hoàn thành, bài học kinh nghiệm.
- **Tài liệu tham khảo:** Dgraph Documentation, pydgraph GitHub, Flask Documentation.

### 10.2. Bảng Phân chia Công việc Mẫu (Nhóm 3 - 4 thành viên)

| Thành viên | Nhiệm vụ chính phụ trách | Sản phẩm bàn giao |
| :--- | :--- | :--- |
| **Thành viên 1 (Trưởng nhóm)** | • Thiết kế Schema Dgraph, viết script seed dữ liệu mẫu.<br>• Xây dựng tầng kết nối gRPC và DAO.<br>• Viết các câu lệnh DQL cơ bản và nâng cao trên Ratel. | `set_schema.py`, `seed_data.py`, `dql_queries.dql`, Báo cáo Chương 1 & 3 |
| **Thành viên 2** | • Phát triển backend Flask (Routes, Services phân quyền ReBAC).<br>• Triển khai luồng nghiệp vụ Sinh viên, Giảng viên và Cán bộ khoa.<br>• Viết script Backup và Restore dữ liệu. | `student_routes.py`, `lecturer_routes.py`, `staff_routes.py`, `export_backup.py`, Báo cáo Chương 4 |
| **Thành viên 3** | • Xây dựng hệ thống Chat Messenger thời gian thực.<br>• Tích hợp thư viện vis.js trực quan hóa đồ thị.<br>• Thiết kế giao diện UI/UX Bootstrap 5 hiện đại, thân thiện. | `chat_routes.py`, `messenger.html`, `style.css`, `graph_explorer.html`, Slide PowerPoint |
| **Thành viên 4** | • Cài đặt và thử nghiệm môi trường Docker Compose.<br>• Thực hiện các thao tác quản trị trên Ratel và chụp ảnh minh chứng.<br>• Tổng hợp quyển báo cáo Word, rà soát chính tả và định dạng. | `docker-compose.yml`, Tổng hợp file Word Báo cáo, Kịch bản thuyết trình Demo |
