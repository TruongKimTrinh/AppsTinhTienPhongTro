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
    page_title="BDUHome | Tính tiền phòng trọ",
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
            electric_end = st.number_input("Chỉ số điện cuối kỳ (kWh)", min_value=0, value=1320, step=1)
        with e3:
            electric_rate = st.number_input("Đơn giá điện (đ/kWh)", min_value=0, value=3500, step=100)

        st.markdown("### 3. Tiền nước")
        water_method = st.radio("Cách tính tiền nước", ["Theo số m³", "Theo đầu người"], horizontal=True)
        w1, w2, w3 = st.columns(3)
        with w1:
            if water_method == "Theo số m³":
                water_start = st.number_input("Chỉ số nước đầu kỳ (m³)", min_value=0.0, value=80.0, step=1.0)
                water_end = st.number_input("Chỉ số nước cuối kỳ (m³)", min_value=0.0, value=86.0, step=1.0)
            else:
                water_start = 0.0
                water_end = 0.0
                water_per_person = st.number_input("Tiền nước / người (đ)", min_value=0, value=50000, step=10000)
        with w2:
            water_rate = st.number_input("Đơn giá nước (đ/m³)", min_value=0, value=15000, step=1000)
        with w3:
            other_fee = st.number_input("Chi phí khác (đ)", min_value=0, value=0, step=10000)
        other_note = st.text_input("Ghi chú chi phí khác (nếu có)", "Ví dụ: gửi xe")

        submitted = st.form_submit_button("✨ TÍNH HÓA ĐƠN", type="primary", use_container_width=True)

    if submitted:
        if electric_end < electric_start:
            st.error("Chỉ số điện cuối kỳ không được nhỏ hơn chỉ số đầu kỳ.")
        elif water_method == "Theo số m³" and water_end < water_start:
            st.error("Chỉ số nước cuối kỳ không được nhỏ hơn chỉ số đầu kỳ.")
        else:
            electric_usage = electric_end - electric_start
            electric_cost = electric_usage * electric_rate
            if water_method == "Theo số m³":
                water_usage = water_end - water_start
                water_cost = water_usage * water_rate
                water_detail = f"{water_usage:g} m³ × {vnd(water_rate)}"
            else:
                water_usage = None
                water_cost = water_per_person * tenant_count
                water_detail = f"{tenant_count} người × {vnd(water_per_person)}"
            total = rent + service_fee + wifi_fee + electric_cost + water_cost + other_fee
            per_person = total / tenant_count
            rows = [
                ["Tiền thuê phòng", 1, rent, rent],
                ["Tiền điện", f"{electric_usage} kWh × {vnd(electric_rate)}", electric_usage, electric_cost],
                ["Tiền nước", water_detail, tenant_count if water_method == "Theo đầu người" else water_usage, water_cost],
                ["Wi-Fi", "Cả phòng", 1, wifi_fee],
                ["Phí dịch vụ / vệ sinh", "Cả phòng", 1, service_fee],
                [other_note or "Chi phí khác", "Cả phòng", 1, other_fee],
            ]
            df = pd.DataFrame(rows, columns=["Khoản thu", "Cách tính", "Số lượng", "Thành tiền (đ)"])
            st.session_state.invoice = {
                "room_name": room_name,
                "bill_month": bill_month,
                "tenant_count": tenant_count,
                "total": total,
                "per_person": per_person,
                "electric_usage": electric_usage,
                "electric_cost": electric_cost,
                "water_cost": water_cost,
                "df": df,
                "water_method": water_method,
            }

    if st.session_state.invoice:
        inv = st.session_state.invoice
        st.success(f"Đã tính hóa đơn cho {inv['room_name']} – kỳ {inv['bill_month']}.")
        m1, m2, m3 = st.columns(3)
        with m1:
            metric_card("Tổng hóa đơn", vnd(inv["total"]), "💰")
        with m2:
            metric_card("Mỗi người đóng", vnd(inv["per_person"]), "👥")
        with m3:
            metric_card("Điện đã dùng", f"{inv['electric_usage']} kWh", "⚡")
        st.markdown("### 📄 Chi tiết hóa đơn")
        st.dataframe(inv["df"], use_container_width=True, hide_index=True)
        st.markdown(f"**Tổng cộng: {vnd(inv['total'])}**")
        st.markdown(f"**Số tiền mỗi người: {vnd(inv['per_person'])}**")
        csv_data = inv["df"].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Tải bảng kê hóa đơn (CSV/Excel)",
            data=csv_data,
            file_name=f"hoa_don_{inv['room_name'].replace(' ', '_')}_{inv['bill_month'].replace('/', '-')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Lưu ý: ứng dụng chia tổng tiền đều theo số người; hãy điều chỉnh nếu có thỏa thuận chia phí khác.")
        st.markdown("### 📊 Cơ cấu chi phí")
        chart_df = inv["df"][["Khoản thu", "Thành tiền (đ)"]].copy()
        chart_df = chart_df[chart_df["Thành tiền (đ)"] > 0].set_index("Khoản thu")
        if not chart_df.empty:
            st.bar_chart(chart_df)
        st.session_state["invoice_context"] = (
            f"Phòng {inv['room_name']}, tháng {inv['bill_month']}, "
            f"tổng {vnd(inv['total'])}, {inv['tenant_count']} người, "
            f"mỗi người {vnd(inv['per_person'])}, tiền điện {vnd(inv['electric_cost'])}, "
            f"tiền nước {vnd(inv['water_cost'])}."
        )

