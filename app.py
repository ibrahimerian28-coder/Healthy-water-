import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط بتاعك
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"

# --- 2. وظيفة جلب البيانات ---
def load_data():
    try:
        # لازم نحدد اسم التبويب "Customers" هنا عشان ميطلعش Error
        res = requests.get(f"{API_URL}/Customers", timeout=15)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data()

# --- 3. تسجيل عميل جديد ---
if 'role' not in st.session_state: st.session_state.role = "admin" # دخول مباشر للتجربة

menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("retry_form"):
        name = st.text_input("الاسم")
        phone = st.text_input("الهاتف")
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # payload بسيط جداً
                payload = [{"اسم العميل": name, "الأرقام": phone}]
                try:
                    # ركز في السطر ده: ضفنا /Customers للرابط
                    resp = requests.post(f"{API_URL}/Customers", json=payload, timeout=20)
                    if resp.status_code == 200:
                        st.success("البيانات وصلت للشيت أخييراً!")
                        st.balloons()
                    else:
                        st.error(f"السيرفر لسه معصلج: {resp.text}")
                except Exception as e:
                    st.error(f"عطل فني: {str(e)}")

elif menu == "بيانات العملاء":
    st.header("👥 القائمة")
    if df_c.empty:
        st.info("مفيش بيانات.. تأكد إن صفحة Customers هي أول صفحة في الإكسيل.")
    else:
        st.write(df_c)
