 

import os 

import json 

import urllib.request 

import urllib.error 

from datetime import date, datetime 

 

import streamlit as st 

 

# ========================================== 

# BDUHome - Quan ly phong tro 

# ========================================== 

st.set_page_config( 

    page_title="BDUHome", 

    page_icon="🏠", 

    layout="wide", 

    initial_sidebar_state="expanded", 

) 

 

# ---------- GIAO DIEN ---------- 

st.markdown(""" 

<style> 

.stApp { 

    background-color: #f3f8ff; 

} 

[data-testid="stSidebar"] { 

    background-color: #e5f1ff; 

} 

.main-header { 

    background: linear-gradient(120deg, #0757a6, #43a5ef); 

    color: white; 

    padding: 25px; 

    border-radius: 18px; 

    margin-bottom: 20px; 

} 

.main-header h1 { 

    margin: 0; 

    font-size: 34px; 

} 

.main-header p { 

    margin: 8px 0 0 0; 

} 

div.stButton > button { 

    border-radius: 10px; 

} 

div[data-testid="stMetric"] { 

    background: white; 

    border: 1px solid #d7e7f8; 

    border-radius: 12px; 

    padding: 12px; 

} 

</style> 

""", unsafe_allow_html=True) 

 

 

# ---------- DU LIEU PHIEN ---------- 

if "bdu_bills" not in st.session_state: 

    st.session_state.bdu_bills = [] 

 

if "bdu_chat" not in st.session_state: 

    st.session_state.bdu_chat = [ 

        { 

            "role": "assistant", 

            "content": ( 

                "Xin chào! Mình là trợ lý AI BDUHome 🏠. " 

                "Bạn cần giúp tính tiền phòng, điện, nước " 

                "hay tìm hiểu cách sử dụng ứng dụng?" 

            ), 

        } 

    ] 

 

 

# ---------- HAM HO TRO ---------- 

def money(value): 

    return f"{value:,.0f}".replace(",", ".") + " VNĐ" 

 

 

def get_api_key(): 

    """Lay API key tu Streamlit Secrets hoac bien moi truong.""" 

    try: 

        key = st.secrets.get("OPENAI_API_KEY", "") 

        if key: 

            return str(key).strip() 

    except Exception: 

        pass 

 

    return os.environ.get("OPENAI_API_KEY", "").strip() 

 

 

def ask_ai(question): 

    """Gui cau hoi den OpenAI API.""" 

    api_key = get_api_key() 

 

    if not api_key: 

        return ( 

            "Chưa cấu hình API key nên mình chưa thể kết nối AI. " 

            "Bạn hãy thêm OPENAI_API_KEY trong mục Secrets " 

            "của Streamlit Cloud rồi thử lại nhé." 

        ) 

 

    messages = [ 

        { 

            "role": "system", 

            "content": ( 

                "Bạn là trợ lý AI của BDUHome, ứng dụng quản lý " 

                "phòng trọ tại Việt Nam. Hãy trả lời bằng tiếng Việt, " 

                "thân thiện, rõ ràng và dễ hiểu. Hỗ trợ người dùng " 

                "về tiền phòng, tiền điện, nước, Wi-Fi, hóa đơn và " 

                "cách sử dụng ứng dụng. Nếu cần tính toán, hãy trình " 

                "bày công thức và kết quả. Không tuyên bố đã lưu hoặc " 

                "thay đổi dữ liệu khi chưa thực hiện." 

            ), 

        } 

    ] 

 

    # Chi gui mot so tin nhan gan nhat de han che token 

    for message in st.session_state.bdu_chat[-10:]: 

        if message["role"] in ("user", "assistant"): 

            messages.append({ 

                "role": message["role"], 

                "content": message["content"], 

            }) 

 

    messages.append({"role": "user", "content": question}) 

 

    payload = { 

        "model": "gpt-4o-mini", 

        "messages": messages, 

        "temperature": 0.5, 

    } 

 

    request = urllib.request.Request( 

        "https://api.openai.com/v1/chat/completions", 

        data=json.dumps(payload).encode("utf-8"), 

        headers={ 

            "Authorization": f"Bearer {api_key}", 

            "Content-Type": "application/json", 

        }, 

        method="POST", 

    ) 

 

    try: 

        with urllib.request.urlopen(request, timeout=45) as response: 

            result = json.loads(response.read().decode("utf-8")) 

 

        return result["choices"][0]["message"]["content"].strip() 

 

    except urllib.error.HTTPError as error: 

        if error.code == 401: 

            return "API key không hợp lệ. Bạn hãy kiểm tra lại Secrets." 

        if error.code == 429: 

            return ( 

                "API đang giới hạn yêu cầu hoặc tài khoản hết hạn mức. " 

                "Bạn hãy kiểm tra billing và usage của tài khoản API." 

            ) 

        return f"OpenAI API trả về lỗi HTTP {error.code}. Bạn thử lại sau nhé." 

 

    except Exception: 

        return ( 

            "Chưa kết nối được AI. Bạn hãy kiểm tra Internet, " 

            "API key và thử lại." 

        ) 

 

 

