import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"

# --- 2. وظيفة جلب البيانات (بدون تحديد صفحة لضمان الرد) ---
def load_data():
    try:
        # بنكلم الرابط الأساسي وهو بيدينا أول داتا يلاقيها
        res = requests.get(API_URL, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # لو الرد عبارة عن قائمة صفحات، بنحاول نجيب صفحة Customers
            if isinstance(data, dict):
                res = requests.get(f"{API_URL}/Customers")
                data = res.json()
            return pd.DataFrame(data)
    except:
        pass
    return pd.DataFrame()

df_c = load_data()

# --- 3. الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

# --- 5. تسجيل عميل جديد (بدون تحديد Range) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("ultra_final"):
        name = st.text_input("الاسم")
        phone = st.text_input("الهاتف")
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                payload = [{"اسم العميل": name, "الأرقام": phone, "التاريخ": str(datetime.now())}]
                # بنبعت للرابط المباشر بدون تحديد /Customers عشان نتفادى خطأ 1:1
                resp = requests.post(API_URL, json=payload)
                if resp.status_code == 200:
                    st.success("تم! شيك على القائمة")
                    st.rerun()
                else:
                    st.error(f"الرد من السيرفر: {resp.text}")

# --- 6. العرض ---
elif menu == "بيانات العملاء":
    st.header("👥 القائمة")
    if df_c.empty:
        st.info("الشيت فاضي أو Stein مش شايف العناوين.")
    else:
        st.dataframe(df_c) # عرض الجدول كما هو للتأكد
