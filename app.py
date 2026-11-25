import streamlit as st
import json
import socket
import urllib.request
import urllib.parse
from data import (
    doc_json,
    ghi_json,
    kiem_tra_sinh_vien,
    kiem_tra_danh_sach,
    chuan_hoa_sinh_vien,
)
from tinh_diem import tinh_diem_sinh_vien
from analytics import search_students, sort_students_by_gpa, get_gpa_statistics

API_URL = "http://127.0.0.1:8000"


@st.cache_data(ttl=15, show_spinner=False)
def check_api_online() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.05):
            return True
    except OSError:
        return False


def load_students_data() -> list:
    if check_api_online():
        with urllib.request.urlopen(f"{API_URL}/students", timeout=1) as res:
            return json.loads(res.read().decode("utf-8"))
    return doc_json()


def save_new_student(sv_da_tinh: dict, current_list: list):
    if check_api_online():
        req = urllib.request.Request(
            f"{API_URL}/students",
            data=json.dumps(sv_da_tinh).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1) as res:
            return json.loads(res.read().decode("utf-8"))

    updated_list = current_list + [sv_da_tinh]
    if not ghi_json(updated_list):
        raise IOError("Ghi dữ liệu vào ketqua.json thất bại.")


def delete_student_by_id(ma_sv: str, current_list: list) -> list:
    if check_api_online():
        encoded_id = urllib.parse.quote(ma_sv.strip(), safe="")
        req = urllib.request.Request(f"{API_URL}/students/{encoded_id}", method="DELETE")
        urllib.request.urlopen(req, timeout=1)
        return load_students_data()

    updated = [sv for sv in current_list if sv["ma_sv"].strip().lower() != ma_sv.strip().lower()]
    if not ghi_json(updated):
        raise IOError("Cập nhật file ketqua.json thất bại.")
    return updated

    updated = [sv for sv in current_list if sv["ma_sv"].strip().lower() != ma_sv.strip().lower()]
    if not ghi_json(updated):
        raise IOError("Cập nhật file ketqua.json thất bại.")
    return updated


st.set_page_config(
    page_title="Quản lý Điểm - Nhóm Bá Khí",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        width: 270px !important;
        min-width: 270px !important;
        max-width: 270px !important;
    }
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
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }
    .block-container {
        padding-top: 1.8rem !important;
    }
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

if "students" not in st.session_state:
    try:
        ds_khoi_tao = load_students_data()
        loi_ds = kiem_tra_danh_sach(ds_khoi_tao)
        if loi_ds:
            st.warning("Phát hiện dữ liệu không hợp lệ trong file JSON:\n- " + "\n- ".join(loi_ds))
        st.session_state.students = ds_khoi_tao
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu JSON ban đầu: {e}")
        st.session_state.students = []

if "active_menu" not in st.session_state:
    st.session_state.active_menu = "nhap_diem"

if "flash_msg" not in st.session_state:
    st.session_state.flash_msg = None

if "form_reset_id" not in st.session_state:
    st.session_state.form_reset_id = 0


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
            "Điểm thành phần 1 (40%)": m["diem_thanh_phan_1"],
            "Điểm thành phần 2 (60%)": m["diem_thanh_phan_2"],
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
                f"(MSSV: **{sv_cho['ma_sv']}** • GPA: **{sv_cho['gpa']}**) vào ketqua.json!"
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

    api_status = "🟢 FastAPI Online" if check_api_online() else "🟡 Chạy trực tiếp (data.py)"
    st.caption(f"Backend: {api_status}")
    st.caption("🟢 Đã tích hợp data.py & tinh_diem.py")


st.title("🎓 Hệ thống Quản lý Kết quả Học tập")
menu = st.session_state.active_menu

if st.session_state.flash_msg:
    st.success(st.session_state.flash_msg, icon="✅")
    st.toast(st.session_state.flash_msg, icon="🎉")
    st.session_state.flash_msg = None

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
            d1 = c2.number_input(f"Điểm thành phần 1 (40%) [0-10]", min_value=0.0, max_value=10.0, step=0.1, key=f"d1_{fid}_{i}")
            d2 = c3.number_input(f"Điểm thành phần 2 (60%) [0-10]", min_value=0.0, max_value=10.0, step=0.1, key=f"d2_{fid}_{i}")
            mon_hoc_inputs.append({
                "ten_mon": ten_mon,
                "diem_thanh_phan_1": float(d1),
                "diem_thanh_phan_2": float(d2),
            })

        submitted = st.form_submit_button("Kiểm tra & Xem trước kết quả", type="primary")
        if submitted:
            sv_tho = {
                "ma_sv": ma_sv,
                "ho_ten": ho_ten,
                "mon_hoc": mon_hoc_inputs,
            }
            danh_sach_loi = kiem_tra_sinh_vien(sv_tho, st.session_state.students)
            if danh_sach_loi:
                st.error("Phát hiện lỗi nhập liệu:\n- " + "\n- ".join(danh_sach_loi))
            else:
                try:
                    sv_hoan_chinh = tinh_diem_sinh_vien(chuan_hoa_sinh_vien(sv_tho))
                    show_confirm_popup(sv_hoan_chinh)
                except ValueError as e:
                    st.error(f"Lỗi tính điểm: {e}")

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
                        "Điểm thành phần 1 (40%)": m["diem_thanh_phan_1"],
                        "Điểm thành phần 2 (60%)": m["diem_thanh_phan_2"],
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

elif menu == "du_lieu":
    st.subheader("💾 Quản lý tệp dữ liệu JSON (ketqua.json)")
    c1, c2 = st.columns(2)

    if c1.button("Lưu dữ liệu hiện tại ra file ketqua.json", use_container_width=True):
        if ghi_json(st.session_state.students):
            st.success("Lưu file ketqua.json thành công!", icon="✅")
            st.toast("Lưu file ketqua.json thành công!", icon="💾")
        else:
            st.error("Lỗi khi lưu file ketqua.json!")

    if c2.button("Đọc lại dữ liệu từ file ketqua.json", use_container_width=True):
        try:
            st.session_state.students = load_students_data()
            st.session_state.flash_msg = "Đã tải lại dữ liệu mới nhất từ tệp ketqua.json!"
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")

    st.json(st.session_state.students)