# ---------- MENU ---------- 

with st.sidebar: 

    st.markdown("## 🏠 BDUHome") 

    st.caption("Quản lý phòng trọ thông minh") 

    st.divider() 

 

    page = st.radio( 

        "MENU CHÍNH", 

        [ 

            "Tổng quan", 

            "Tính hóa đơn", 

            "Lịch sử hóa đơn", 

            "Chatbox AI", 

        ], 

    ) 

 

    st.divider() 

    st.caption("Phiên bản 1.0") 

    st.caption("Giao diện xanh dương - trắng") 

 

 

# ---------- TIEU DE ---------- 

st.markdown(""" 

<div class="main-header"> 

    <h1>🏠 BDUHome</h1> 

    <p>Quản lý phòng trọ • Tính hóa đơn • Trợ lý AI</p> 

</div> 

""", unsafe_allow_html=True) 

 

 

# ========================================== 

# 1. TONG QUAN 

# ========================================== 

if page == "Tổng quan": 

    st.subheader("Xin chào! Chào mừng đến với BDUHome 👋") 

 

    total_bills = len(st.session_state.bdu_bills) 

    total_amount = sum( 

        bill["total"] for bill in st.session_state.bdu_bills 

    ) 

 

    col1, col2, col3 = st.columns(3) 

 

    col1.metric("🧾 Số hóa đơn", total_bills) 

    col2.metric("💰 Tổng hóa đơn đã tính", money(total_amount)) 

    col3.metric("📅 Ngày hôm nay", date.today().strftime("%d/%m/%Y")) 

 

    st.divider() 

 

    left, right = st.columns([1.2, 1]) 

 

    with left: 

        st.markdown("### Quản lý phòng trọ dễ dàng") 

        st.write( 

            "BDUHome hỗ trợ tính tiền phòng, điện, nước, " 

            "Wi-Fi và các khoản phí khác trong cùng một hóa đơn." 

        ) 

        st.info( 

            "Chọn **Tính hóa đơn** ở menu bên trái để bắt đầu." 

        ) 

 

        st.markdown("#### ✨ Chức năng chính") 

        st.write("🧮 Tự động tính tổng tiền phải trả.") 

        st.write("🧾 Xem lại lịch sử hóa đơn trong phiên.") 

        st.write("🤖 Chat với trợ lý AI bằng tiếng Việt.") 

 

    with right: 

        st.image( 

            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267" 

            "?auto=format&fit=crop&w=1000&q=80", 

            caption="Không gian sống tiện nghi", 

            use_container_width=True, 

        ) 

 

 

# ========================================== 

# 2. TINH HOA DON 

# ========================================== 

