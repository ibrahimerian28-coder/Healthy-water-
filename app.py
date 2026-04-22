import streamlit as st
import pandas as pd
import requests

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", page_icon="💧")

# ⚠️ حط هنا الرابط الجديد اللي هيطلعلك بعد ما تمسح الـ API وتعمله تاني
NEW_API_URL = "حط_الرابط_الجديد_هنا" 
# اسم الصفحة في الشيت (تأكد إنها Data)
SHEET_NAME = "Data"

# --- 2. دالة جلب البيانات ---
def get_data():
    try:
        res = requests.get(f"{NEW_API_URL}/{SHEET_NAME}", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 3. الواجهة ---
st.title("💧 نظام إدارة العملاء")
menu = st.sidebar.radio("القائمة", ["إضافة عميل", "عرض العملاء"])

if menu == "إضافة عميل":
    st.subheader("📝 تسجيل جديد")
    with st.form("new_form", clear_on_submit=True):
        name = st.text_input("الاسم")
        phone = st.text_input("الهاتف")
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # بنبعت العناوين بالإنجليزي name و phone
                payload = [{"name": name, "phone": phone}]
                try:
                    resp = requests.post(f"{NEW_API_URL}/{SHEET_NAME}", json=payload)
                    if resp.status_code == 200:
                        st.success("أخيراً! البيانات وصلت للشيت.")
                        st.balloons()
                    else:
                        st.error(f"السيرفر لسه مقمص: {resp.text}")
                except:
                    st.error("مشكلة في الاتصال")
            else:
                st.warning("دخل البيانات")

else:
    st.subheader("👥 قائمة العملاء")
    df = get_data()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("لا توجد بيانات حالياً في صفحة Data.")
