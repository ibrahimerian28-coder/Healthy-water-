import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Healthy Water", layout="wide", page_icon="💧")

# إخفاء القائمة الجانبية والقوائم الافتراضية لتعزيز الشكل الاحترافي
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- بيانات الربط ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 2. تصميم الواجهة الرئيسية (اللوجو والقائمة) ---
col_logo, col_empty = st.columns([1, 3])

with col_logo:
    # التأكد من وجود ملف اللوجو
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        st.title("💧 Healthy Water")

# إنشاء القائمة كأزرار في الصفحة الرئيسية
st.markdown("### القائمة الرئيسية")
selected_menu = st.radio("", ["🔍 بحث وإدارة العملاء", "📋 جدول صيانة الأسبوع", "➕ تسجيل عميل جديد", "🔧 إضافة سجل صيانة"], label_visibility="collapsed")

st.markdown("---")

# --- 3. محتوى الصفحات ---

if selected_menu == "🔍 بحث وإدارة العملاء":
    st.subheader("🔍 بحث وإدارة العملاء")
    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)

    if not df_customers.empty:
        search = st.text_input("ابحث بالاسم أو الرقم")
        if search:
            df_customers = df_customers[df_customers.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for _, row in df_customers.iterrows():
            name = str(row.get('الاسم', '---')).strip()
            area = row.get('المنطقة', '---')
            with st.expander(f"👤 {name} | 📍 {area}"):
                # (هنا نضع نفس كود عرض بيانات العميل والجداول اللي عملناه المرة اللي فاتت)
                st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                # ... بقية الكود

elif selected_menu == "📋 جدول صيانة الأسبوع":
    st.subheader("🗓️ جدول صيانة الأسبوع")
    st.info("سيتم عرض المواعيد القادمة هنا تلقائياً.")

elif selected_menu == "➕ تسجيل عميل جديد":
    st.subheader("➕ تسجيل عميل جديد")
    with st.form("new_customer"):
        n_name = st.text_input("الاسم بالكامل")
        # ... بقية خانات النموذج
        if st.form_submit_button("عرض السطر للنسخ"):
            st.success("تم تجهيز البيانات")

elif selected_menu == "🔧 إضافة سجل صيانة":
    st.subheader("🔧 إضافة سجل صيانة")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        with st.form("maint_entry"):
            m_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
            # ... بقية خانات سجل الصيانة
            if st.form_submit_button("تجهيز السطر"):
                st.success("جاهز للنسخ")
