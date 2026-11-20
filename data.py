import json
import os

THU_MUC_FILE_NAY = os.path.dirname(os.path.abspath(__file__))
DUONG_DAN_MAC_DINH = os.path.join(THU_MUC_FILE_NAY, "ketqua.json")
DIEM_MIN = 0
DIEM_MAX = 10

# ---------------------------------------------------------------------------
# 1. KIỂM TRA ĐIỂM
# ---------------------------------------------------------------------------

def kiem_tra_diem(diem):
    if isinstance(diem, bool):
        return False
    if not isinstance(diem, (int, float)):
        return False
    return DIEM_MIN <= diem <= DIEM_MAX


def chuyen_diem(gia_tri):

    if isinstance(gia_tri, bool):
        raise ValueError("Điểm phải là số, không phải True/False.")

    if isinstance(gia_tri, str):
        chuoi = gia_tri.strip().replace(",", ".")  
        if chuoi == "":
            raise ValueError("Điểm không được để trống.")
        try:
            diem = float(chuoi)
        except ValueError:
            raise ValueError(f"'{gia_tri}' không phải là số.")
    elif isinstance(gia_tri, (int, float)):
        diem = float(gia_tri)
    else:
        raise ValueError("Điểm phải nhập là số.")

    if not kiem_tra_diem(diem):
        raise ValueError(f"Điểm {gia_tri} không hợp lệ, phải trong khoảng {DIEM_MIN}-{DIEM_MAX}.")
    return diem


def kiem_tra_khong_rong(gia_tri, ten_truong):
    if not isinstance(gia_tri, str) or gia_tri.strip() == "":
        raise ValueError(f"{ten_truong} không được để trống.")
    return gia_tri.strip()


# ---------------------------------------------------------------------------
# 2. KIỂM TRA MỘT SINH VIÊN
# ---------------------------------------------------------------------------

def _la_chuoi_khong_rong(gia_tri):
    return isinstance(gia_tri, str) and gia_tri.strip() != ""


def kiem_tra_sinh_vien(sv, ds_hien_co=None):
    loi = []

    if not isinstance(sv, dict):
        return ["Dữ liệu sinh viên phải là dict."]
    ma_sv = sv.get("ma_sv")
    if not _la_chuoi_khong_rong(ma_sv):
        loi.append("MSSV không được để trống và phải là chuỗi (ví dụ \"5001104111\").")
    elif ds_hien_co:
        ma_da_co = set()
        for sv_cu in ds_hien_co:
            if isinstance(sv_cu, dict) and isinstance(sv_cu.get("ma_sv"), str):
                ma_da_co.add(sv_cu["ma_sv"].strip())
        if ma_sv.strip() in ma_da_co:
            loi.append(f"MSSV {ma_sv.strip()} đã tồn tại.")
    if not _la_chuoi_khong_rong(sv.get("ho_ten")):
        loi.append("Họ tên không được để trống.")
    mon_hoc = sv.get("mon_hoc")
    if not isinstance(mon_hoc, list) or len(mon_hoc) == 0:
        loi.append("Sinh viên phải có ít nhất 1 môn học.")
    else:
        ten_da_gap = set()
        for i, mon in enumerate(mon_hoc, start=1):
            if not isinstance(mon, dict):
                loi.append(f"Môn thứ {i}: dữ liệu môn học phải là dict.")
                continue

            ten_mon = mon.get("ten_mon")
            if not _la_chuoi_khong_rong(ten_mon):
                loi.append(f"Môn thứ {i}: tên môn không được để trống.")
            else:
                ten_chuan = ten_mon.strip().lower()
                if ten_chuan in ten_da_gap:
                    loi.append(f"Môn thứ {i}: môn '{ten_mon.strip()}' bị nhập trùng.")
                ten_da_gap.add(ten_chuan)

            for khoa in ("diem_thanh_phan_1", "diem_thanh_phan_2"):
                if not kiem_tra_diem(mon.get(khoa)):
                    loi.append(f"Môn thứ {i}: {khoa} = {mon.get(khoa)!r} không hợp lệ (phải là số 0-10).")
            if mon.get("diem_tong_ket") is not None and not kiem_tra_diem(mon["diem_tong_ket"]):
                loi.append(f"Môn thứ {i}: diem_tong_ket không hợp lệ.")
    gpa = sv.get("gpa")
    if gpa is not None and not kiem_tra_diem(gpa):
        loi.append("GPA không hợp lệ (phải là số 0-10).")

    return loi

def kiem_tra_danh_sach(ds_sinh_vien):
    loi = []
    da_duyet = []
    for i, sv in enumerate(ds_sinh_vien, start=1):
        for thong_bao in kiem_tra_sinh_vien(sv, da_duyet):
            loi.append(f"Sinh viên thứ {i}: {thong_bao}")
        da_duyet.append(sv)
    return loi


def chuan_hoa_sinh_vien(sv):
    mon_moi = []
    for mon in sv.get("mon_hoc", []):
        mon_moi.append({
            "ten_mon": mon["ten_mon"].strip(),
            "diem_thanh_phan_1": float(mon["diem_thanh_phan_1"]),
            "diem_thanh_phan_2": float(mon["diem_thanh_phan_2"]),
            "diem_tong_ket": mon.get("diem_tong_ket"),
        })
    return {
        "ma_sv": sv["ma_sv"].strip(),
        "ho_ten": " ".join(sv["ho_ten"].split()), 
        "mon_hoc": mon_moi,
        "gpa": sv.get("gpa"),
    }


# ---------------------------------------------------------------------------
# 3. ĐỌC / GHI JSON
# ---------------------------------------------------------------------------

def doc_json(duong_dan=DUONG_DAN_MAC_DINH):
    if not os.path.exists(duong_dan):
        return []

    try:
        with open(duong_dan, "r", encoding="utf-8") as f:
            noi_dung = f.read()
    except OSError as e:
        raise ValueError(f"Không mở được file '{duong_dan}': {e}")

    if noi_dung.strip() == "":
        return []

    try:
        du_lieu = json.loads(noi_dung)
    except json.JSONDecodeError as e:
        raise ValueError(f"File '{duong_dan}' không đúng định dạng JSON (dòng {e.lineno}, cột {e.colno}).")

    if not isinstance(du_lieu, list):
        raise ValueError(f"File '{duong_dan}' phải chứa một danh sách [ ] sinh viên.")

    return du_lieu


def ghi_json(ds_sinh_vien, duong_dan=DUONG_DAN_MAC_DINH):
    if not isinstance(ds_sinh_vien, list):
        return False
    file_tam = duong_dan + ".tmp"
    try:
        with open(file_tam, "w", encoding="utf-8") as f:
            json.dump(ds_sinh_vien, f, ensure_ascii=False, indent=2)
        os.replace(file_tam, duong_dan)
        return True
    except (OSError, TypeError, ValueError):
        if os.path.exists(file_tam):
            os.remove(file_tam)
        return False


