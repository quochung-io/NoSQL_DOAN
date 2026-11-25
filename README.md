# HỆ THỐNG TRA CỨU VÀ ĐỊNH TUYẾN LIÊN LẠC GIẢNG VIÊN (DGRAPH & RATEL)

Đề tài: **Tìm hiểu công cụ Dgraph Ratel để quản trị CSDL đồ thị cho hệ thống tra cứu và định tuyến liên lạc giảng viên. Xây dựng ứng dụng minh họa.**  
Tài liệu báo cáo chi tiết theo Barem chấm điểm: Xem tại file [NOI_DUNG_DE_TAI_THEO_BAREM.md](file:///D:/Năm%204/NoSQL/NOI_DUNG_DE_TAI_THEO_BAREM.md)

---

## 1. Cấu trúc thư mục dự án
- `docker-compose.yml`: Cấu hình cụm Dgraph Zero, Alpha và giao diện Ratel.
- `data_sample/`: 8 file CSV dữ liệu học tập chuẩn nghiệp vụ (Khoa, Ngành, Giảng viên, Môn, Lớp HP, Sinh viên, Chủ đề).
- `scripts/`:
  - `set_schema.py`: Thiết lập Schema, Types và Indexes trên Dgraph.
  - `seed_data.py`: Đọc CSV và đẩy dữ liệu mẫu vào Dgraph qua Mutation gRPC.
  - `dql_queries.dql`: Bộ câu lệnh DQL cơ bản và nâng cao để chạy và chụp ảnh trên Ratel.
  - `export_backup.py`: Script sao lưu / export dữ liệu ra JSON.
  - `restore_data.py`: Script phục hồi dữ liệu từ bản backup.
- `app/`: Ứng dụng Flask phân tầng hoàn chỉnh (DAO, Services, Routes, Templates).
- `run.py`: Điểm khởi chạy ứng dụng web.

---

## 2. Hướng dẫn cài đặt và chạy trên VS Code

### Bước 1: Khởi động Dgraph và Ratel (Docker)
Tại terminal VS Code (`D:\Năm 4\NoSQL`):
```bash
docker compose up -d
```
- **Dgraph Ratel Web UI:** [http://localhost:8000](http://localhost:8000) (Kết nối Alpha: `http://localhost:8080`)
- **Dgraph Alpha gRPC:** `localhost:9080` (Cổng kết nối của ứng dụng Flask)

### Bước 2: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 3: Nạp Schema và Dữ liệu mẫu vào Dgraph
1. Chạy lệnh nạp schema:
   ```bash
   python scripts/set_schema.py
   ```
2. Chạy lệnh nạp dữ liệu mẫu:
   ```bash
   python scripts/seed_data.py
   ```

### Bước 4: Khởi chạy Ứng dụng Flask
```bash
python run.py
```
Mở trình duyệt truy cập: **[http://localhost:5000](http://localhost:5000)**

---

## 3. Danh sách tài khoản đăng nhập mẫu (4 Roles)

| Vai trò | Tên đăng nhập | Mật khẩu mặc định | Quyền hạn và phạm vi hiển thị |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | • Quản trị toàn bộ tài khoản toàn trường (Khóa/Mở, Reset MK).<br>• Import CSV sinh viên.<br>• Phân công chủ đề xử lý N - N toàn trường.<br>• Backup/Restore và xem nhật ký `AccessLog`. |
| **Cán bộ khoa (Trưởng khoa)** | `canbo_cntt` | `Canbo@123` | • Xem danh sách Giảng viên và Sinh viên **thuộc khoa mình**.<br>• Quản lý và phân công Giảng viên trong khoa cho các chủ đề xử lý (N - N).<br>• Nhắn tin với Giảng viên / Sinh viên trong khoa. |
| **Giảng viên** | `gv_gv01` | `Gv@123` | • Quản lý kênh liên lạc, giờ tiếp sinh viên, mức hiển thị.<br>• **Tự cấu hình Người tiếp nhận thay thế khi vắng mặt** (`escalates_to`).<br>• Nhắn tin với Sinh viên và Giảng viên khác. |
| **Sinh viên** | `sv_20210001` | `Sv@123` | • Bắt buộc đổi mật khẩu trong lần đăng nhập đầu tiên.<br>• Xem thông tin cá nhân và cập nhật số điện thoại (`/student/profile`).<br>• Xem danh sách **toàn bộ giảng viên** toàn trường để tra cứu và lựa chọn người liên lạc.<br>• Xem kênh liên lạc theo phân quyền đồ thị (`all_students`, `same_faculty`, `enrolled_only`, `hidden`).<br>• Xem chuỗi thay thế khi vắng mặt và tìm theo nhu cầu (`Topic`).<br>• Khung chat Messenger nhắn tin với Giảng viên / Trưởng khoa / Admin. |
