# Quản lý kết quả học tập sinh viên (Bài A1 – JSON)

Chương trình quản lý điểm: nhập điểm, kiểm tra hợp lệ, tính điểm môn và GPA, lưu/đọc dữ liệu bằng file JSON.

Mô tả 2 module đã có:

| File | Vai trò |
|---|---|
| [data.py](data.py) | Kiểm tra dữ liệu đầu vào, đọc/ghi file JSON |
| [tinh_diem.py](tinh_diem.py) | Tính điểm tổng kết từng môn và GPA |
| [tests/test_core.py](tests/test_core.py) | Kiểm thử các phép tính, dữ liệu và luồng lưu/đọc JSON |

Yêu cầu: Python 3.10 trở lên (đã chạy thử với 3.11). Chỉ dùng thư viện chuẩn, không cần cài thêm gì.

---

## Cấu trúc dữ liệu JSON

Dữ liệu là một **danh sách** sinh viên, lưu mặc định ở `ketqua.json` (cùng thư mục với `data.py`):

```json
[
  {
    "ma_sv": "5001104111",
    "ho_ten": "Nguyễn Văn A",
    "mon_hoc": [
      {
        "ten_mon": "Toán",
        "diem_thanh_phan_1": 7.0,
        "diem_thanh_phan_2": 8.0,
        "diem_tong_ket": 7.6
      }
    ],
    "gpa": 7.6
  }
]
```

| Khóa | Kiểu | Ghi chú |
|---|---|---|
| `ma_sv` | chuỗi | Không trống, không trùng trong danh sách |
| `ho_ten` | chuỗi | Không trống |
| `mon_hoc` | list | Ít nhất 1 môn, tên môn không trùng (không phân biệt hoa/thường) |
| `diem_thanh_phan_1` | số 0–10 | Trọng số 40% |
| `diem_thanh_phan_2` | số 0–10 | Trọng số 60% |
| `diem_tong_ket` | số 0–10 | Do `tinh_diem.py` điền vào |
| `gpa` | số 0–10 | Do `tinh_diem.py` điền vào |

---

## data.py – Kiểm tra dữ liệu và đọc/ghi JSON

### Hằng số

| Tên | Giá trị | Ý nghĩa |
|---|---|---|
| `DUONG_DAN_MAC_DINH` | `<thư mục data.py>/ketqua.json` | File JSON mặc định |
| `DIEM_MIN`, `DIEM_MAX` | `0`, `10` | Khoảng điểm hợp lệ |

### 1. Kiểm tra điểm và ô nhập

| Hàm | Trả về | Mô tả |
|---|---|---|
| `kiem_tra_diem(diem)` | `True` / `False` | `True` nếu `diem` là số `int`/`float` trong khoảng 0–10. `True`/`False` (kiểu `bool`) bị coi là không hợp lệ. |
| `chuyen_diem(gia_tri)` | `float` | Đổi dữ liệu người dùng nhập thành điểm. Chấp nhận `"7.5"`, `"7,5"`, `8`. Nhập trống, chữ, hoặc ngoài 0–10 → `ValueError`. |
| `kiem_tra_khong_rong(gia_tri, ten_truong)` | chuỗi đã bỏ khoảng trắng | Dùng cho MSSV, họ tên, tên môn. Để trống → `ValueError`. |

### 2. Kiểm tra sinh viên

| Hàm | Trả về | Mô tả |
|---|---|---|
| `kiem_tra_sinh_vien(sv, ds_hien_co=None)` | list thông báo lỗi | Kiểm tra 1 sinh viên theo bảng cấu trúc ở trên. Truyền `ds_hien_co` để kiểm tra trùng MSSV. List rỗng `[]` = hợp lệ. |
| `kiem_tra_danh_sach(ds_sinh_vien)` | list thông báo lỗi | Kiểm tra cả danh sách (ví dụ ngay sau khi đọc JSON). Chỉ báo lỗi, không tự sửa hay xóa bản ghi. |
| `chuan_hoa_sinh_vien(sv)` | dict mới | Bỏ khoảng trắng thừa (cả khoảng trắng giữa họ tên), đổi điểm về `float`. Chỉ gọi **sau khi** `kiem_tra_sinh_vien` không có lỗi. |

### 3. Đọc / ghi JSON

