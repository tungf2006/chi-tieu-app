import re

def auto_categorize(note: str) -> str:
    """Tự động phân loại giao dịch dựa trên ghi chú."""
    note = note.lower()
    an_uong_patterns = [r"\ban\b", r"cơm|com", r"trà sữa|tra sua", r"cafe"]
    hoc_tap_patterns = [r"sách|sach", r"học phí|hoc phi", r"khóa học|khoa hoc"]
    mua_sam_patterns = [r"quần áo|quan ao", r"giày|giay", r"mua sắm|mua sam"]

    if any(re.search(p, note) for p in an_uong_patterns):
        return "An uong"
    if any(re.search(p, note) for p in hoc_tap_patterns):
        return "Hoc tap"
    if any(re.search(p, note) for p in mua_sam_patterns):
        return "Mua sam"
    return "Khac"