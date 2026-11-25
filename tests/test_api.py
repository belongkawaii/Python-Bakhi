"""Kiểm thử API bằng tệp JSON tạm, tách khỏi dữ liệu đang sử dụng."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from unittest.mock import patch

import data


CO_THU_VIEN_API = all(
    importlib.util.find_spec(ten) is not None for ten in ("fastapi", "httpx")
)

if CO_THU_VIEN_API:
    from fastapi.testclient import TestClient

    import api


@unittest.skipUnless(CO_THU_VIEN_API, "Cần cài fastapi và httpx để kiểm thử API.")
class TestAPI(unittest.TestCase):
    def setUp(self):
        thu_muc_tam = TemporaryDirectory()
        self.addCleanup(thu_muc_tam.cleanup)
        self.duong_dan = Path(thu_muc_tam.name) / "ketqua.json"
        thay_the_luu_tru = patch.multiple(
            api,
            doc_json=partial(data.doc_json, duong_dan=str(self.duong_dan)),
            ghi_json=partial(data.ghi_json, duong_dan=str(self.duong_dan)),
        )
        thay_the_luu_tru.start()
        self.addCleanup(thay_the_luu_tru.stop)
        self.client = TestClient(api.app)
        self.addCleanup(self.client.close)
        self.sinh_vien = {
            "ma_sv": " DEMO001 ",
            "ho_ten": "  Long   Demo  ",
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

    def test_nhap_tinh_luu_mo_lai_xem_ket_qua(self):
        phan_hoi = self.client.post("/students", json=self.sinh_vien)
        self.assertEqual(phan_hoi.status_code, 200, phan_hoi.text)
        da_luu = phan_hoi.json()["data"]
        self.assertEqual(da_luu["ma_sv"], "DEMO001")
        self.assertEqual(da_luu["ho_ten"], "Long Demo")
        self.assertEqual(da_luu["mon_hoc"][0]["ten_mon"], "Lập trình Python")
        self.assertEqual(
            [mon["diem_tong_ket"] for mon in da_luu["mon_hoc"]], [8.2, 8.6]
        )
        self.assertEqual(da_luu["gpa"], 8.4)
        noi_dung = self.duong_dan.read_text(encoding="utf-8")
        self.assertIn("Lập trình Python", noi_dung)
        self.assertEqual(json.loads(noi_dung), [da_luu])

        with TestClient(api.app) as client_moi:
            phan_hoi_moi = client_moi.get("/students")
            self.assertEqual(phan_hoi_moi.status_code, 200)
            self.assertEqual(phan_hoi_moi.json(), [da_luu])

    def test_tinh_lai_diem_tong_ket_va_gpa_duoc_gui_kem(self):
        du_lieu = deepcopy(self.sinh_vien)
        du_lieu["gpa"] = 1.0
        for mon in du_lieu["mon_hoc"]:
            mon["diem_tong_ket"] = 1.0
        phan_hoi = self.client.post("/students", json=du_lieu)
        self.assertEqual(phan_hoi.status_code, 200, phan_hoi.text)
        da_luu = phan_hoi.json()["data"]
        self.assertEqual(da_luu["gpa"], 8.4)
        self.assertEqual(da_luu["mon_hoc"][0]["diem_tong_ket"], 8.2)

    def test_tu_choi_ma_sinh_vien_trung_va_giu_nguyen_tep(self):
        self.assertEqual(self.client.post("/students", json=self.sinh_vien).status_code, 200)
        truoc_khi_gui = self.duong_dan.read_bytes()
        for ma_trung in ("DEMO001", "demo001", " demo001 "):
            with self.subTest(ma_trung=ma_trung):
                du_lieu_trung = deepcopy(self.sinh_vien)
                du_lieu_trung["ma_sv"] = ma_trung
                phan_hoi = self.client.post("/students", json=du_lieu_trung)
                self.assertEqual(phan_hoi.status_code, 400)
                self.assertEqual(self.duong_dan.read_bytes(), truoc_khi_gui)

    def test_tu_choi_diem_ngoai_thang_10(self):
        for diem in (-0.1, 10.1):
            with self.subTest(diem=diem):
                du_lieu = deepcopy(self.sinh_vien)
                du_lieu["mon_hoc"][0]["diem_thanh_phan_1"] = diem
                phan_hoi = self.client.post("/students", json=du_lieu)
                self.assertEqual(phan_hoi.status_code, 422)
                self.assertFalse(self.duong_dan.exists())

    def test_tu_choi_diem_boolean(self):
        for diem in (True, False):
            with self.subTest(diem=diem):
                du_lieu = deepcopy(self.sinh_vien)
                du_lieu["mon_hoc"][0]["diem_thanh_phan_1"] = diem
                phan_hoi = self.client.post("/students", json=du_lieu)
                self.assertEqual(phan_hoi.status_code, 422)
                self.assertFalse(self.duong_dan.exists())

    def test_tu_choi_ten_trong_thieu_mon_va_mon_trung(self):
        cac_truong_hop = []
        ten_trong = deepcopy(self.sinh_vien)
        ten_trong["ho_ten"] = "   "
        cac_truong_hop.append(ten_trong)
        thieu_mon = deepcopy(self.sinh_vien)
        thieu_mon["mon_hoc"] = []
        cac_truong_hop.append(thieu_mon)
        mon_trung = deepcopy(self.sinh_vien)
        mon_trung["mon_hoc"][1]["ten_mon"] = "lập trình python"
        cac_truong_hop.append(mon_trung)

        for du_lieu in cac_truong_hop:
            with self.subTest(du_lieu=du_lieu):
                phan_hoi = self.client.post("/students", json=du_lieu)
                self.assertEqual(phan_hoi.status_code, 400)
                self.assertFalse(self.duong_dan.exists())

    def test_chap_nhan_diem_bien_0_va_10(self):
        du_lieu = deepcopy(self.sinh_vien)
        du_lieu["mon_hoc"] = [{
            "ten_mon": "Môn kiểm tra biên",
            "diem_thanh_phan_1": 0,
            "diem_thanh_phan_2": 10,
        }]
        phan_hoi = self.client.post("/students", json=du_lieu)
        self.assertEqual(phan_hoi.status_code, 200, phan_hoi.text)
        self.assertEqual(phan_hoi.json()["data"]["gpa"], 6.0)

    def test_tim_kiem_sap_xep_va_thong_ke_sau_khi_luu(self):
        self.assertEqual(self.client.post("/students", json=self.sinh_vien).status_code, 200)
        sinh_vien_hai = {
            "ma_sv": "DEMO002",
            "ho_ten": "Sang Demo",
            "mon_hoc": [{
                "ten_mon": "Lập trình Python",
                "diem_thanh_phan_1": 3,
                "diem_thanh_phan_2": 5,
            }],
        }
        self.assertEqual(self.client.post("/students", json=sinh_vien_hai).status_code, 200)
        theo_ten = self.client.get("/students", params={"keyword": "LONG"})
        self.assertEqual([sv["ma_sv"] for sv in theo_ten.json()], ["DEMO001"])
        theo_ma = self.client.get("/students", params={"keyword": "002"})
        self.assertEqual([sv["ma_sv"] for sv in theo_ma.json()], ["DEMO002"])
        tang_dan = self.client.get("/students", params={"sort": "asc"})
        self.assertEqual([sv["ma_sv"] for sv in tang_dan.json()], ["DEMO002", "DEMO001"])
        giam_dan = self.client.get("/students", params={"sort": "desc"})
        self.assertEqual([sv["ma_sv"] for sv in giam_dan.json()], ["DEMO001", "DEMO002"])
        thong_ke = self.client.get("/statistics").json()
        self.assertEqual(thong_ke["avg_gpa"], 6.3)
        self.assertEqual(thong_ke["max_sv"]["ma_sv"], "DEMO001")
        self.assertEqual(thong_ke["min_sv"]["ma_sv"], "DEMO002")

    def test_xoa_duoc_luu_va_doc_lai(self):
        self.assertEqual(self.client.post("/students", json=self.sinh_vien).status_code, 200)
        self.assertEqual(self.client.delete("/students/DEMO001").status_code, 200)
        self.assertEqual(data.doc_json(str(self.duong_dan)), [])
        with TestClient(api.app) as client_moi:
            self.assertEqual(client_moi.get("/students").json(), [])
            self.assertEqual(client_moi.delete("/students/DEMO001").status_code, 404)

    def test_bao_loi_khi_khong_luu_duoc(self):
        with patch.object(api, "ghi_json", return_value=False):
            phan_hoi = self.client.post("/students", json=self.sinh_vien)
        self.assertEqual(phan_hoi.status_code, 500)
        self.assertFalse(self.duong_dan.exists())

    def test_cac_endpoint_bao_loi_json_hong_va_giu_nguyen_tep(self):
        self.duong_dan.write_text('[{"ma_sv": ', encoding="utf-8")
        truoc_khi_gui = self.duong_dan.read_bytes()
        cac_yeu_cau = (
            ("GET", "/students", {}),
            ("POST", "/students", {"json": self.sinh_vien}),
            ("DELETE", "/students/DEMO001", {}),
            ("GET", "/statistics", {}),
        )
        for phuong_thuc, duong_dan, tham_so in cac_yeu_cau:
            with self.subTest(phuong_thuc=phuong_thuc, duong_dan=duong_dan):
                phan_hoi = self.client.request(phuong_thuc, duong_dan, **tham_so)
                self.assertEqual(phan_hoi.status_code, 500)
                self.assertIsInstance(phan_hoi.json()["detail"], str)
                self.assertEqual(self.duong_dan.read_bytes(), truoc_khi_gui)

    def test_nhieu_yeu_cau_them_dong_thoi_giu_du_cac_sinh_vien(self):
        so_sinh_vien = 4
        cung_bat_dau = Barrier(so_sinh_vien)

        with TestClient(api.app) as client_song_song:
            def them_sinh_vien(thu_tu):
                sinh_vien = deepcopy(self.sinh_vien)
                sinh_vien["ma_sv"] = f"PARALLEL{thu_tu:03d}"
                cung_bat_dau.wait(timeout=10)
                return client_song_song.post("/students", json=sinh_vien)

            with ThreadPoolExecutor(max_workers=so_sinh_vien) as nhom_luong:
                cac_phan_hoi = list(nhom_luong.map(them_sinh_vien, range(so_sinh_vien)))

        for phan_hoi in cac_phan_hoi:
            self.assertEqual(phan_hoi.status_code, 200, phan_hoi.text)
        da_luu = data.doc_json(str(self.duong_dan))
        self.assertEqual(len(da_luu), so_sinh_vien)
        self.assertEqual(
            {sv["ma_sv"] for sv in da_luu},
            {f"PARALLEL{thu_tu:03d}" for thu_tu in range(so_sinh_vien)},
        )
        self.assertTrue(all(sv["gpa"] == 8.4 for sv in da_luu))


if __name__ == "__main__":
    unittest.main()
