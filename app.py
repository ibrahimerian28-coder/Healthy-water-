import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. كود التنسيق الاحترافي (CSS) ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}

    /* تنسيق الأزرار المربعة */
    div.stButton > button {
        width: 100%;
        height: 120px;
        background-color: #ffffff;
        color: #004a99;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        font-size: 18px !important;
        font-weight: bold;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    div.stButton > button:hover {
        border: 1px solid #004a99;
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. بيانات الربط المباشر ---
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

# --- 4. إدارة الصفحات (Navigation) ---
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# --- 5. الهيدر (اللوجو أقصى اليسار) ---
col_l, _ = st.columns([1, 4])
with col_l:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)

# --- 6. عرض الصفحات ---

# --- صفحة الرئيسية (Home) ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666;'>الرئيسية</h4>", unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 2]) # عمودين للأزرار وباقي الصفحة فاضي لليسار
    
    with col1:
        if st.button("🔍\nالبحث"):
            st.session_state.page = 'search'
            st.rerun()
        if st.button("➕\nإضافة عميل"):
            st.session_state.page = 'add_customer'
            st.rerun()
            
    with col2:
        if st.button("📋\nالمواعيد"):
            st.session_state.page = 'schedule'
            st.rerun()
        if st.button("🔧\nسجل صيانة"):
            st.session_state.page = 'add_maint'
            st.rerun()

# --- صفحة البحث وإدارة العملاء ---
elif st.session_state.page == 'search':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.subheader("🔍 بحث وإدارة العملاء")
    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)

    if not df_customers.empty:
        search = st.text_input("ابحث بالاسم أو الرقم")
        if search:
            df_customers = df_customers[df_customers.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for _, row in df_customers.iterrows():
            name = str(row.get('الاسم', '---')).strip()
            with st.expander(f"👤 {name} | 📍 {row.get('المنطقة', '---')}"):
                st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                # كود عرض السجل والجدول (✅/❌) اللي عملناه قبل كدة بيتحط هنا
                st.info("بيانات العميل وجدول صيانته تظهر هنا")

# --- صفحة تسجيل عميل جديد ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.subheader("➕ تسجيل بيانات عميل جديد")
    with st.form("new_cust"):
        n_name = st.text_input("الاسم")
        n_phone = st.text_input("الأرقام")
        n_area = st.selectbox("المنطقة", ["حدائق العاصمة", "مدينتي", "الشروق", "بدر", "أخرى"])
        n_cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        if st.form_submit_button("تجهيز السطر"):
            st.code(f"{n_name} | {n_phone} | {n_area} | {n_cycle}")

# --- صفحة إضافة سجل صيانة ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.subheader("🔧 إضافة سجل صيانة (زيارة)")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        with st.form("maint"):
            m_name = st.selectbox("اختر العميل", df_customers['الاسم'].tolist())
            m_date = st.date_input("التاريخ", datetime.now())
            p1 = st.checkbox("P1")
            p2 = st.checkbox("P2")
            p3 = st.checkbox("P3")
            if st.form_submit_button("تجهيز سطر الصيانة"):
                st.success("تم التجهيز للنسخ")

# --- صفحة جدول المواعيد ---
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.subheader("📋 مواعيد الصيانة القادمة")
    st.write("العملاء المطلوب زيارتهم هذا الأسبوع يظهرون هنا.")
