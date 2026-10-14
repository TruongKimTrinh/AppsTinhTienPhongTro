import os
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================
# KIMCHIN ROOMMATE - ỨNG DỤNG TÍNH TIỀN PHÒNG TRỌ THÔNG MINH
# Chạy: streamlit run app.py
# Chat AI thật: cài openai và đặt biến môi trường OPENAI_API_KEY.
# ============================================================

st.set_page_config(
    page_title="RoomMate | Tính tiền phòng trọ",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- GIAO DIỆN --------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
    .stApp { background: #f5f9ff; }
    [data-testid="stSidebar"] { background: #eaf3ff; }
    .hero {
        background: linear-gradient(120deg, #0f5bd7 0%, #49a3ff 100%);
        color: white; padding: 28px 30px; border-radius: 22px;
        margin-bottom: 18px; box-shadow: 0 8px 24px rgba(22, 91, 190, .14);
    }
    .hero h1 { font-size: 2.05rem; margin: 0 0 8px 0; color: white; }
    .hero p { font-size: 1rem; margin: 0; color: #eef6ff; }
    .metric-card {
        background: white; border: 1px solid #e0ebfa; padding: 18px;
        border-radius: 16px; box-shadow: 0 4px 16px rgba(32, 87, 150, .05);
        min-height: 110px;
    }
    .metric-label { color: #60748d; font-size: .9rem; margin-bottom: 8px; }
    .metric-value { color: #104da8; font-size: 1.45rem; font-weight: 800; }
    .section-title { color: #123f7a; font-size: 1.25rem; font-weight: 800; margin: 10px 0 14px; }
    .info-box {
        padding: 14px 16px; background: #e8f3ff; border-left: 4px solid #2684ff;
        border-radius: 10px; color: #24466d; margin: 8px 0 14px;
    }
    .small-note { color: #6b7d93; font-size: .83rem; }
    div[data-testid="stChatMessage"] { border-radius: 14px; }
    .stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

def vnd(value):
    """Định dạng số tiền Việt Nam."""
    return f"{value:,.0f} đ".replace(",", ".")

def metric_card(label, value, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def default_reply(question, context):
    """Trợ lý dự phòng khi chưa cấu hình API AI."""
    q = question.lower()
    if any(word in q for word in ["điện", "kwh"]):
        return (
            "Tiền điện được tính bằng: số kWh sử dụng × đơn giá điện. "
            "Ví dụ dùng 120 kWh, đơn giá 3.500 đ/kWh thì tiền điện là 420.000 đ. "
          "Hãy nhập chỉ số điện đầu kỳ và cuối kỳ để ứng dụng tính tự động."
        )
    if "nước" in q:
        return (
            "Tiền nước có thể tính theo số m³ sử dụng hoặc theo đầu người, tùy thỏa thuận "
            "với chủ trọ. Ứng dụng này cho phép chọn một trong hai cách tính."
        )
    if any(word in q for word in ["chia", "mỗi người", "người ở"]):
        return (
            "Ứng dụng chia tổng hóa đơn cho số người ở. Nếu các bạn có thỏa thuận chia "
            "tiền phòng hoặc phí riêng theo tỷ lệ khác nhau, cần điều chỉnh cách phân bổ "
            "trước khi thanh toán."
        )
    if any(word in q for word in ["tiết kiệm", "giảm tiền", "tiết kiệm điện"]):
        return (
            "Mẹo tiết kiệm: tắt thiết bị khi không dùng, đặt điều hòa khoảng 26–28°C, "
            "dùng đèn LED, kiểm tra rò rỉ nước và thống nhất ngày chốt chỉ số điện nước "
            "mỗi tháng."
        )
    if any(word in q for word in ["xin chào", "hello", "chào"]):
        return "Xin chào! Mình là RoomMate Assistant 🏠. Bạn cần hỗ trợ tính tiền phòng, điện, nước hay chia hóa đơn?"
    return (
        "Mình có thể giải thích cách tính tiền phòng, điện, nước, Wi-Fi, chia hóa đơn "
        "và gợi ý tiết kiệm chi phí. Bạn hãy hỏi cụ thể hơn nhé! "
        "Lưu ý: đây là trợ lý minh họa; chưa kết nối AI trực tuyến nếu chưa cài API key."
    )

def ai_reply(question, context):
    """Dùng OpenAI API nếu có OPENAI_API_KEY; nếu không thì dùng câu trả lời dự phòng."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return default_reply(question, context)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là RoomMate Assistant, trợ lý tiếng Việt cho ứng dụng tính tiền phòng trọ. "
                        "Trả lời thân thiện, ngắn gọn, dễ hiểu; giải thích phép tính rõ ràng. "
                        "Không tự nhận là ngân hàng hay đơn vị thu tiền. Không yêu cầu mật khẩu, OTP, "
                        "số thẻ hoặc dữ liệu cá nhân nhạy cảm. Dữ liệu hóa đơn hiện tại: " + context
                    ),
                },
                {"role": "user", "content": question},
            ],
            temperature=0.5,
        )
      return response.choices[0].message.content or "Mình chưa tạo được câu trả lời, bạn thử lại nhé."
    except Exception as exc:
        return (
            "Chưa gọi được dịch vụ AI. Bé kiểm tra API key, kết nối mạng và gói thư viện nhé. "
            f"Chi tiết kỹ thuật: {str(exc)[:180]}"
        )

# -------------------- THANH BÊN --------------------
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
        use_container_width=True,
    )
    st.markdown("## 🏠 RoomMate")
    st.caption("Trợ lý quản lý chi phí phòng trọ")
    page = st.radio(
        "Điều hướng",
        ["🏡 Tổng quan", "🧮 Tính tiền phòng", "💬 Chatbox trợ lý AI", "📊 Báo cáo & hóa đơn", "ℹ️ Hướng dẫn"],
        key="navigation",
    )
    st.divider()
    st.caption("Phiên bản học tập • Dữ liệu được lưu trong phiên trình duyệt hiện tại.")

# -------------------- KHỞI TẠO TRẠNG THÁI --------------------
if "invoice" not in st.session_state:
    st.session_state.invoice = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Xin chào! 🏠 Mình là RoomMate Assistant. Bạn muốn hỏi gì về hóa đơn phòng trọ?"}
    ]

# -------------------- TỔNG QUAN --------------------
if page == "🏡 Tổng quan":
    st.markdown(
        """
        <div class="hero">
            <h1>🏠 RoomMate – Tính tiền phòng trọ thông minh</h1>
            <p>Tính tiền phòng, điện, nước, Wi-Fi và chia hóa đơn minh bạch chỉ trong vài bước.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### ✨ Quản lý chi phí dễ dàng")
        st.write(
            "RoomMate giúp người thuê trọ tổng hợp các khoản phí hàng tháng, "
            "ước tính số tiền mỗi người cần đóng và xuất bảng kê để đối chiếu."
        )
        st.markdown(
            """
            - 🧮 Tự động tính tiền điện theo chỉ số công tơ.
            - 💧 Tính tiền nước theo m³ hoặc theo đầu người.
            - 👥 Chia tổng hóa đơn theo số người ở.
            - 📄 Xuất bảng kê CSV để mở bằng Excel.
            - 🤖 Chatbox giải đáp câu hỏi thường gặp.
            """
        )
        if st.button("Bắt đầu tính hóa đơn", type="primary", use_container_width=True):
            st.session_state["navigation"] = "🧮 Tính tiền phòng"
            st.rerun()
    with right:
        st.image(
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=85",
          caption="Không gian sống gọn gàng, quản lý chi phí rõ ràng",
            use_container_width=True,
        )
    st.markdown("### 🧭 Quy trình sử dụng")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Bước 1", "Nhập chỉ số", "📝")
        st.caption("Điền tiền thuê và chỉ số điện nước.")
    with c2:
        metric_card("Bước 2", "Tính hóa đơn", "🧮")
        st.caption("Ứng dụng tự cộng các khoản phí.")
    with c3:
        metric_card("Bước 3", "Xuất bảng kê", "📄")
        st.caption("Tải CSV hoặc xem lại kết quả.")

# -------------------- TÍNH TIỀN --------------------
elif page == "🧮 Tính tiền phòng":
    st.markdown("## 🧮 Tính tiền phòng trọ")
    st.markdown(
        '<div class="info-box">Nhập số liệu theo thỏa thuận thực tế với chủ trọ. Đơn giá mặc định chỉ là ví dụ và có thể sửa lại.</div>',
        unsafe_allow_html=True,
    )
    with st.form("bill_form"):
        st.markdown("### 1. Thông tin chung")
        a, b, c = st.columns(3)
        with a:
            room_name = st.text_input("Tên phòng / địa chỉ ngắn", "Phòng 203")
            tenant_count = st.number_input("Số người ở", min_value=1, max_value=20, value=2, step=1)
        with b:
            bill_month = st.selectbox(
                "Tháng hóa đơn",
                [f"{m:02d}/{y}" for y in [datetime.now().year, datetime.now().year - 1] for m in range(1, 13)],
                index=datetime.now().month - 1,
            )
            rent = st.number_input("Tiền thuê phòng (đ)", min_value=0, value=2500000, step=100000)
        with c:
            service_fee = st.number_input("Phí dịch vụ / vệ sinh (đ)", min_value=0, value=50000, step=10000)
            wifi_fee = st.number_input("Tiền Wi-Fi cả phòng (đ)", min_value=0, value=100000, step=10000)

        st.markdown("### 2. Tiền điện")
        e1, e2, e3 = st.columns(3)
        with e1:
            electric_start = st.number_input("Chỉ số điện đầu kỳ (kWh)", min_value=0, value=1200, step=1)
        with e2:
            electric_end = st.number_input("Chỉ số điện cuối kỳ (kWh)", min_value=0,
