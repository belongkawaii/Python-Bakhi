def search_students(students: list, keyword: str) -> list:
    """Tìm kiếm sinh viên theo MSSV hoặc Họ tên (không phân biệt hoa thường)."""
    kw = keyword.strip().lower()
    if not kw:
        return students
    return [
        sv for sv in students
        if kw in sv.get("ma_sv", "").lower() or kw in sv.get("ho_ten", "").lower()
    ]


def sort_students_by_gpa(students: list, descending: bool = True) -> list:
    """Sắp xếp danh sách sinh viên theo GPA."""
    return sorted(students, key=lambda sv: sv.get("gpa", 0.0), reverse=descending)


def get_gpa_statistics(students: list) -> dict:
    """Thống kê GPA cao nhất, thấp nhất và trung bình của nhóm."""
    if not students:
        return {"max_sv": None, "min_sv": None, "avg_gpa": 0.0}

    max_sv = max(students, key=lambda sv: sv.get("gpa", 0.0))
    min_sv = min(students, key=lambda sv: sv.get("gpa", 0.0))
    avg_gpa = round(sum(sv.get("gpa", 0.0) for sv in students) / len(students), 2)

    return {
        "max_sv": max_sv,
        "min_sv": min_sv,
        "avg_gpa": avg_gpa
    }