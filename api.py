from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import json
import os
from analytics import search_students, sort_students_by_gpa, get_gpa_statistics

app = FastAPI(title="API Quản lý Kết quả Học tập - Nhóm Bá Khí")
DATA_FILE = "data/students.json"


# --- RÀNG BUỘC DỮ LIỆU ĐẦU VÀO (VALIDATION) ---
class MonHoc(BaseModel):
    ten_mon: str
    diem_1: float = Field(..., ge=0.0, le=10.0)
    diem_2: float = Field(..., ge=0.0, le=10.0)
    diem_tong_ket: float = Field(..., ge=0.0, le=10.0)


class SinhVien(BaseModel):
    ma_sv: str
    ho_ten: str
    mon_hoc: List[MonHoc]
    gpa: float = Field(..., ge=0.0, le=10.0)


def read_json() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: list):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/students")
def get_all_students(keyword: str = "", sort: str = "default"):
    students = read_json()
    result = search_students(students, keyword)
    if sort == "desc":
        result = sort_students_by_gpa(result, descending=True)
    elif sort == "asc":
        result = sort_students_by_gpa(result, descending=False)
    return result


@app.post("/students")
def add_student(sv: SinhVien):
    students = read_json()
    if any(item["ma_sv"].lower() == sv.ma_sv.strip().lower() for item in students):
        raise HTTPException(status_code=400, detail=f"Mã sinh viên '{sv.ma_sv}' đã tồn tại!")
    students.append(sv.model_dump())
    write_json(students)
    return {"message": "Thêm sinh viên thành công", "data": sv}


@app.delete("/students/{ma_sv}")
def delete_student(ma_sv: str):
    students = read_json()
    new_list = [sv for sv in students if sv["ma_sv"].lower() != ma_sv.lower()]
    if len(new_list) == len(students):
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên để xóa")
    write_json(new_list)
    return {"message": f"Đã xóa sinh viên {ma_sv}"}


@app.get("/statistics")
def get_stats():
    return get_gpa_statistics(read_json())