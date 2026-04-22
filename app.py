import streamlit as st
import pandas as pd
import requests

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", page_icon="💧")

# الرابط المظبوط بالمللي (آخر 6051)
API_URL = "https://api.steinhq.com/v1/storages/69e917683807a370b05f6051"
SHEET_NAME = "Data"

# --- 2. دالة جلب البيانات ---
def load_data():
    try:
        res = requests.get(f"{API_URL}/{SHEET_NAME}", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 3. الواجهة ---
st.title("💧 نظام إدارة العملاء")
menu = st.sidebar.selectbox("القائمة", ["إضافة عميل", "عرض العملاء"])

if menu == "إضافة عميل":
    with st.form("final_rescue"):
        name = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        area = st.text_input("المنطقة")
        if st.form_submit_button("✅ حفظ في Data"):
            if name and phone:
                # العناوين بالإنجليزي name و phone
                payload = [{"name": name, "phone": phone, "area": area}]
                try:
                    resp = requests.post(f"{API_URL}/{SHEET_NAME}", json=payload)
                    if resp.status_code == 200:
                        st.success("أخيراً! البيانات اتحفظت واللينك صح.")
                        st.balloons()
                    else:
                        st.error(f"رد السيرفر: {resp.text}")
                except Exception as e:
                    st.error(f"مشكلة اتصال: {e}")

else:
    df = load_data()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("القائمة فاضية.. سجل أول عميل.")
