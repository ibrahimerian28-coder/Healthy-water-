import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", page_icon="💧", layout="wide")

# الرابط الجديد اللي إنت بعته (العهدة عليّ أهو 😅)
API_URL = "https://api.steinhq.com/v1/storages/69e917683807a370b05f56051"
# اسم الصفحة اللي اتفقنا عليها
SHEET_NAME = "Data"

# --- 2. دالة جلب البيانات ---
def load_data():
    try:
        res = requests.get(f"{API_URL}/{SHEET_NAME}", timeout=15)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_customers = load_data()

# --- 3. واجهة التطبيق ---
st.title("💧 نظام إدارة العملاء")
menu = st.sidebar.radio("القائمة", ["إضافة عميل جديد", "عرض قائمة العملاء"])

# --- 4. إضافة عميل جديد ---
if menu == "إضافة عميل جديد":
    st.subheader("📝 تسجيل بيانات العميل")
    with st.form("main_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ في صفحة Data"):
            if name and phone:
                # البيانات هتروح للعناوين اللي عملناها (name, phone, area)
                payload = [{
                    "name": name, 
                    "phone": phone, 
                    "area": area,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }]
                try:
                    resp = requests.post(f"{API_URL}/{SHEET_NAME}", json=payload, timeout=20)
                    if resp.status_code == 200:
                        st.success(f"ألف مبروك يا هندسة! {name} اتسجل بنجاح واللينك شغال.")
                        st.balloons()
                    else:
                        st.error(f"السيرفر رد بحاجة غريبة: {resp.text}")
                except Exception as e:
                    st.error(f"حصلت مشكلة في الطريق: {str(e)}")
            else:
                st.warning("دخل الاسم والرقم عشان السيستم يرضى عننا.")

# --- 5. عرض العملاء ---
else:
    st.subheader("👥 العملاء المسجلين")
    if st.button("🔄 تحديث"):
        st.rerun()
        
    if df_customers.empty:
        st.info("لسه مفيش بيانات ظهرت.. سجل أول عميل وجرب.")
    else:
        search = st.text_input("🔍 بحث")
        display_df = df_customers.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search in str(r.values), axis=1)]
        
        st.dataframe(display_df, use_container_width=True)
