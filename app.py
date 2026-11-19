import streamlit as st
import json
import os
import urllib.request
import urllib.error
from analytics import search_students, sort_students_by_gpa, get_gpa_statistics

API_URL = "http://127.0.0.1:8000"
DATA_FILE = "data/students.json"

# --- KIỂM TRA TRẠNG THÁI MODULE CỦA TRỌNG & SENG ---
USING_FALLBACK_STORAGE = False
USING_FALLBACK_CALC = False

try:
    from storage import load_data as trong_load, save_data as trong_save, validate_score  # type: ignore
except ImportError:
    USING_FALLBACK_STORAGE = True

    def trong_load():
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def trong_save(data):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def validate_score(score):
        return 0.0 <= float(score) <= 10.0

try:
    from calculator import calc_subject_score, calc_gpa  # type: ignore
except ImportError:
    USING_FALLBACK_CALC = True

    def calc_subject_score(d1, d2):
        return round(float(d1) * 0.4 + float(d2) * 0.6, 1)

    def calc_gpa(mon_hoc_list):
        if not mon_hoc_list:
            return 0.0
        return round(sum(m["diem_tong_ket"] for m in mon_hoc_list) / len(mon_hoc_list), 2)


# --- LỚP GIAO TIẾP DỮ LIỆU (ƯU TIÊN FASTAPI -> FALLBACK LOCAL) ---
def check_api_online() -> bool:
    try:
        with urllib.request.urlopen(f"{API_URL}/students", timeout=0.4) as res:
            return res.status == 200
    except Exception:
        return False


def load_students_data() -> list:
    if check_api_online():
        with urllib.request.urlopen(f"{API_URL}/students", timeout=1) as res:
            return json.loads(res.read().decode("utf-8"))
    return trong_load()


def save_new_student(sv_moi: dict, current_list: list):
    if check_api_online():
        req = urllib.request.Request(
            f"{API_URL}/students",
            data=json.dumps(sv_moi).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1) as res:
            return json.loads(res.read().decode("utf-8"))
    current_list.append(sv_moi)
    trong_save(current_list)


def delete_student_by_id(ma_sv: str, current_list: list) -> list:
    if check_api_online():
        req = urllib.request.Request(f"{API_URL}/students/{ma_sv}", method="DELETE")
        urllib.request.urlopen(req, timeout=1)
        return load_students_data()
    updated = [sv for sv in current_list if sv["ma_sv"].lower() != ma_sv.lower()]
    trong_save(updated)
    return updated


def sync_save_all(current_list: list):
    trong_save(current_list)


