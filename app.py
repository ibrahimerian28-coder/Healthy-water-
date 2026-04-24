import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. كود التنسيق السحري (CSS) لإجبار الأزرار تظهر جنب بعض ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}

    /* تنسيق الحاوية للأزرار */
    .main-button-container {
        display: grid;
        grid-template-columns: 1fr 1fr; /* عمودين متساويين */
        gap: 15px; /* مسافة بين الأزرار */
        padding: 10px;
        max-width: 400px; /* عشان ما يفرش بالعرض أوي في الكمبيوتر */
    }

    /* ستايل الزرار المربع */
    div.stButton > button {
        width: 100%;
        height: 140px !important;
        background-color: #ffffff;
        color: #004a99;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        font-size: 18px !important;
        font-weight: bold;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    div.stButton > button:hover {
        border: 2px solid #004a99;
        background-color: #f0f7ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. بيانات الربط (لازم ترجع عشان البيانات تظهر) ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 4. إدارة الصفحات ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 5. الهيدر واللوجو ---
col_logo, _ = st.columns([1, 3])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=140)

# --- 6. عرض المحتوى ---

if st.session_state.page == 'Home':
    st.markdown("<h3 style='color: #444; margin-left: 15px;'>الرئيسية</h3>", unsafe_allow_html=True)
    
    # استخدام Columns لإجبار الأزرار تطلع جنب بعض
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍\nالبحث"): st.session_state.page = 'search'; st.rerun()
        if st.button("➕\nإضافة عميل"): st.session_state.page = 'add_customer'; st.rerun()
    with c2:
        if st.button("📋\nالمواعيد"): st.session_state.page = 'schedule'; st.rerun()
        if st.button("🔧\nسجل صيانة"): st.session_state.page = 'add_maint'; st.rerun()

elif st.session_state.page == 'search':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔍 بحث وإدارة العملاء")
    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)
    
    if not df_customers.empty:
        search = st.text_input("ابحث بالاسم أو الرقم")
        if search:
            df_customers = df_customers[df_customers.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        for _, row in df_customers.iterrows():
            name = str(row.get('الاسم', '---')).strip()
            with st.expander(f"👤 {name}"):
                st.write(f"📍 المنطقة: {row.get('المنطقة', '---')}")
                st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                # هنا بنحط جدول الصيانات ✅/❌ اللي عملناه

elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ تسجيل عميل جديد")
    with st.form("new_c"):
        n_name = st.text_input("الاسم")
        n_area = st.selectbox("المنطقة", ["حدائق العاصمة", "مدينتي", "الشروق", "بدر", "أخرى"])
        if st.form_submit_button("حفظ"): st.success("جاهز للربط!")

elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 إضافة سجل صيانة")
    # كود نموذج الصيانة
