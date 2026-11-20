from data import kiem_tra_diem
TRONG_SO_1 = 0.4
TRONG_SO_2 = 0.6
SO_LE_DIEM_MON = 1
SO_LE_GPA = 2

def tinh_diem_mon(diem_1, diem_2):
    for ten, diem in (("Điểm thành phần 1", diem_1), ("Điểm thành phần 2", diem_2)):
        if not kiem_tra_diem(diem):
            raise ValueError(f"{ten} = {diem!r} không hợp lệ (phải là số 0-10).")

    return round(diem_1 * TRONG_SO_1 + diem_2 * TRONG_SO_2, SO_LE_DIEM_MON)


def tinh_gpa(ds_diem_mon):
    if not isinstance(ds_diem_mon, (list, tuple)) or len(ds_diem_mon) == 0:
        raise ValueError("Cần ít nhất 1 điểm môn để tính GPA.")
    for diem in ds_diem_mon:
        if not kiem_tra_diem(diem):
            raise ValueError(f"Điểm môn {diem!r} không hợp lệ (phải là số 0-10).")

    return round(sum(ds_diem_mon) / len(ds_diem_mon), SO_LE_GPA)


def tinh_diem_sinh_vien(sv):
    mon_hoc = sv.get("mon_hoc")
    if not isinstance(mon_hoc, list) or len(mon_hoc) == 0:
        raise ValueError("Sinh viên phải có ít nhất 1 môn học.")

    ds_diem_mon = []
    for mon in mon_hoc:
        try:
            diem = tinh_diem_mon(mon.get("diem_thanh_phan_1"), mon.get("diem_thanh_phan_2"))
        except ValueError as e:
            raise ValueError(f"Môn '{mon.get('ten_mon')}': {e}")
        mon["diem_tong_ket"] = diem
        ds_diem_mon.append(diem)

    sv["gpa"] = tinh_gpa(ds_diem_mon)
    return sv