# --- CẤU HÌNH TRANG & CSS TỐI ƯU MÀN HÌNH ---
st.set_page_config(
    page_title="Quản lý Điểm - Nhóm Bá Khí",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 1. Thu gọn độ rộng sidebar về 270px để không bị vỡ khung trên máy chiếu */
    section[data-testid="stSidebar"] {
        width: 270px !important;
        min-width: 270px !important;
        max-width: 270px !important;
    }

    /* 2. Ẩn triệt để nút đóng/mở sidebar và biểu tượng mắt xích cạnh tiêu đề */
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"],
    [data-testid="stHeaderActionElements"],
    section[data-testid="stSidebar"] button[kind="header"],
    section[data-testid="stSidebar"] button[kind="headerNoPadding"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* 3. Kéo khung nội dung sidebar sát lên trên cùng */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }
    .block-container {
        padding-top: 1.8rem !important;
    }

    /* 4. Căn chỉnh nút menu sidebar */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[kind="secondary"] {
        justify-content: flex-start !important;
        padding: 0.6rem 0.85rem !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        margin-bottom: 0.25rem !important;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo dữ liệu & trạng thái
if "students" not in st.session_state:
    try:
        st.session_state.students = load_students_data()
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu JSON ban đầu: {e}")
        st.session_state.students = []

if "active_menu" not in st.session_state:
    st.session_state.active_menu = "nhap_diem"

if "flash_msg" not in st.session_state:
    st.session_state.flash_msg = None

if "form_reset_id" not in st.session_state:
    st.session_state.form_reset_id = 0


# --- POPUP XÁC NHẬN TRƯỚC KHI LƯU ---
@st.dialog("📝 Xác nhận thông tin sinh viên", width="large")
def show_confirm_popup(sv_cho: dict):
    st.info("Vui lòng kiểm tra kỹ thông tin và điểm số bên dưới trước khi lưu vào hệ thống.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Mã số sinh viên", sv_cho["ma_sv"])
    c2.metric("Họ và tên", sv_cho["ho_ten"])
    c3.metric("GPA dự kiến", sv_cho["gpa"])

    bang_diem_hien_thi = [
        {
            "Tên môn học": m["ten_mon"],
            "Điểm 1 (40%)": m["diem_1"],
            "Điểm 2 (60%)": m["diem_2"],
            "Điểm tổng kết": m["diem_tong_ket"],
        }
        for m in sv_cho["mon_hoc"]
    ]
    st.dataframe(bang_diem_hien_thi, use_container_width=True, hide_index=True)

    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("✅ Xác nhận & Lưu hồ sơ", type="primary", use_container_width=True):
        try:
            save_new_student(sv_cho, st.session_state.students)
            st.session_state.students = load_students_data()
            st.session_state.flash_msg = (
                f"Đã lưu thành công sinh viên **{sv_cho['ho_ten']}** "
                f"(MSSV: **{sv_cho['ma_sv']}** • GPA: **{sv_cho['gpa']}**)!"
            )
            st.session_state.form_reset_id += 1
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi khi lưu dữ liệu: {e}")

    if btn_col2.button("❌ Hủy / Chỉnh sửa lại", use_container_width=True):
        st.rerun()


MENU_ITEMS = [
    ("nhap_diem", "➕  Nhập sinh viên & Tính điểm"),
    ("danh_sach", "📋  Danh sách, Tìm & Sắp xếp"),
    ("thong_ke", "📊  Thống kê kết quả nhóm"),
    ("du_lieu", "💾  Lưu / Tải dữ liệu JSON"),
]

# --- THIẾT KẾ SIDEBAR MENU ---
with st.sidebar:
    st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 14px 10px;
            text-align: center;
            margin-bottom: 12px;
        ">
            <div style="font-size: 1.8rem; line-height: 1.2;">🎓</div>
            <div style="font-size: 1.05rem; font-weight: 700; margin-top: 6px; color: #FFFFFF;">
                Quản lý Kết quả Học tập
            </div>
            <div style="
                display: inline-block;
                margin-top: 8px;
                padding: 2px 10px;
                font-size: 0.75rem;
                font-weight: 600;
                border-radius: 20px;
                background: rgba(255, 75, 75, 0.18);
                color: #FF6B6B;
            ">
                Nhóm Bá Khí • Bài A1
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.caption("CHỨC NĂNG HỆ THỐNG")

    for key, label in MENU_ITEMS:
        is_active = (st.session_state.active_menu == key)
        if st.button(
            label,
            key=f"btn_{key}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.active_menu = key
            st.session_state.flash_msg = None
            st.rerun()

    st.divider()
    st.info(f"👥 Tổng số hồ sơ: **{len(st.session_state.students)}** sinh viên")

    # Hiển thị trạng thái kết nối để tránh "lỗi im lặng" khi ghép code nhóm
    api_status = "🟢 FastAPI Online" if check_api_online() else "🟡 Chạy độc lập (Local JSON)"
    st.caption(f"Backend: {api_status}")
    if USING_FALLBACK_STORAGE or USING_FALLBACK_CALC:
        st.caption("⚠️ Đang dùng hàm tạm (chờ ghép module Trọng/Seng)")


# --- NỘI DUNG CHÍNH BÊN PHẢI ---
st.title("🎓 Hệ thống Quản lý Kết quả Học tập")
menu = st.session_state.active_menu

if st.session_state.flash_msg:
    st.success(st.session_state.flash_msg, icon="✅")
    st.toast(st.session_state.flash_msg, icon="🎉")
    st.session_state.flash_msg = None

# --- CHỨC NĂNG 1: NHẬP & TÍNH ĐIỂM ---
if menu == "nhap_diem":
    st.subheader("➕ Thêm sinh viên mới (Thang điểm 10)")

    fid = st.session_state.form_reset_id
    col1, col2 = st.columns(2)
    ma_sv = col1.text_input("Mã số sinh viên (MSSV)", key=f"ma_sv_{fid}")
    ho_ten = col2.text_input("Họ và tên", key=f"ho_ten_{fid}")
    so_mon = st.number_input("Số lượng môn học", min_value=1, max_value=15, value=2, step=1)

    with st.form("form_nhap_diem"):
        mon_hoc_inputs = []
        for i in range(int(so_mon)):
            st.markdown(f"**Môn học {i + 1}**")
            c1, c2, c3 = st.columns([2, 1, 1])
            ten_mon = c1.text_input(f"Tên môn {i + 1}", key=f"ten_{fid}_{i}")
            d1 = c2.number_input(f"Điểm 1 (40%) [0-10]", min_value=0.0, max_value=10.0, step=0.1, key=f"d1_{fid}_{i}")
            d2 = c3.number_input(f"Điểm 2 (60%) [0-10]", min_value=0.0, max_value=10.0, step=0.1, key=f"d2_{fid}_{i}")
            mon_hoc_inputs.append((ten_mon, d1, d2))

        submitted = st.form_submit_button("Kiểm tra & Xem trước kết quả", type="primary")
        if submitted:
            try:
                clean_mssv = ma_sv.strip()
                clean_name = ho_ten.strip()

                if not clean_mssv or not clean_name:
                    raise ValueError("Vui lòng nhập đầy đủ MSSV và Họ tên!")

                # Kiểm tra trùng MSSV
                if any(sv["ma_sv"].lower() == clean_mssv.lower() for sv in st.session_state.students):
                    raise ValueError(f"Mã số sinh viên '{clean_mssv}' đã tồn tại trong hệ thống!")

                ds_mon = []
                seen_subjects = set()
                for ten_mon, d1, d2 in mon_hoc_inputs:
                    clean_sub = ten_mon.strip()
                    if not clean_sub:
                        raise ValueError("Tên môn học không được để trống.")
                    if clean_sub.lower() in seen_subjects:
                        raise ValueError(f"Môn học '{clean_sub}' bị nhập trùng lặp.")
                    seen_subjects.add(clean_sub.lower())

                    if not (validate_score(d1) and validate_score(d2)):
                        raise ValueError(f"Điểm môn '{clean_sub}' phải nằm trong khoảng 0 - 10.")

                    diem_tk = calc_subject_score(d1, d2)
                    ds_mon.append({
                        "ten_mon": clean_sub,
                        "diem_1": float(d1),
                        "diem_2": float(d2),
                        "diem_tong_ket": diem_tk
                    })

                gpa = calc_gpa(ds_mon)
                sv_moi = {
                    "ma_sv": clean_mssv,
                    "ho_ten": clean_name,
                    "mon_hoc": ds_mon,
                    "gpa": gpa
                }
                show_confirm_popup(sv_moi)
            except Exception as e:
                st.error(f"Lỗi nhập liệu: {e}")

# --- CHỨC NĂNG 2: XEM, TÌM KIẾM, SẮP XẾP & XÓA ---
elif menu == "danh_sach":
    st.subheader("📋 Danh sách kết quả học tập")

    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("🔍 Tìm kiếm theo MSSV hoặc Họ tên")
    sort_order = c2.selectbox("Sắp xếp theo GPA", ["Mặc định", "Cao đến thấp", "Thấp đến cao"])

    result = search_students(st.session_state.students, keyword)
    if sort_order == "Cao đến thấp":
        result = sort_students_by_gpa(result, descending=True)
    elif sort_order == "Thấp đến cao":
        result = sort_students_by_gpa(result, descending=False)

    if not result:
        st.info("Chưa có dữ liệu sinh viên phù hợp.")
    else:
        for idx, sv in enumerate(result):
            with st.expander(f"🧑‍🎓 {sv['ma_sv']} - {sv['ho_ten']} | GPA: {sv['gpa']}"):
                bang_diem = [
                    {
                        "Tên môn học": m["ten_mon"],
                        "Điểm 1 (40%)": m["diem_1"],
                        "Điểm 2 (60%)": m["diem_2"],
                        "Điểm tổng kết": m["diem_tong_ket"],
                    }
                    for m in sv["mon_hoc"]
                ]
                st.dataframe(bang_diem, use_container_width=True, hide_index=True)

                if st.button(f"🗑️ Xóa hồ sơ ({sv['ma_sv']})", key=f"del_{idx}_{sv['ma_sv']}"):
                    try:
                        st.session_state.students = delete_student_by_id(sv["ma_sv"], st.session_state.students)
                        st.session_state.flash_msg = f"Đã xóa hồ sơ sinh viên **{sv['ho_ten']}** ({sv['ma_sv']})."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi xóa hồ sơ: {e}")

# --- CHỨC NĂNG 3: THỐNG KÊ ---
elif menu == "thong_ke":
    st.subheader("📊 Thống kê GPA toàn nhóm")
    stats = get_gpa_statistics(st.session_state.students)

    if not stats["max_sv"]:
        st.info("Chưa có dữ liệu để thống kê.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("GPA Trung bình nhóm", stats["avg_gpa"])
        c2.metric("GPA Cao nhất", stats["max_sv"]["gpa"], stats["max_sv"]["ho_ten"])
        c3.metric("GPA Thấp nhất", stats["min_sv"]["gpa"], stats["min_sv"]["ho_ten"])

# --- CHỨC NĂNG 4: LƯU / ĐỌC FILE JSON ---
elif menu == "du_lieu":
    st.subheader("💾 Quản lý tệp dữ liệu JSON")
    c1, c2 = st.columns(2)

    if c1.button("Lưu dữ liệu hiện tại ra file JSON", use_container_width=True):
        try:
            sync_save_all(st.session_state.students)
            st.success("Lưu file JSON thành công!", icon="✅")
            st.toast("Lưu file JSON thành công!", icon="💾")
        except Exception as e:
            st.error(f"Lỗi khi lưu file: {e}")

    if c2.button("Đọc lại dữ liệu từ file JSON", use_container_width=True):
        try:
            st.session_state.students = load_students_data()
            st.session_state.flash_msg = "Đã tải lại dữ liệu mới nhất từ tệp JSON!"
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")

    st.json(st.session_state.students)