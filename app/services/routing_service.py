from app.dao.routing_dao import RoutingDAO

class RoutingService:
    @staticmethod
    def get_full_fallback_plan(lecturer_uid):
        """
        Tập hợp chuỗi phương án thay thế toàn diện:
        1. Đồng nghiệp giảng dạy cùng môn học phần
        2. Chuỗi leo thang cấp bậc: Trưởng bộ môn -> Văn phòng Khoa
        """
        # 1. Lấy đồng nghiệp dạy cùng môn
        colleagues = RoutingDAO.get_colleague_substitutes(lecturer_uid)

        # 2. Lấy chuỗi leo thang
        chain = RoutingDAO.get_escalation_chain(lecturer_uid)
        
        # Bỏ qua chính node đầu tiên (vì là chính giảng viên này)
        escalation_targets = chain[1:] if len(chain) > 1 else []

        return {
            'colleagues': colleagues,
            'escalation_targets': escalation_targets
        }
