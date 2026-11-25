"""Exercise the Streamlit form and saved results using temporary JSON files."""

import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import data

STREAMLIT_AVAILABLE = importlib.util.find_spec("streamlit") is not None
if STREAMLIT_AVAILABLE:
    from streamlit.testing.v1 import AppTest
    from streamlit.runtime.scriptrunner_utils.script_requests import ScriptRequests


@unittest.skipUnless(STREAMLIT_AVAILABLE, "Install streamlit to run UI tests")
class StreamlitFlowTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.json_path = Path(temporary_directory.name) / "ketqua.json"
        self.real_read = data.doc_json
        self.real_write = data.ghi_json
        read_patch = patch("data.doc_json", side_effect=self.read_students)
        write_patch = patch("data.ghi_json", side_effect=self.write_students)
        offline_patch = patch.object(
            socket, "create_connection", side_effect=OSError("API offline for test")
        )
        read_patch.start()
        write_patch.start()
        offline_patch.start()
        self.addCleanup(read_patch.stop)
        self.addCleanup(write_patch.stop)
        self.addCleanup(offline_patch.stop)

    def read_students(self, *args, **kwargs):
        return self.real_read(str(self.json_path))

    def write_students(self, students, *args, **kwargs):
        return self.real_write(students, str(self.json_path))

    def new_app(self):
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=15)
        app.run()
        self.assertEqual(list(app.exception), [])
        return app

    def click_button(self, app, label):
        buttons = [button for button in app.button if button.label == label]
        self.assertEqual(len(buttons), 1, f"Button not found: {label}")
        buttons[0].click().run()
        self.assertEqual(list(app.exception), [])

    def fill_student(self, app, student_id="DEMO001", name="Nguyễn Văn Long"):
        reset_id = app.session_state["form_reset_id"]
        app.text_input(key=f"ma_sv_{reset_id}").set_value(student_id)
        app.text_input(key=f"ho_ten_{reset_id}").set_value(name)
        app.text_input(key=f"ten_{reset_id}_0").set_value("Lập trình Python")
        app.number_input(key=f"d1_{reset_id}_0").set_value(7.0)
        app.number_input(key=f"d2_{reset_id}_0").set_value(9.0)
        app.text_input(key=f"ten_{reset_id}_1").set_value("Cơ sở dữ liệu")
        app.number_input(key=f"d1_{reset_id}_1").set_value(8.0)
        app.number_input(key=f"d2_{reset_id}_1").set_value(9.0)
        self.click_button(app, "Kiểm tra & Xem trước kết quả")

    def confirm_student(self, app):
        # AppTest reruns the whole page by default. Dialog buttons in a browser
        # rerun their fragment, so preserve that scope for this interaction.
        fragment_ids = list(app._fragment_storage._fragments)
        self.assertEqual(len(fragment_ids), 1)
        request_rerun = ScriptRequests.request_rerun

        def rerun_dialog(requests, rerun_data):
            if threading.current_thread() is threading.main_thread():
                rerun_data = replace(rerun_data, fragment_id_queue=fragment_ids)
            return request_rerun(requests, rerun_data)

        with patch.object(ScriptRequests, "request_rerun", rerun_dialog):
            self.click_button(app, "✅ Xác nhận & Lưu hồ sơ")
        self.assertEqual(list(app.error), [])

    def test_form_calculates_saves_reopens_and_displays_results(self):
        app = self.new_app()
        self.fill_student(app)
        preview_gpa = [metric.value for metric in app.metric if metric.label == "GPA dự kiến"]
        self.assertEqual(preview_gpa, ["8.4"])
        self.assertFalse(self.json_path.exists(), "Preview must not save before confirmation")
        self.confirm_student(app)

        persisted = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["gpa"], 8.4)
        self.assertEqual(
            [course["diem_tong_ket"] for course in persisted[0]["mon_hoc"]],
            [8.2, 8.6],
        )

        reopened = self.new_app()
        self.click_button(reopened, "📋  Danh sách, Tìm & Sắp xếp")
        self.assertEqual(len(reopened.expander), 1)
        self.assertIn("DEMO001", reopened.expander[0].label)
        self.assertIn("GPA: 8.4", reopened.expander[0].label)
        displayed = reopened.dataframe[0].value
        self.assertEqual(list(displayed["Điểm tổng kết"]), [8.2, 8.6])

    def test_empty_form_reports_error_without_saving(self):
        app = self.new_app()
        self.click_button(app, "Kiểm tra & Xem trước kết quả")
        self.assertTrue(app.error)
        self.assertIn("MSSV", app.error[0].value)
        self.assertFalse(self.json_path.exists())

    def test_duplicate_student_reports_error_without_changing_file(self):
        app = self.new_app()
        self.fill_student(app)
        self.confirm_student(app)
        saved_bytes = self.json_path.read_bytes()
        self.fill_student(app, student_id="demo001")
        self.assertTrue(app.error)
        self.assertIn("đã tồn tại", app.error[0].value)
        self.assertEqual(self.json_path.read_bytes(), saved_bytes)

    def test_corrupt_json_blocks_input_and_preserves_file(self):
        self.json_path.write_text('{"broken":', encoding="utf-8")
        saved_bytes = self.json_path.read_bytes()
        app = self.new_app()
        self.assertTrue(app.error)
        self.assertEqual(len(app.text_input), 0)
        self.assertEqual(self.json_path.read_bytes(), saved_bytes)

    def test_input_only_json_is_calculated_before_result_display(self):
        raw_student = {
            "ma_sv": "RAW001",
            "ho_ten": "Trọng",
            "mon_hoc": [
                {
                    "ten_mon": "Lập trình Python",
                    "diem_thanh_phan_1": 7,
                    "diem_thanh_phan_2": 9,
                }
            ],
        }
        self.json_path.write_text(json.dumps([raw_student]), encoding="utf-8")
        app = self.new_app()
        self.click_button(app, "📋  Danh sách, Tìm & Sắp xếp")
        self.assertIn("GPA: 8.2", app.expander[0].label)
        self.assertEqual(list(app.dataframe[0].value["Điểm tổng kết"]), [8.2])

    def test_add_from_stale_session_preserves_students_added_elsewhere(self):
        app = self.new_app()
        existing_student = {
            "ma_sv": "EXISTING001",
            "ho_ten": "Sang",
            "mon_hoc": [
                {
                    "ten_mon": "Lập trình Python",
                    "diem_thanh_phan_1": 8,
                    "diem_thanh_phan_2": 8,
                    "diem_tong_ket": 8,
                }
            ],
            "gpa": 8,
        }
        self.assertTrue(self.real_write([existing_student], str(self.json_path)))
        self.fill_student(app)
        self.confirm_student(app)
        persisted = self.real_read(str(self.json_path))
        self.assertEqual(
            {student["ma_sv"] for student in persisted},
            {"EXISTING001", "DEMO001"},
        )

    def test_save_reload_and_statistics_keep_current_json_results(self):
        demo_path = PROJECT_ROOT / "demo" / "ketqua_demo.json"
        self.json_path.write_bytes(demo_path.read_bytes())
        app = self.new_app()
        self.click_button(app, "💾  Lưu / Tải dữ liệu JSON")
        stored_students = self.real_read(str(self.json_path))
        extra_student = {
            "ma_sv": "EXTRA001",
            "ho_ten": "Sinh viên mới",
            "mon_hoc": [
                {
                    "ten_mon": "Lập trình Python",
                    "diem_thanh_phan_1": 10,
                    "diem_thanh_phan_2": 10,
                    "diem_tong_ket": 10,
                }
            ],
            "gpa": 10,
        }
        self.assertTrue(
            self.real_write(stored_students + [extra_student], str(self.json_path))
        )
        self.click_button(app, "Lưu dữ liệu hiện tại ra file ketqua.json")
        self.assertEqual(len(self.real_read(str(self.json_path))), 5)
        self.click_button(app, "Đọc lại dữ liệu từ file ketqua.json")
        self.assertEqual(len(app.session_state["students"]), 5)
        self.click_button(app, "📊  Thống kê kết quả nhóm")
        metrics = {metric.label: metric.value for metric in app.metric}
        self.assertEqual(metrics["GPA Trung bình nhóm"], "8.21")
        self.assertEqual(metrics["GPA Cao nhất"], "10.0")
        self.assertEqual(metrics["GPA Thấp nhất"], "6.6")


if __name__ == "__main__":
    unittest.main()
