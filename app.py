import streamlit as st
import pandas as pd
import requests

# --- الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro")
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982/Customers"

# --- جلب البيانات ---
def get_data():
    try:
        res = requests.get(API_URL, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- واجهة التطبيق ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "إضافة عميل"])

if menu == "إضافة عميل":
    st.header("📝 إضافة جديد")
    with st.form("simple_form"):
        u_name = st.text_input("الاسم")
        u_phone = st.text_input("الهاتف")
        if st.form_submit_button("✅ حفظ"):
            if u_name and u_phone:
                # بنبعت العناوين بالإنجليزي عشان Stein ميتلخبطش
                payload = [{"name": u_name, "phone": u_phone}]
                resp = requests.post(API_URL, json=payload)
                if resp.status_code == 200:
                    st.success("أخيراً.. البيانات اتحفظت!")
                    st.balloons()
                else:
                    st.error(f"السيرفر بيقول: {resp.text}")

else:
    st.header("👥 القائمة")
    df = get_data()
    if not df.empty:
        st.write(df)
    else:
        st.info("لا توجد بيانات.. جرب تضيف عميل.")
