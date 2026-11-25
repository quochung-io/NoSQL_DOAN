from datetime import datetime

class VisibilityService:
    DAY_MAP = {
        0: 'Mon',
        1: 'Tue',
        2: 'Wed',
        3: 'Thu',
        4: 'Fri',
        5: 'Sat',
        6: 'Sun'
    }

    @classmethod
    def is_channel_active_now(cls, channel):
        """
        Kiểm tra kênh liên lạc có đang trong giờ khả dụng hay không
        dựa trên thứ và khung giờ hiện tại.
        """
        now = datetime.now()
        current_day_str = cls.DAY_MAP.get(now.weekday())
        current_time_str = now.strftime('%H:%M')

        active_days = channel.get('active_days', [])
        start_time = channel.get('start_time', '')
        end_time = channel.get('end_time', '')

        if not active_days or not start_time or not end_time:
            # Nếu không cấu hình giờ -> mặc định luôn khả dụng
            return True, "Sẵn sàng nhận tin"

        if current_day_str not in active_days:
            days_vn = ", ".join(active_days)
            return False, f"Chỉ hoạt động vào các ngày: {days_vn}"

        if start_time <= current_time_str <= end_time:
            return True, f"Đang khả dụng ({start_time} - {end_time})"
        else:
            return False, f"Ngoài giờ làm việc (Khung giờ: {start_time} - {end_time})"

    @classmethod
    def filter_channels(cls, channels, student_relations, lecturer_faculty_uid, lecturer_uid, viewer_role='student'):
        """
        Lọc danh sách kênh liên lạc theo quyền xem và ngữ cảnh quan hệ đồ thị:
        - all_students: Mọi sinh viên đã đăng nhập
        - same_faculty: Cùng khoa với giảng viên
        - enrolled_only: Đang học lớp của giảng viên này
        - hidden: Ẩn hoàn toàn với sinh viên
        """
        # Nếu là giảng viên tự xem, cán bộ hoặc admin -> hiển thị tất cả kèm badge
        if viewer_role in ['lecturer', 'staff', 'admin']:
            result = []
            for ch in channels:
                active, status_msg = cls.is_channel_active_now(ch)
                ch_copy = dict(ch)
                ch_copy['is_active_now'] = active
                ch_copy['status_message'] = status_msg
                ch_copy['accessible'] = True
                result.append(ch_copy)
            return result

        student_fac_uid = student_relations.get('faculty_uid')
        enrolled_gv_uids = student_relations.get('enrolled_lecturer_uids', set())

        is_same_faculty = (student_fac_uid and lecturer_faculty_uid and student_fac_uid == lecturer_faculty_uid)
        is_enrolled = (lecturer_uid in enrolled_gv_uids)

        filtered = []
        for ch in channels:
            vis = ch.get('visibility', 'all_students')
            if vis == 'hidden':
                continue

            accessible = False
            reason = ""

            if vis == 'all_students':
                accessible = True
            elif vis == 'same_faculty':
                if is_same_faculty:
                    accessible = True
                else:
                    reason = "Kênh này chỉ dành cho sinh viên cùng Khoa"
            elif vis == 'enrolled_only':
                if is_enrolled:
                    accessible = True
                else:
                    reason = "Chỉ sinh viên đang học lớp học phần của Thầy/Cô mới được xem"

            if accessible:
                active, status_msg = cls.is_channel_active_now(ch)
                ch_copy = dict(ch)
                ch_copy['is_active_now'] = active
                ch_copy['status_message'] = status_msg
                ch_copy['accessible'] = True
                filtered.append(ch_copy)
            else:
                # Hiển thị kênh nhưng làm mờ và thông báo điều kiện
                ch_copy = dict(ch)
                ch_copy['channel_value'] = "****** (Bị giới hạn)"
                ch_copy['is_active_now'] = False
                ch_copy['status_message'] = reason
                ch_copy['accessible'] = False
                filtered.append(ch_copy)

        return filtered