elif page == "Tính hóa đơn": 

    st.subheader("🧾 Tính hóa đơn phòng trọ") 

    st.caption("Nhập số liệu thực tế của phòng trong tháng.") 

 

    with st.form("bdu_invoice_form"): 

        col1, col2 = st.columns(2) 

 

        with col1: 

            tenant = st.text_input( 

                "Tên người thuê *", 

                placeholder="Nguyễn Văn A", 

            ) 

            room = st.text_input( 

                "Mã hoặc tên phòng *", 

                placeholder="Phòng 101", 

            ) 

            bill_month = st.selectbox( 

                "Tháng hóa đơn", 

                [ 

                    f"{m:02d}/{y}" 

                    for y in (date.today().year, 

                              date.today().year - 1) 

                    for m in range(1, 13) 

                ], 

                index=date.today().month - 1, 

            ) 

            rent = st.number_input( 

                "Tiền phòng (VNĐ)", 

                min_value=0, 

                value=2500000, 

                step=100000, 

            ) 

 

        with col2: 

            electricity_used = st.number_input( 

                "Điện sử dụng (kWh)", 

                min_value=0.0, 

                value=100.0, 

                step=1.0, 

            ) 

            electricity_rate = st.number_input( 

                "Đơn giá điện (VNĐ/kWh)", 

                min_value=0, 

                value=3500, 

                step=100, 

            ) 

            water_used = st.number_input( 

                "Nước sử dụng (m³)", 

                min_value=0.0, 

                value=4.0, 

                step=1.0, 

            ) 

            water_rate = st.number_input( 

                "Đơn giá nước (VNĐ/m³)", 

                min_value=0, 

                value=15000, 

                step=1000, 

            ) 

 

        col3, col4 = st.columns(2) 

 

        with col3: 

            wifi = st.number_input( 

                "Phí Wi-Fi (VNĐ)", 

                min_value=0, 

                value=50000, 

                step=10000, 

            ) 

            service = st.number_input( 

                "Phí dịch vụ / vệ sinh (VNĐ)", 

                min_value=0, 

                value=30000, 

                step=10000, 

            ) 

 

        with col4: 

            other = st.number_input( 

                "Chi phí phát sinh (VNĐ)", 

                min_value=0, 

                value=0, 

                step=10000, 

            ) 

            note = st.text_input("Ghi chú") 

 

        submitted = st.form_submit_button( 

            "🧮 Tính và lưu hóa đơn", 

            use_container_width=True, 

        ) 

 

    if submitted: 

        if not tenant.strip() or not room.strip(): 

            st.error("Vui lòng nhập tên người thuê và tên phòng.") 

        else: 

            electric_cost = round(electricity_used * electricity_rate) 

            water_cost = round(water_used * water_rate) 

 

            total = int( 

                rent + electric_cost + water_cost 

                + wifi + service + other 

            ) 

 

            bill = { 

                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"), 

                "month": bill_month, 

                "tenant": tenant.strip(), 

                "room": room.strip(), 

                "rent": int(rent), 

                "electricity_used": electricity_used, 

                "electricity_rate": int(electricity_rate), 

                "electric_cost": electric_cost, 

                "water_used": water_used, 

                "water_rate": int(water_rate), 

                "water_cost": water_cost, 

                "wifi": int(wifi), 

                "service": int(service), 

                "other": int(other), 

                "total": total, 

                "note": note.strip(), 

            } 

 

            st.session_state.bdu_bills.insert(0, bill) 

            st.session_state.latest_bdu_bill = bill 

            st.success("Đã tính và lưu hóa đơn trong phiên hiện tại!") 

 

    if "latest_bdu_bill" in st.session_state: 

        bill = st.session_state.latest_bdu_bill 

 

        st.divider() 

        st.markdown("### 📄 Chi tiết hóa đơn") 

        st.write(f"**Người thuê:** {bill['tenant']}") 

        st.write(f"**Phòng:** {bill['room']}") 

        st.write(f"**Tháng:** {bill['month']}") 

 

        rows = [ 

            ("Tiền phòng", bill["rent"]), 

            ("Tiền điện", bill["electric_cost"]), 

            ("Tiền nước", bill["water_cost"]), 

            ("Wi-Fi", bill["wifi"]), 

            ("Phí dịch vụ", bill["service"]), 

            ("Phát sinh", bill["other"]), 

        ] 

 

        for label, amount in rows: 

            left, right = st.columns([3, 1]) 

            left.write(label) 

            right.write(money(amount)) 

 

        st.success(f"TỔNG CỘNG: {money(bill['total'])}") 

 

        if bill["note"]: 

            st.caption(f"Ghi chú: {bill['note']}") 

 

        receipt = ( 

            "BDUHome - HOA DON PHONG TRO\n" 

            f"Thang: {bill['month']}\n" 

            f"Nguoi thue: {bill['tenant']}\n" 

            f"Phong: {bill['room']}\n" 

            f"Tien phong: {money(bill['rent'])}\n" 

            f"Tien dien: {money(bill['electric_cost'])}\n" 

            f"Tien nuoc: {money(bill['water_cost'])}\n" 

            f"Wi-Fi: {money(bill['wifi'])}\n" 

            f"Phi dich vu: {money(bill['service'])}\n" 

            f"Phat sinh: {money(bill['other'])}\n" 

            f"TONG CONG: {money(bill['total'])}\n" 

            f"Ghi chu: {bill['note']}\n" 

        ) 

 

        st.download_button( 

            "⬇️ Tải hóa đơn dạng TXT", 

            data=receipt.encode("utf-8"), 

            file_name=( 

                f"BDUHome_{bill['room'].replace(' ', '_')}_" 

                f"{bill['month'].replace('/', '-')}.txt" 

            ), 

            mime="text/plain", 

        ) 

 

 

