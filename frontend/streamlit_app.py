import datetime as dt
import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


@st.cache_data(ttl=30)
def get_categories():
    try:
        resp = requests.get(f"{API_BASE}/categories", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


@st.cache_data(ttl=5)
def get_transactions():
    try:
        resp = requests.get(f"{API_BASE}/transactions", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Không lấy được danh sách giao dịch: {exc}")
        return []


def cat_name(categories, cat_id):
    for c in categories:
        if c["id"] == cat_id:
            return c["name"]
    return "—"


st.set_page_config(page_title="Quản lý Chi tiêu", page_icon="💰", layout="wide")
st.title("💰 Quản lý Chi tiêu")

categories = get_categories()

with st.sidebar:
    st.header("Cài đặt")
    st.text_input("API Base URL", value=API_BASE, key="api_base", disabled=True)
    method = st.selectbox("Phương pháp dự báo", ["linear", "seasonal", "arima"])

tab_input, tab_list = st.tabs(["➕ Nhập giao dịch", "📋 Danh sách"])

with tab_input:
    st.subheader("Thêm giao dịch mới")
    with st.form("new_transaction", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Số tiền (VND)", min_value=0.0, step=1000.0)
            date_val = st.date_input("Ngày", value=dt.date.today())
        with col2:
            cat_options = {c["name"]: c["id"] for c in categories}
            cat_options = {"(Tự động phân loại)": None, **cat_options}
            selected_cat = st.selectbox("Danh mục", list(cat_options.keys()))
            note = st.text_input("Ghi chú", placeholder="VD: Ăn trưa, taxi, mua sắm...")

        submitted = st.form_submit_button("Thêm giao dịch", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.warning("Số tiền phải lớn hơn 0")
            else:
                payload = {
                    "amount": float(amount),
                    "note": note,
                    "date": str(date_val),
                    "category_id": cat_options[selected_cat],
                }
                try:
                    resp = requests.post(f"{API_BASE}/transactions", json=payload, timeout=5)
                    resp.raise_for_status()
                    st.success("Đã thêm giao dịch!")
                    get_transactions.clear()
                    get_categories.clear()
                except Exception as exc:
                    st.error(f"Thêm thất bại: {exc}")

with tab_list:
    st.subheader("Danh sách giao dịch")
    if st.button("🔄 Làm mới"):
        get_transactions.clear()

    transactions = get_transactions()
    if not transactions:
        st.info("Chưa có giao dịch nào.")
    else:
        rows = []
        total = 0.0
        for t in sorted(transactions, key=lambda x: str(x.get("date", "")), reverse=True):
            amt = float(t.get("amount", 0))
            total += amt
            rows.append(
                {
                    "ID": t.get("id"),
                    "Ngày": t.get("date"),
                    "Số tiền": f"{amt:,.0f}",
                    "Danh mục": cat_name(categories, t.get("category_id")),
                    "Ghi chú": t.get("note", ""),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.metric("Tổng chi tiêu", f"{total:,.0f} VND", f"{len(rows)} giao dịch")
