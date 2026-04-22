import streamlit as st
import pandas as pd
import requests

# --- الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", page_icon="💧", layout="wide")

# الرابط "المبروك"
API_URL = "https://api.steinhq.com/v1/storages/69e917683807a370b05f6051"
SHEET_NAME = "Data"

# --- دالة جلب البيانات ---
def load_data():
    try:
        res = requests.get(f"{API_URL}/{SHEET_NAME}", timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- الواجهة ---
st.title("💧 Healthy Water Pro")
menu = st.sidebar.selectbox("القائمة", ["إضافة عميل جديد", "قاعدة البيانات"])

if menu == "إضافة عميل جديد":
    st.subheader("📝 تسجيل عميل")
    with st.form("pro_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        area = st.text_input("المنطقة")
        if st.form_submit_button("✅ حفظ البيانات"):
            if name and phone:
                payload = [{"name": name, "phone": phone, "area": area}]
                resp = requests.post(f"{API_URL}/{SHEET_NAME}", json=payload)
                if resp.status_code == 200:
                    st.success(f"تم تسجيل {name}.. يا ترعة المفهومية!")
                    st.balloons()
                else: st.error("السيرفر رجع يقمص تاني!")

else:
    st.subheader("👥 العملاء المسجلين")
    df = load_data()
    
    if not df.empty:
        # --- ميزة البحث الجديدة ---
        search = st.text_input("🔍 ابحث بالاسم أو الرقم أو المنطقة")
        if search:
            # بيبحث في كل الخانات مرة واحدة
            df = df[df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)]
        
        st.dataframe(df, use_container_width=True)
        st.write(f"إجمالي العملاء: {len(df)}")
    else:
        st.info("لسه مفيش داتا.. ابدأ سجل!")

if st.sidebar.button("🔄 تحديث يدوي"):
    st.rerun()
