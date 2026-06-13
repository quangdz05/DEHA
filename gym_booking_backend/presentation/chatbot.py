import os
from functools import lru_cache
from pathlib import Path

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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


class ChatbotAPIView(APIView):
    """API POST /api/chat/ de frontend gui cau hoi va nhan cau tra loi tu Gemini."""

    permission_classes = [AllowAny]

    def post(self, request):
        message = str(request.data.get("message", "")).strip()
        user_type = str(request.data.get("user_type", "")).strip()
        history = request.data.get("history", [])

        if not message:
            return Response(
                {"detail": "message khong duoc de trong"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_type not in VALID_USER_TYPES:
            return Response(
                {"detail": "user_type khong hop le. Gia tri hop le: Giam_Can, Tang_Co, Van_Phong"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return Response(
                {"detail": "Server thieu GEMINI_API_KEY. Hay tao file .env trong gym_booking_backend."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return Response(
                {"detail": "Server chua cai google-genai. Hay chay: pip install google-genai python-dotenv"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            knowledge = load_knowledge()
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        except Exception:
            return Response(
                {"detail": "Khong goi duoc Gemini API. Vui long thu lai sau."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        reply = (gemini_response.text or "").strip()
        if not reply:
            return Response(
                {"detail": "Gemini API khong tra ve noi dung phu hop."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"reply": reply})
