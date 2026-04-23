import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import uuid

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# الرابط (2a05)
API_URL = "https://api.steinhq.com/v1/storages/69e9d16c92b1163e973e2a05"

# --- 2. واجهة الإضافة ---
st.header("📝 إضافة عميل جديد")

with st.form("new_cust", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("اسم العميل")
        area = st.text_input("المنطقة")
        address = st.text_input("العنوان")
    with col2:
        phones = st.text_area("الأرقام (كل رقم في سطر)")
        install_date = st.date_input("تاريخ التركيب", datetime.now())

    if st.form_submit_button("✅ حفظ البيانات"):
        if name and phones:
            # تجهيز البيانات
            payload = [{
                "id": str(uuid.uuid4())[:8],
                "name": name,
                "phones_json": phones,
                "address": address,
                "area": area,
                "install_date": str(install_date)
            }]
            
            # محاولة الإرسال
            try:
                res = requests.post(f"{API_URL}/Data", json=payload)
                if res.status_code == 200:
                    st.success("أيوة كدة! كرامتي رجعت والبالونات أهي 🎈🎈🎈")
                    st.balloons()
                else:
                    # لو لسه فيه خطأ، هيعرضهولك بالتفصيل الممل
                    st.error(f"السيرفر بيقول: {res.text}")
                    st.info("تأكد إنك كتبت العناوين في الإكسيل بالظبط: id, name, phones_json, address, area, install_date")
            except Exception as e:
                st.error(f"مشكلة في النت عندك: {e}")
