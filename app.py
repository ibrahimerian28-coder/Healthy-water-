import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Healthy Water", layout="wide", page_icon="💧")

# كود CSS لتنسيق الأزرار واللوجو والواجهة
st.markdown("""
    <style>
    /* إخفاء القوائم الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* تنسيق الحاوية الرئيسية */
    .main {
        background-color: #ffffff;
    }

    /* تنسيق اللوجو في أقصى اليسار */
    .logo-container {
        position: absolute;
        top: -50px;
        left: -20px;
        z-index: 100;
    }

    /* تنسيق الأزرار لتكون كبيرة وفي المنتصف */
    div.stButton > button {
        width: 100%;
        height: 80px;
        font-size: 24px !important;
        font-weight: bold;
        color: #004a99;
        background-color: #ffffff;
        border: 2px solid #004a99;
        border-radius: 15px;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #004a99;
        color: #ffffff;
        border: 2px solid #004a99;
    }

    /* إخفاء النقطة الحمراء بتاعة الراديو */
    [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة (Navigation) ---
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# وظيفة لتغيير الصفحة
def move_to(page_name):
    st.session_state.page = page_name

# --- 3. عرض اللوجو (أقصى اليسار) ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=180)
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. محتوى الصفحات ---

# صفحة Home (الأزرار الكبيرة)
if st.session_state.page == 'Home':
    st.write("<br><br><br>", unsafe_allow_html=True) # مسافة للأسفل
    
    # توزيع الأزرار في المنتصف
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #004a99;'>القائمة الرئيسية</h1><br>", unsafe_allow_html=True)
        
        if st.button("🔍 بحث وإدارة العملاء"):
            move_to('search')
            st.rerun()
            
        if st.button("📋 جدول صيانة الأسبوع"):
            move_to('schedule')
            st.rerun()
            
        if st.button("➕ تسجيل عميل جديد"):
            move_to('add_customer')
            st.rerun()
            
        if st.button("🔧 إضافة سجل صيانة"):
            move_to('add_maint')
            st.rerun()

# صفحة البحث (تظهر فقط بعد الضغط على الزر)
elif st.session_state.page == 'search':
    if st.button("⬅️ العودة للرئيسية"):
        move_to('Home')
        st.rerun()
    st.header("🔍 بحث وإدارة العملاء")
    # هنا يوضع كود البحث اللي عملناه قبل كدة...

elif st.session_state.page == 'schedule':
    if st.button("⬅️ العودة للرئيسية"):
        move_to('Home')
        st.rerun()
    st.header("📋 جدول صيانة الأسبوع")

elif st.session_state.page == 'add_customer':
    if st.button("⬅️ العودة للرئيسية"):
        move_to('Home')
        st.rerun()
    st.header("➕ تسجيل عميل جديد")

elif st.session_state.page == 'add_maint':
    if st.button("⬅️ العودة للرئيسية"):
        move_to('Home')
        st.rerun()
    st.header("🔧 إضافة سجل صيانة")
