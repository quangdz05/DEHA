import os
import traceback
from functools import lru_cache
from pathlib import Path

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gym_booking_backend.domain.result import Result
from gym_booking_backend.presentation.views import BaseAPIView

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - chi xay ra khi chua cai dependency
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = BASE_DIR / "chatbot_knowledge.txt"

VALID_USER_TYPES = {
    "Giam_Can": "Uu tien giam mo, cardio, kiem soat calo, tap deu va duy tri thoi quen.",
    "Tang_Co": "Uu tien tang co, tap ta dung ky thuat, nap du protein va phuc hoi hop ly.",
    "Van_Phong": "Uu tien giam dau moi, van dong nhe, cai thien tu the va gian co.",
}


if load_dotenv:
    # Load file .env o thu muc backend de khong hard-code API key trong source code.
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@lru_cache(maxsize=1)
def load_knowledge():
    """Doc kho tri thuc tu file rieng va cache lai cho cac request sau."""

    try:
        content = KNOWLEDGE_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError("Khong doc duoc file chatbot_knowledge.txt") from exc

    if not content:
        raise RuntimeError("File chatbot_knowledge.txt dang rong")

    return content


def format_history(history):
    """Chuyen lich su chat tu frontend thanh dang van ban ngan gon cho prompt."""

    if not isinstance(history, list) or not history:
        return "Chua co lich su chat."

    lines = []
    for item in history[-12:]:
        if not isinstance(item, dict):
            continue

        role = "Khach" if item.get("role") == "user" else "Bot"
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines) if lines else "Chua co lich su chat."


def build_prompt(message, user_type, history, knowledge):
    """Tao system instruction va prompt day du de gui cho Gemini."""

    system_instruction = """
Ban la tu van vien phong gym chuyen nghiep.
Hay tra loi bang tieng Viet, ngan gon, than thien va de hieu.
Uu tien tra loi dua tren KHO TRI THUC neu co thong tin lien quan.
Neu khong chac chan, hay noi khach nen gap nhan vien tu van hoac huan luyen vien.
Khong dua loi khuyen y te nguy hiem, khong chan doan benh, khong khuyen tap qua suc.
Khong bia thong tin ve gia, goi tap, uu dai, lich lop hoac lich huan luyen neu KHO TRI THUC khong co.
""".strip()

    prompt = f"""
KHO TRI THUC PHONG GYM:
{knowledge}

NHOM KHACH HANG:
{user_type}

DINH HUONG TU VAN THEO NHOM KHACH:
{VALID_USER_TYPES[user_type]}

LICH SU CHAT GAN DAY:
{format_history(history)}

CAU HOI HIEN TAI CUA KHACH:
{message}

Hay tra loi truc tiep cho khach. Neu can hoi them thong tin de tu van dung hon, chi hoi 1-2 cau ngan gon.
""".strip()

    return system_instruction, prompt