| Hàm | Trả về | Mô tả |
|---|---|---|
| `doc_json(duong_dan=DUONG_DAN_MAC_DINH)` | list sinh viên | File chưa có hoặc rỗng → `[]`. File hỏng, sai định dạng JSON, hoặc không phải list → `ValueError` (không trả `[]`, để tránh ghi đè làm mất dữ liệu cũ). |
| `ghi_json(ds_sinh_vien, duong_dan=DUONG_DAN_MAC_DINH)` | `True` / `False` | Ghi ra file tạm `.tmp` trước rồi mới thay file thật, nên lỗi giữa chừng không làm hỏng dữ liệu cũ. Giữ nguyên tiếng Việt có dấu, thụt lề 2 dấu cách. |

---

## tinh_diem.py – Tính điểm môn và GPA

### Quy ước tính điểm

- **Điểm môn** = `diem_thanh_phan_1 × 0.4 + diem_thanh_phan_2 × 0.6`, làm tròn **1** chữ số thập phân.
- **GPA** = trung bình cộng các điểm môn **đã làm tròn**, làm tròn **2** chữ số thập phân. Không tính theo tín chỉ vì đề bài không có số tín chỉ.
- Làm tròn bằng hàm `round()` có sẵn của Python.
### 1 Điểm nhỏ trong phần của tui (TanSeng)
> **Lưu ý về `round()`:** hàm này làm tròn kiểu "ngân hàng" và chịu sai số của số thực, nên số 5 ở cuối không phải lúc nào cũng được làm tròn lên. Ví dụ `round(7.25, 1) = 7.2`, `round(2.675, 2) = 2.67`. Nếu cần làm tròn kiểu "5 thì lên", đổi sang thư viện `decimal` với `ROUND_HALF_UP`.

### Hằng số

| Tên | Giá trị |
|---|---|
| `TRONG_SO_1` | `0.4` |
| `TRONG_SO_2` | `0.6` |
| `SO_LE_DIEM_MON` | `1` |
| `SO_LE_GPA` | `2` |

### Hàm

| Hàm | Trả về | Mô tả |
|---|---|---|
| `tinh_diem_mon(diem_1, diem_2)` | `float` | Điểm tổng kết 1 môn. Điểm không phải số 0–10 → `ValueError`. |
| `tinh_gpa(ds_diem_mon)` | `float` | GPA từ list điểm môn. List rỗng hoặc có điểm sai → `ValueError`. |
| `tinh_diem_sinh_vien(sv)` | chính `sv` | Điền `diem_tong_ket` cho từng môn và `gpa` cho sinh viên (sửa trực tiếp dict). Điểm sai → `ValueError` kèm tên môn. |

Ví dụ:

```python
from tinh_diem import tinh_diem_mon, tinh_gpa

tinh_diem_mon(7, 8)        # 7 × 0.4 + 8 × 0.6 = 7.6
tinh_diem_mon(6.5, 7.3)    # 6.98 -> 7.0
tinh_gpa([7.6, 8.0, 6.5])  # 22.1 / 3 = 7.366... -> 7.37
```

---

## Ghép 2 module lại

Luồng xử lý một sinh viên mới: **nhập → kiểm tra → chuẩn hóa → tính điểm → lưu JSON**.

```python
from data import chuyen_diem, kiem_tra_sinh_vien, chuan_hoa_sinh_vien, doc_json, ghi_json
from tinh_diem import tinh_diem_sinh_vien

try:
    ds = doc_json()  # đọc danh sách hiện có

    sv = {
        "ma_sv": "5001104111",
        "ho_ten": "Nguyễn   Văn  A",
        "mon_hoc": [
            {"ten_mon": "Toán", "diem_thanh_phan_1": chuyen_diem("7"),   "diem_thanh_phan_2": chuyen_diem("8")},
            {"ten_mon": "Lý",   "diem_thanh_phan_1": chuyen_diem("6,5"), "diem_thanh_phan_2": chuyen_diem("7.3")},
        ],
    }

    loi = kiem_tra_sinh_vien(sv, ds)
    if loi:
        print("\n".join(loi))
    else:
        sv = tinh_diem_sinh_vien(chuan_hoa_sinh_vien(sv))
        ds.append(sv)
        if ghi_json(ds):
            print("Đã lưu:", sv["ho_ten"], "- GPA", sv["gpa"])
except ValueError as e:
    print("Lỗi:", e)
```

Kết quả: `Đã lưu: Nguyễn Văn A - GPA 7.3` (Toán 7.6, Lý 7.0).

---

## Kiểm thử

```bash
python -m unittest discover -s tests -p test_core.py -v
```
Hướng dẫn chạy giao diện, API, toàn bộ kiểm thử và kịch bản demo được cập nhật trong [README.md](README.md).