# ========================================== 

# 3. LICH SU HOA DON 

# ========================================== 

elif page == "Lịch sử hóa đơn": 

    st.subheader("📚 Lịch sử hóa đơn") 

 

    bills = st.session_state.bdu_bills 

 

    if not bills: 

        st.info( 

            "Chưa có hóa đơn. Hãy vào mục Tính hóa đơn " 

            "để tạo hóa đơn đầu tiên." 

        ) 

    else: 

        st.write(f"Số hóa đơn trong phiên: **{len(bills)}**") 

 

        for bill in bills: 

            with st.expander( 

                f"{bill['month']} | {bill['room']} | " 

                f"{bill['tenant']} | {money(bill['total'])}" 

            ): 

                st.write(f"Ngày tạo: {bill['created_at']}") 

                st.write(f"Tiền phòng: {money(bill['rent'])}") 

                st.write(f"Tiền điện: {money(bill['electric_cost'])}") 

                st.write(f"Tiền nước: {money(bill['water_cost'])}") 

                st.write(f"Wi-Fi: {money(bill['wifi'])}") 

                st.write(f"Phí dịch vụ: {money(bill['service'])}") 

                st.write(f"Phát sinh: {money(bill['other'])}") 

                st.markdown(f"**Tổng cộng: {money(bill['total'])}**") 

 

                if bill["note"]: 

                    st.caption(f"Ghi chú: {bill['note']}") 

 

        if st.button("🗑️ Xóa toàn bộ lịch sử"): 

            st.session_state.bdu_bills = [] 

            st.session_state.pop("latest_bdu_bill", None) 

            st.rerun() 

 

 

# ========================================== 

# 4. CHATBOX AI 

# ========================================== 

elif page == "Chatbox AI": 

    st.subheader("💬 Chat với trợ lý AI BDUHome") 

    st.caption( 

        "Hỏi đáp về tiền phòng, điện, nước, hóa đơn " 

        "hoặc cách sử dụng ứng dụng." 

    ) 

 

    if not get_api_key(): 

        st.warning( 

            "Chưa tìm thấy OPENAI_API_KEY. Hãy cấu hình Secrets " 

            "trên Streamlit Cloud để bật chat AI." 

        ) 

 

    for message in st.session_state.bdu_chat: 

        with st.chat_message(message["role"]): 

            st.markdown(message["content"]) 

 

    prompt = st.chat_input("Nhập câu hỏi của bạn...") 

 

    if prompt: 

        st.session_state.bdu_chat.append({ 

            "role": "user", 

            "content": prompt, 

        }) 

 

        with st.chat_message("user"): 

            st.markdown(prompt) 

 

        with st.chat_message("assistant"): 

            with st.spinner("BDUHome đang trả lời..."): 

                reply = ask_ai(prompt) 

            st.markdown(reply) 

 

        st.session_state.bdu_chat.append({ 

            "role": "assistant", 

            "content": reply, 

        }) 

 

 

# ---------- CHAN TRANG ---------- 

st.divider() 

st.caption( 

    "© BDUHome | Ứng dụng mẫu quản lý phòng trọ. " 

    "Lịch sử hóa đơn hiện chỉ lưu trong phiên chạy hiện tại." 

) 
