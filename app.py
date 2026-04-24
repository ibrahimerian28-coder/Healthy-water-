import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. كود التنسيق الاحترافي (CSS) ---
st.markdown("""
    <style>
    /* إخفاء القوائم الافتراضية */
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* خلفية بيضاء نظيفة */
    .stApp {
        background-color: #fcfcfc;
    }

    /* محاذاة اللوجو في أقصى اليسار */
    .header-container {
        display: flex;
        justify-content: flex-start;
        padding: 10px;
    }

    /* تنسيق الأزرار لتكون مربعة (Grid) ومحاذاة لليسار */
    div.stButton > button {
        width: 160px;
        height: 140px;
        background-color: #ffffff;
        color: #004a99;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
        font-size: 18px !important;
        font-weight: bold;
        transition: 0.3s;
        margin-bottom: 10px;
    }
    
    div.stButton > button:hover {
        border: 1px solid #004a99;
        box-shadow: 0px 6px 12px rgba(0,74,153,0.15);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. الهيدر (اللوجو) ---
col_l, _ = st.columns([1, 4])
with col_l:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=140)
    else:
        st.write("### Healthy Water")

# --- 4. إدارة الصفحات ---
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# --- 5. الصفحة الرئيسية (Home) ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666; margin-left: 10px;'>الرئيسية</h4>", unsafe_allow_html=True)
    
    # توزيع الأزرار في مربعات جنب بعضها محاذية لليسار
    col1, col2, _ = st.columns([1, 1, 2.5]) # جعل الأعمدة ضيقة ومحاذية لليسار
    
    with col1:
        if st.button("🔍\n\nالبحث"):
            st.session_state.page = 'search'
            st.rerun()
        if st.button("➕\n\nإضافة عميل"):
            st.session_state.page = 'add_customer'
            st.rerun()
            
    with col2:
        if st.button("📋\n\nالمواعيد"):
            st.session_state.page = 'schedule'
            st.rerun()
        if st.button("🔧\n\nسجل صيانة"):
            st.session_state.page = 'add_maint'
            st.rerun()

# --- 6. الصفحات الداخلية ---
else:
    # زرار رجوع شيك ومحاذاة لليسار
    col_back, _ = st.columns([1, 10])
    with col_back:
        if st.button("🔙"):
            st.session_state.page = 'Home'
            st.rerun()
    
    # هنا يوضع الكود الخاص بكل صفحة (نفس الأكواد السابقة للبحث والإضافة)
    if st.session_state.page == 'search':
        st.subheader("🔍 بحث وإدارة العملاء")
    elif st.session_state.page == 'add_customer':
        st.subheader("➕ تسجيل عميل جديد")
    elif st.session_state.page == 'schedule':
        st.subheader("📋 جدول صيانة الأسبوع")
    elif st.session_state.page == 'add_maint':
        st.subheader("🔧 إضافة سجل صيانة")