def get_local_fallback_response(message: str, user_type: str, history: list) -> str:
    """Sinh cau tra loi cuc bo dua tren thong tin cua user_type va tu khoa trong tin nhan, tranh lap lai."""
    msg = message.lower().strip()
    
    # 1. Tu van HLV
    if any(k in msg for k in ["hlv", "pt", "huan luyen vien", "nguoi day", "co day", "huấn luyện viên"]):
        if user_type == "Giam_Can":
            return (
                "Dành cho mục tiêu Giảm Cân, bạn nên tập cùng HLV Minh Tuấn. "
                "Thế mạnh của HLV Minh Tuấn là giảm cân cấp tốc, cardio chuyên sâu và thiết lập chế độ dinh dưỡng siết mỡ. "
                "Bạn có thể click vào phần đặt lịch để hẹn lịch tập cùng HLV Minh Tuấn nhé!"
            )
        elif user_type == "Tang_Co":
            return (
                "Dành cho mục tiêu Tăng Cơ, bạn nên tập cùng HLV Quốc Hùng. "
                "Thế mạnh của HLV Quốc Hùng là xây dựng cơ bắp (Bodybuilding), tăng sức mạnh thể chất và cử tạ nặng. "
                "Bạn có thể đặt lịch hẹn để tập luyện cùng HLV Quốc Hùng nhé!"
            )
        elif user_type == "Van_Phong":
            return (
                "Dành cho mục tiêu Dân Văn Phòng / Đau Mỏi, bạn nên tập cùng HLV Thùy Linh. "
                "Thế mạnh của HLV Thùy Linh là căng cơ phục hồi, cải thiện tư thế, giảm đau mỏi cơ khớp do ngồi lâu và Pilates nhẹ nhàng."
            )
        else:
            return (
                "Chúng mình có các HLV chuyên nghiệp:\n"
                "1. HLV Minh Tuấn: Giảm cân cấp tốc, cardio chuyên sâu (Phù hợp Giảm Cân).\n"
                "2. HLV Quốc Hùng: Xây dựng cơ bắp, tăng sức mạnh (Phù hợp Tăng Cơ).\n"
                "3. HLV Thùy Linh: Căng cơ phục hồi, cải thiện tư thế, Pilates (Phù hợp Dân Văn Phòng)."
            )

    # 2. Tu van lich tap
    if any(k in msg for k in ["lich", "lich tap", "ke hoach", "chuong trinh", "buoi", "schedule", "lịch"]):
        if user_type == "Giam_Can":
            return (
                "Dưới đây là kế hoạch tập luyện gợi ý 3 buổi/tuần cho mục tiêu Giảm Cân:\n"
                "- Buổi 1: Luyện tập Cardio cường độ cao (HIIT) 45 phút + Chạy bộ dốc.\n"
                "- Buổi 2: Tập Full-body với tạ nhẹ (Số reps cao) để đốt cháy calo.\n"
                "- Buổi 3: Luyện tập các bài nhóm cơ lớn (Chân, Mông) kết hợp đạp xe.\n"
                "Bạn nên duy trì tập đều đặn và kết hợp kiểm soát calo nhé!"
            )
        elif user_type == "Tang_Co":
            return (
                "Dưới đây là kế hoạch tập luyện gợi ý 3 buổi/tuần cho mục tiêu Tăng Cơ:\n"
                "- Buổi 1: Ngực - Tay sau (Đẩy tạ đòn, Tạ đôi cô lập).\n"
                "- Buổi 2: Lưng - Xô - Tay trước (Kéo xà, Pull-down nặng).\n"
                "- Buổi 3: Chân - Đùi - Vai (Squat gánh tạ, Đẩy vai).\n"
                "Lưu ý bổ sung đủ protein và nghỉ ngơi hợp lý để cơ bắp phục hồi nhé!"
            )
        elif user_type == "Van_Phong":
            return (
                "Dưới đây là kế hoạch tập luyện gợi ý 3 buổi/tuần cho mục tiêu Dân Văn Phòng:\n"
                "- Buổi 1: Các bài tập giải mỏi toàn thân, kích hoạt cơ mông và đùi sau.\n"
                "- Buổi 2: Tập trung giải tỏa áp lực vùng Lưng trên và Vai gáy.\n"
                "- Buổi 3: Tập Core (Cơ bụng/lưng) để cải thiện tư thế và Yoga giãn cơ sâu.\n"
                "Hãy cố gắng đứng dậy vận động nhẹ sau mỗi 45-60 phút làm việc nhé!"
            )

    # 3. Hoi ve dinh duong/an uong
    if any(k in msg for k in ["dinh duong", "an uong", "thuc don", "an gi", "uong gi", "protein", "calo", "fat", "carbs", "dinh dưỡng"]):
        if user_type == "Giam_Can":
            return "Để giảm cân bền vững, bạn cần kiểm soát lượng calo nạp vào nhỏ hơn lượng tiêu thụ, bổ sung đủ protein (đạm), hạn chế đường và ngủ đủ giấc."
        elif user_type == "Tang_Co":
            return "Chế độ dinh dưỡng tăng cơ cần đảm bảo dư thừa calo nhẹ, bổ sung đầy đủ protein (1.6 - 2.2g trên mỗi kg thể trọng), tinh bột tốt, chất béo tốt và uống đủ nước."
        else:
            return "Bạn nên ăn uống cân bằng, bổ sung đủ nước, ăn nhiều rau xanh và hạn chế đồ ăn nhanh để cơ thể luôn khỏe mạnh, giảm mệt mỏi nhé."

    # 4. Hoi gia ca/khuyen mai/goi tap
    if any(k in msg for k in ["gia", "goi tap", "uu dai", "khuyen mai", "bao nhieu", "tien", "dang ky", "giá"]):
        return "Hiện tại mình chưa có thông tin chi tiết về giá cả hoặc gói tập cụ thể trong kho tri thức. Bạn vui lòng liên hệ nhân viên tại quầy hoặc qua hotline phòng gym để được tư vấn chính xác nhất nhé!"

    # 5. Hoi suc khoe/chan thuong
    if any(k in msg for k in ["chan thuong", "dau", "benh", "tim mach", "huyet ap", "moi gối", "chấn thương"]):
        return "Nếu bạn có bệnh nền, chấn thương hoặc cảm thấy đau bất thường khi tập, hãy dừng lại ngay và tham khảo ý kiến của bác sĩ hoặc huấn luyện viên chuyên nghiệp để đảm bảo an toàn."

    # 6. Tra loi dong y / khang dinh tu nguoi dung
    if any(k in msg for k in ["co", "có", "ok", "uh", "uha", "yes", "duoc", "được", "xem", "nghe", "gui", "gửi"]):
        if user_type == "Giam_Can":
            return (
                "Dưới đây là gợi ý giảm cân cho bạn:\n\n"
                "**1. Huấn luyện viên:** HLV Minh Tuấn chuyên Giảm cân cấp tốc và dinh dưỡng siết mỡ.\n"
                "**2. Lịch tập gợi ý:**\n"
                "- Buổi 1: Luyện tập Cardio HIIT 45 phút + Chạy bộ dốc.\n"
                "- Buổi 2: Tập Full-body tạ nhẹ đốt mỡ.\n"
                "- Buổi 3: Tập cơ lớn (Chân, Mông) + Đạp xe.\n\n"
                "Bạn cần mình tư vấn thêm gì không?"
            )
        elif user_type == "Tang_Co":
            return (
                "Dưới đây là gợi ý tăng cơ cho bạn:\n\n"
                "**1. Huấn luyện viên:** HLV Quốc Hùng chuyên Bodybuilding và tăng sức mạnh cơ bắp.\n"
                "**2. Lịch tập gợi ý:**\n"
                "- Buổi 1: Ngực - Tay sau.\n"
                "- Buổi 2: Lưng - Xô - Tay trước.\n"
                "- Buổi 3: Chân - Đùi - Vai.\n\n"
                "Bạn cần mình tư vấn thêm gì không?"
            )
        elif user_type == "Van_Phong":
            return (
                "Dưới đây là gợi ý phục hồi cho bạn:\n\n"
                "**1. Huấn luyện viên:** HLV Thùy Linh chuyên cải thiện tư thế, căng cơ giải mỏi.\n"
                "**2. Lịch tập gợi ý:**\n"
                "- Buổi 1: Giải mỏi toàn thân, kích hoạt mông đùi.\n"
                "- Buổi 2: Giải tỏa vùng Lưng trên và Vai gáy.\n"
                "- Buổi 3: Tập Core và Yoga giãn cơ sâu.\n\n"
                "Bạn cần mình tư vấn thêm gì không?"
            )

    # 7. Tu choi, chao tam biet
    if any(k in msg for k in ["cam on", "cảm ơn", "thanks", "thank you", "bye", "tam biet", "tạm biệt"]):
        return "Rất sẵn lòng hỗ trợ bạn! Chúc bạn tập luyện hiệu quả và sớm đạt mục tiêu. Hẹn gặp lại bạn tại phòng gym nhé!"

    # 8. Neu da co hoi thoai truoc do (khong phai turn dau) thi dua ra cau hoi huong dan thay vi lap lai welcome
    if len(history) > 1:
        return "Mình có thể giúp gì thêm cho bạn về lịch tập, huấn luyện viên hoặc chế độ dinh dưỡng không? Bạn hãy gõ câu hỏi hoặc từ khóa cụ thể nhé!"

    # 9. Welcome mac dinh o turn dau
    if user_type == "Giam_Can":
        return (
            "Chào bạn! Mình là trợ lý tư vấn phòng gym. Với mục tiêu Giảm Cân/Giảm Mỡ, "
            "bạn nên kết hợp tập sức mạnh (2-4 buổi/tuần) và cardio (chạy bộ, HIIT, đạp xe). "
            "Bạn có muốn tham khảo lịch tập 3 buổi/tuần hay huấn luyện viên chuyên giảm cân không?"
        )
    elif user_type == "Tang_Co":
        return (
            "Chào bạn! Mình là trợ lý tư vấn phòng gym. Với mục tiêu Tăng Cơ, "
            "bạn nên ưu tiên các bài tập tạ như Squat, Deadlift, Bench Press và tăng tải từ từ. "
            "Bạn có muốn xem lịch tập gợi ý hay tìm hiểu về HLV Quốc Hùng chuyên tăng cơ không?"
        )
    else:
        return (
            "Chào bạn! Mình là trợ lý tư vấn phòng gym. Với nhóm Dân Văn Phòng, "
            "chúng ta nên tập trung vào các bài tập cải thiện tư thế, cơ core, giãn cơ cổ vai gáy. "
            "Bạn có muốn tham khảo lịch tập giãn cơ hay HLV Thùy Linh chuyên phục hồi không?"
        )