# -------------------- CHATBOX --------------------
elif page == "💬 Chatbox trợ lý AI":
    st.markdown("## 💬 Chat với RoomMate Assistant")
    st.markdown(
        '<div class="info-box">Hỏi về cách tính hóa đơn, tiền điện nước, cách chia chi phí hoặc mẹo tiết kiệm. Không gửi mật khẩu, OTP hay thông tin ngân hàng.</div>',
        unsafe_allow_html=True,
    )
    st.image(
        "https://images.unsplash.com/photo-1531746795393-6c9f2b823b91?auto=format&fit=crop&w=1400&q=80",
        caption="Trợ lý hỗ trợ giải đáp câu hỏi về chi phí phòng trọ",
        use_container_width=True,
    )
    st.markdown("**Câu hỏi gợi ý:**")
    suggestions = st.columns(4)
    prompts = [
        "Cách tính tiền điện như thế nào?",
        "Làm sao tiết kiệm điện nước?",
        "Chia tiền phòng cho 3 người thế nào?",
        "Tiền nước tính theo m³ là sao?",
    ]
    for col, prompt in zip(suggestions, prompts):
        with col:
            if st.button(prompt, use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                context = st.session_state.get("invoice_context", "Chưa có hóa đơn nào được tính.")
                answer = ai_reply(prompt, context)
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                st.rerun()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Nhập câu hỏi của bạn...")
    if user_prompt:
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        context = st.session_state.get("invoice_context", "Chưa có hóa đơn nào được tính.")
        answer = ai_reply(user_prompt, context)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.button("🧹 Xóa cuộc trò chuyện"):
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Xin chào! 🏠 Mình là RoomMate Assistant. Bạn muốn hỏi gì về hóa đơn phòng trọ?"}
        ]
        st.rerun()

# -------------------- BÁO CÁO --------------------
elif page == "📊 Báo cáo & hóa đơn":
    st.markdown("## 📊 Báo cáo & hóa đơn")
    inv = st.session_state.invoice
    if not inv:
        st.info("Bé chưa có hóa đơn nào trong phiên này. Vào mục **Tính tiền phòng** để nhập dữ liệu trước nhé.")
        st.image(
            "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            use_container_width=True,
        )
    else:
        st.markdown(f"### Hóa đơn {inv['room_name']} – {inv['bill_month']}")
        a, b = st.columns(2)
        with a:
            metric_card("Tổng cần thanh toán", vnd(inv["total"]), "💵")
        with b:
            metric_card("Bình quân mỗi người", vnd(inv["per_person"]), "🧑‍🤝‍🧑")
        st.dataframe(inv["df"], use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Tải hóa đơn CSV",
            data=inv["df"].to_csv(index=False).encode("utf-8-sig"),
            file_name="hoa_don_phong_tro.csv",
            mime="text/csv",
        )
        st.caption("Bản mẫu học tập: lịch sử chỉ giữ trong phiên chạy hiện tại, chưa lưu vào cơ sở dữ liệu lâu dài.")

# -------------------- HƯỚNG DẪN --------------------
elif page == "ℹ️ Hướng dẫn":
    st.markdown("## ℹ️ Hướng dẫn sử dụng")
    st.markdown(
        """
        ### Cách chạy ứng dụng
        1. Cài Python trên máy tính.
        2. Mở Terminal / Command Prompt tại thư mục có file `app.py`.
        3. Cài thư viện: `pip install streamlit pandas openai`
        4. Chạy ứng dụng: `streamlit run app.py`
        5. Trình duyệt sẽ mở ứng dụng RoomMate.

        ### Bật chatbot AI trực tuyến
        - Tạo API key từ nhà cung cấp AI mà bạn có quyền sử dụng.
        - Đặt key trong biến môi trường `OPENAI_API_KEY`; không dán key công khai vào mã nguồn hoặc GitHub.
        - Có thể đặt `OPENAI_MODEL` nếu muốn đổi model tương thích.
        - Nếu chưa có API key, chatbot vẫn trả lời các câu hỏi thường gặp bằng chế độ dự phòng.

        ### Công thức tính
        - **Tiền điện** = (chỉ số điện cuối kỳ − chỉ số đầu kỳ) × đơn giá điện.
        - **Tiền nước theo m³** = (chỉ số nước cuối kỳ − chỉ số đầu kỳ) × đơn giá nước.
        - **Tiền nước theo đầu người** = số người × mức phí nước mỗi người.
        - **Tổng hóa đơn** = tiền phòng + điện + nước + Wi-Fi + phí dịch vụ + chi phí khác.
        - **Mỗi người đóng** = tổng hóa đơn ÷ số người ở.

        ### Lưu ý
        - Đơn giá mẫu không phải mức giá bắt buộc hay mức giá chính thức.
        - Cần thống nhất đơn giá và cách chia phí với chủ trọ.
        - Phiên bản này chưa có đăng nhập, cơ sở dữ liệu, thanh toán trực tuyến hoặc lưu lịch sử lâu dài.
        """
    )
    st.markdown(
        '<div class="info-box">Bảo mật: không đưa API key, mật khẩu, mã OTP hoặc dữ liệu thanh toán cá nhân vào mã nguồn công khai.</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#71839a;font-size:.82rem;'>RoomMate • Bản mẫu học tập Công nghệ tài chính • Made with Streamlit 🩵</p>",
    unsafe_allow_html=True,
)

