"""Kiểm thử dữ liệu, tính điểm và JSON bằng các tệp tạm riêng biệt."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from analytics import get_gpa_statistics, search_students, sort_students_by_gpa
from data import (
    chuan_hoa_sinh_vien,
    chuyen_diem,
    doc_json,
    ghi_json,
    kiem_tra_danh_sach,
    kiem_tra_diem,
    kiem_tra_sinh_vien,
)
from tinh_diem import tinh_diem_mon, tinh_diem_sinh_vien, tinh_gpa


def sinh_vien_mau():
    return {
        "ma_sv": " DEMO001 ",
        "ho_ten": "  Nguyễn   Văn  Long  ",
        "mon_hoc": [
            {
                "ten_mon": " Lập trình Python ",
                "diem_thanh_phan_1": 7,
                "diem_thanh_phan_2": 9,
            },
            {
                "ten_mon": "Cơ sở dữ liệu",
                "diem_thanh_phan_1": 8,
                "diem_thanh_phan_2": 9,
            },
        ],
    }


class TestTinhDiem(unittest.TestCase):
    def test_trong_so_40_60_va_diem_bien(self):
        cases = [
            (7, 9, 8.2),
            (0, 10, 6.0),
            (10, 0, 4.0),
            (0, 0, 0.0),
            (10, 10, 10.0),
        ]
        for diem_1, diem_2, expected in cases:
            with self.subTest(diem_1=diem_1, diem_2=diem_2):
                self.assertEqual(tinh_diem_mon(diem_1, diem_2), expected)

    def test_lam_tron_diem_mon_mot_chu_so(self):
        self.assertEqual(tinh_diem_mon(6.5, 7.3), 7.0)
        self.assertEqual(tinh_diem_mon(8.5, 9.5), 9.1)

    def test_gpa_trung_binh_cac_diem_mon(self):
        self.assertEqual(tinh_gpa([7.6, 8.0, 6.5]), 7.37)
        self.assertEqual(tinh_gpa([0, 10]), 5.0)
        self.assertEqual(tinh_gpa([8.2]), 8.2)

    def test_gpa_dung_diem_mon_da_lam_tron(self):
        student = sinh_vien_mau()
        student["mon_hoc"][0].update(diem_thanh_phan_1=6.5, diem_thanh_phan_2=7.3)
        student["mon_hoc"][1].update(diem_thanh_phan_1=4, diem_thanh_phan_2=5)
        result = tinh_diem_sinh_vien(student)
        self.assertEqual([mon["diem_tong_ket"] for mon in result["mon_hoc"]], [7.0, 4.6])
        self.assertEqual(result["gpa"], 5.8)

    def test_diem_sai_kieu_ngoai_khoang_va_khong_huu_han(self):
        invalid_scores = [
            -0.1, 10.1, True, False, "7", None, [],
            float("nan"), float("inf"), -float("inf"),
        ]
        for score in invalid_scores:
            with self.subTest(score=score):
                self.assertFalse(kiem_tra_diem(score))
                with self.assertRaises(ValueError):
                    tinh_diem_mon(score, 8)
                with self.assertRaises(ValueError):
                    tinh_diem_mon(8, score)

    def test_gpa_tu_choi_danh_sach_rong_va_diem_sai(self):
        for scores in ([], None, "8", [True], [11], [float("nan")]):
            with self.subTest(scores=scores):
                with self.assertRaises(ValueError):
                    tinh_gpa(scores)

    def test_chuyen_diem_chap_nhan_dau_phay_va_dau_cham(self):
        self.assertEqual(chuyen_diem(" 7,5 "), 7.5)
        self.assertEqual(chuyen_diem("7.5"), 7.5)
        self.assertEqual(chuyen_diem(0), 0.0)
        self.assertEqual(chuyen_diem(10), 10.0)
        for value in ("", "abc", "NaN", "Infinity", True, None, -1, 11):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    chuyen_diem(value)


class TestKiemTraDuLieu(unittest.TestCase):
    def test_sinh_vien_mau_hop_le_va_chuan_hoa_tieng_viet(self):
        student = sinh_vien_mau()
        original = copy.deepcopy(student)
        self.assertEqual(kiem_tra_sinh_vien(student), [])
        result = chuan_hoa_sinh_vien(student)
        self.assertEqual(result["ma_sv"], "DEMO001")
        self.assertEqual(result["ho_ten"], "Nguyễn Văn Long")
        self.assertEqual(result["mon_hoc"][0]["ten_mon"], "Lập trình Python")
        self.assertIsInstance(result["mon_hoc"][0]["diem_thanh_phan_1"], float)
        self.assertEqual(student, original)

    def test_thieu_truong_bat_buoc(self):
        for field in ("ma_sv", "ho_ten", "mon_hoc"):
            with self.subTest(field=field):
                student = sinh_vien_mau()
                student.pop(field)
                self.assertTrue(kiem_tra_sinh_vien(student))
        for field in ("ten_mon", "diem_thanh_phan_1", "diem_thanh_phan_2"):
            with self.subTest(course_field=field):
                student = sinh_vien_mau()
                student["mon_hoc"][0].pop(field)
                self.assertTrue(kiem_tra_sinh_vien(student))

    def test_chuoi_rong_va_kieu_du_lieu_sai(self):
        invalid_fields = [
            ("ma_sv", " "),
            ("ho_ten", " "),
            ("ma_sv", 123),
            ("mon_hoc", []),
            ("mon_hoc", {}),
            ("mon_hoc", [None]),
        ]
        for field, value in invalid_fields:
            with self.subTest(field=field, value=value):
                student = sinh_vien_mau()
                student[field] = value
                self.assertTrue(kiem_tra_sinh_vien(student))
        self.assertTrue(kiem_tra_sinh_vien(None))
        student = sinh_vien_mau()
        student["mon_hoc"][0]["ten_mon"] = " "
        self.assertTrue(kiem_tra_sinh_vien(student))

    def test_tu_choi_mon_hoc_trung_khong_phan_biet_hoa_thuong(self):
        student = sinh_vien_mau()
        student["mon_hoc"][1]["ten_mon"] = "lẬp TrÌnH pYtHoN"
        self.assertTrue(kiem_tra_sinh_vien(student))

    def test_tu_choi_mssv_trung_ke_ca_hoa_thuong_va_khoang_trang(self):
        existing = chuan_hoa_sinh_vien(sinh_vien_mau())
        for duplicate_id in ("DEMO001", " DEMO001 ", "demo001"):
            with self.subTest(duplicate_id=duplicate_id):
                student = sinh_vien_mau()
                student["ma_sv"] = duplicate_id
                self.assertTrue(kiem_tra_sinh_vien(student, [existing]))
                self.assertTrue(kiem_tra_danh_sach([existing, student]))

    def test_tu_choi_diem_thanh_phan_sai(self):
        for field in ("diem_thanh_phan_1", "diem_thanh_phan_2"):
            for score in (-1, 11, True, "7.5", None, float("nan"), float("inf")):
                with self.subTest(field=field, score=score):
                    student = sinh_vien_mau()
                    student["mon_hoc"][0][field] = score
                    self.assertTrue(kiem_tra_sinh_vien(student))


class TestJsonVaLuongDayDu(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "ketqua.json"

    def test_nhap_tinh_luu_mo_lai_tim_sap_xep_va_thong_ke(self):
        raw_students = [sinh_vien_mau(), sinh_vien_mau(), sinh_vien_mau()]
        raw_students[1].update(ma_sv="DEMO002", ho_ten="Sang")
        raw_students[1]["mon_hoc"][0].update(diem_thanh_phan_1=9, diem_thanh_phan_2=9)
        raw_students[1]["mon_hoc"][1].update(diem_thanh_phan_1=8.5, diem_thanh_phan_2=9.5)
        raw_students[2].update(ma_sv="DEMO003", ho_ten="Khoa")
        raw_students[2]["mon_hoc"][0].update(diem_thanh_phan_1=0, diem_thanh_phan_2=0)
        raw_students[2]["mon_hoc"][1].update(diem_thanh_phan_1=10, diem_thanh_phan_2=10)

        students = doc_json(str(self.path))
        for raw_student in raw_students:
            self.assertEqual(kiem_tra_sinh_vien(raw_student, students), [])
            students.append(tinh_diem_sinh_vien(chuan_hoa_sinh_vien(raw_student)))
            self.assertTrue(ghi_json(students, str(self.path)))
            students = doc_json(str(self.path))

        self.assertEqual([sv["gpa"] for sv in students], [8.4, 9.05, 5.0])
        self.assertEqual([sv["ma_sv"] for sv in search_students(students, " LONG ")], ["DEMO001"])
        self.assertEqual([sv["ho_ten"] for sv in search_students(students, "demo002")], ["Sang"])
        self.assertEqual(search_students(students, "không tồn tại"), [])
        self.assertEqual(search_students(students, " "), students)
        self.assertEqual(
            [sv["ma_sv"] for sv in sort_students_by_gpa(students)],
            ["DEMO002", "DEMO001", "DEMO003"],
        )
        self.assertEqual(
            [sv["ma_sv"] for sv in sort_students_by_gpa(students, descending=False)],
            ["DEMO003", "DEMO001", "DEMO002"],
        )
        self.assertEqual([sv["ma_sv"] for sv in students], ["DEMO001", "DEMO002", "DEMO003"])
        stats = get_gpa_statistics(students)
        self.assertEqual(stats["avg_gpa"], 7.48)
        self.assertEqual(stats["max_sv"]["ma_sv"], "DEMO002")
        self.assertEqual(stats["min_sv"]["ma_sv"], "DEMO003")

    def test_doc_file_chua_co_rong_va_danh_sach_rong(self):
        self.assertEqual(doc_json(str(self.path)), [])
        for content in ("", " \n\t", "[]"):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                self.assertEqual(doc_json(str(self.path)), [])

    def test_doc_tu_choi_json_hong_va_cau_truc_goc_sai(self):
        for content in ("{", "[1,", "{}", "null", "1"):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    doc_json(str(self.path))
                self.assertEqual(self.path.read_text(encoding="utf-8"), content)

    def test_doc_tu_choi_ban_ghi_khong_hop_le(self):
        duplicate = sinh_vien_mau()
        duplicate["ma_sv"] = "demo001"
        for students in ([None], [{}], ["sinh viên"], [sinh_vien_mau(), duplicate]):
            with self.subTest(students=students):
                content = json.dumps(students, ensure_ascii=False)
                self.path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    doc_json(str(self.path))
                self.assertEqual(self.path.read_text(encoding="utf-8"), content)

    def test_doc_bo_sung_diem_tong_ket_va_gpa_con_thieu(self):
        raw_student = sinh_vien_mau()
        self.path.write_text(json.dumps([raw_student], ensure_ascii=False), encoding="utf-8")
        student = doc_json(str(self.path))[0]
        self.assertEqual(student["ma_sv"], "DEMO001")
        self.assertEqual(student["ho_ten"], "Nguyễn Văn Long")
        self.assertEqual([mon["diem_tong_ket"] for mon in student["mon_hoc"]], [8.2, 8.6])
        self.assertEqual(student["gpa"], 8.4)

    def test_doc_tinh_lai_diem_tong_ket_va_gpa_cu(self):
        student = sinh_vien_mau()
        student["gpa"] = 10.0
        for course in student["mon_hoc"]:
            course["diem_tong_ket"] = 10.0
        self.path.write_text(json.dumps([student], ensure_ascii=False), encoding="utf-8")
        loaded = doc_json(str(self.path))[0]
        self.assertEqual([mon["diem_tong_ket"] for mon in loaded["mon_hoc"]], [8.2, 8.6])
        self.assertEqual(loaded["gpa"], 8.4)

    def test_luu_giu_nguyen_tieng_viet_va_cau_truc(self):
        students = [tinh_diem_sinh_vien(chuan_hoa_sinh_vien(sinh_vien_mau()))]
        self.assertTrue(ghi_json(students, str(self.path)))
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("Nguyễn Văn Long", text)
        self.assertIn("Lập trình Python", text)
        self.assertEqual(json.loads(text), students)
        self.assertEqual(doc_json(str(self.path)), students)

    def test_ghi_that_bai_giu_noi_dung_da_luu(self):
        students = [tinh_diem_sinh_vien(chuan_hoa_sinh_vien(sinh_vien_mau()))]
        self.assertTrue(ghi_json(students, str(self.path)))
        original = self.path.read_bytes()
        self.assertFalse(ghi_json({"sai": "kiểu gốc"}, str(self.path)))
        self.assertFalse(ghi_json([{"khong_json": object()}], str(self.path)))
        self.assertEqual(self.path.read_bytes(), original)

    def test_thong_ke_khi_chua_co_sinh_vien(self):
        self.assertEqual(get_gpa_statistics([]), {"avg_gpa": 0.0, "max_sv": None, "min_sv": None})
        self.assertEqual(search_students([], "long"), [])
        self.assertEqual(sort_students_by_gpa([]), [])


if __name__ == "__main__":
    unittest.main()