class ChatbotAPIView(BaseAPIView):
    """API POST /api/chat/ de frontend gui cau hoi va nhan cau tra loi tu Gemini."""

    permission_classes = [AllowAny]

    def post(self, request):
        message = str(request.data.get("message", "")).strip()
        user_type = str(request.data.get("user_type", "")).strip()
        history = request.data.get("history", [])

        if not message:
            return self.handle_result(Result.failure_result("message khong duoc de trong", status_code=400))

        if user_type not in VALID_USER_TYPES:
            return self.handle_result(Result.failure_result("user_type khong hop le. Gia tri hop le: Giam_Can, Tang_Co, Van_Phong", status_code=400))

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: Server thieu GEMINI_API_KEY. Chuyen sang che do Local Fallback.")
            reply = get_local_fallback_response(message, user_type, history)
            return self.handle_result(Result.success_result({"reply": reply, "fallback": True}, status_code=200))

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            print("WARNING: google-genai chua duoc cai. Chuyen sang che do Local Fallback.")
            reply = get_local_fallback_response(message, user_type, history)
            return self.handle_result(Result.success_result({"reply": reply, "fallback": True}, status_code=200))

        try:
            knowledge = load_knowledge()
        except RuntimeError as exc:
            return self.handle_result(Result.failure_result(str(exc), status_code=500))

        system_instruction, prompt = build_prompt(message, user_type, history, knowledge)

        try:
            client = genai.Client(api_key=api_key)
            gemini_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    system_instruction=system_instruction,
                ),
            )
            reply = (gemini_response.text or "").strip()
            if not reply:
                raise ValueError("Gemini API khong tra ve noi dung phu hop.")
        except Exception as exc:
            print("--- LOG CHATBOT GEMINI ERROR ---")
            traceback.print_exc()
            print("--------------------------------")
            print("Chuyen sang che do Local Fallback do loi Gemini API.")
            reply = get_local_fallback_response(message, user_type, history)

        return self.handle_result(Result.success_result({"reply": reply}, status_code=200))
