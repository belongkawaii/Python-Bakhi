from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from data import doc_json, ghi_json, kiem_tra_sinh_vien, chuan_hoa_sinh_vien
from tinh_diem import tinh_diem_sinh_vien
from analytics import search_students, sort_students_by_gpa, get_gpa_statistics

app = FastAPI(title="API Quản lý Kết quả Học tập - Nhóm Bá Khí")


class MonHoc(BaseModel):
    ten_mon: str
    diem_thanh_phan_1: float = Field(..., ge=0.0, le=10.0)
    diem_thanh_phan_2: float = Field(..., ge=0.0, le=10.0)
    diem_tong_ket: float | None = None


class SinhVien(BaseModel):
    ma_sv: str
    ho_ten: str
    mon_hoc: List[MonHoc]
    gpa: float | None = None


@app.get("/students")
def get_all_students(keyword: str = "", sort: str = "default"):
    try:
        students = doc_json()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = search_students(students, keyword)
    if sort == "desc":
        result = sort_students_by_gpa(result, descending=True)
    elif sort == "asc":
        result = sort_students_by_gpa(result, descending=False)
    return result


@app.post("/students")
def add_student(sv: SinhVien):
    students = doc_json()
    sv_dict = sv.model_dump()

    loi = kiem_tra_sinh_vien(sv_dict, students)
    if loi:
        raise HTTPException(status_code=400, detail=" | ".join(loi))

    sv_chuan = tinh_diem_sinh_vien(chuan_hoa_sinh_vien(sv_dict))
    students.append(sv_chuan)

    if not ghi_json(students):
        raise HTTPException(status_code=500, detail="Không thể ghi dữ liệu ra file JSON.")
    return {"message": "Thêm sinh viên thành công", "data": sv_chuan}


@app.delete("/students/{ma_sv}")
def delete_student(ma_sv: str):
    students = doc_json()
    new_list = [sv for sv in students if sv["ma_sv"].strip().lower() != ma_sv.strip().lower()]
    if len(new_list) == len(students):
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên để xóa")

    if not ghi_json(new_list):
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật file JSON.")
    return {"message": f"Đã xóa sinh viên {ma_sv}"}


@app.get("/statistics")
def get_stats():
    return get_gpa_statistics(doc_json())