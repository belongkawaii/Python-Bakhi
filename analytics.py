def search_students(students: list, keyword: str) -> list:
    if not keyword or not keyword.strip():
        return students
    kw = keyword.strip().lower()
    return [
        sv for sv in students
        if kw in sv.get("ma_sv", "").lower() or kw in sv.get("ho_ten", "").lower()
    ]


def sort_students_by_gpa(students: list, descending: bool = True) -> list:
    return sorted(
        students,
        key=lambda sv: sv.get("gpa") if sv.get("gpa") is not None else -1.0,
        reverse=descending
    )


def get_gpa_statistics(students: list) -> dict:
    valid_students = [sv for sv in students if sv.get("gpa") is not None]
    if not valid_students:
        return {"avg_gpa": 0.0, "max_sv": None, "min_sv": None}

    avg_gpa = round(sum(sv["gpa"] for sv in valid_students) / len(valid_students), 2)
    max_sv = max(valid_students, key=lambda sv: sv["gpa"])
    min_sv = min(valid_students, key=lambda sv: sv["gpa"])
    return {"avg_gpa": avg_gpa, "max_sv": max_sv, "min_sv": min_sv}