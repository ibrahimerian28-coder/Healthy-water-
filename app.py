import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import uuid

# --- الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# الرابط الجديد اللي إنت لسه عامله
API_URL = "https://api.steinhq.com/v1/storages/69e9cdbc92b1163e973e0f5e"

# دالة ذكية لإرسال البيانات
def send_to_stein(sheet, data):
    try:
        response = requests.post(f"{API_URL}/{sheet}", json=data, timeout=15)
        return response
    except Exception as e:
        return str(e)

# --- واجهة التطبيق ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["➕ إضافة عميل", "🛠️ سجل صيانة", "🔍 عرض البيانات"])

if menu == "➕ إضافة عميل":
    st.header("📝 تسجيل عميل جديد")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        area = st.text_input("المنطقة")
        address = st.text_input("العنوان بالتفصيل")
        location = st.text_input("رابط الخريطة")
        phones = st.text_area("الأرقام (كل رقم في سطر)")
        
        if st.form_submit_button("✅ حفظ البيانات"):
            if name and phones:
                # تجهيز البيانات بالظبط زي العناوين اللي في الشيت عندك
                payload = [{
                    "id": str(uuid.uuid4())[:8],
                    "name": name,
                    "phones_json": phones,
                    "address": address,
                    "area": area,
                    "location": location,
                    "install_date": str(datetime.now().date())
                }]
                
                res = send_to_stein("Data", payload)
                
                if hasattr(res, 'status_code') and res.status_code == 200:
                    st.success("أيوة كدة! السيرفر اتصالح والبيانات اتحفظت 🎈")
                    st.balloons()
                else:
                    st.error(f"لسه مقموص برضه! الرد: {res.text if hasattr(res, 'text') else res}")
            else:
                st.warning("لازم تكتب الاسم ورقم التليفون يا هندسة!")

elif menu == "🛠️ سجل صيانة":
    st.info("سجل عميل الأول عشان نتأكد إن السيرفر فك القمصة!")

elif menu == "🔍 عرض البيانات":
    st.subheader("📊 البيانات الحالية في الشيت")
    try:
        res = requests.get(f"{API_URL}/Data")
        if res.status_code == 200:
            st.write(res.json())
        else:
            st.error("مش عارف يقرأ البيانات")
    except:
        st.error("خطأ في الاتصال")
