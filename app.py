import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. التنسيق (CSS) لإجبار الأزرار تطلع جنب بعض وتكبير اللوجو ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}

    /* تنسيق الأزرار لتكون مربعات جنب بعضها */
    div.stButton > button {
        width: 100%;
        height: 150px !important;
        background-color: #ffffff;
        color: #004a99;
        border: 2px solid #004a99;
        border-radius: 20px;
        font-size: 20px !important;
        font-weight: bold;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {background-color: #f0f7ff;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. بيانات الربط ---
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

# --- 5. اللوجو (كبير وواضح) ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=250)

# --- 6. عرض المحتوى ---

# --- صفحة الرئيسية (Home) ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666;'>الرئيسية</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2) # تقسيم الشاشة لنصين للأزرار
    with col1:
        if st.button("🔍\nالبحث"): st.session_state.page = 'search'; st.rerun()
        if st.button("➕\nإضافة عميل"): st.session_state.page = 'add_customer'; st.rerun()
    with col2:
        if st.button("📋\nالمواعيد"): st.session_state.page = 'schedule'; st.rerun()
        if st.button("🔧\nسجل صيانة"): st.session_state.page = 'add_maint'; st.rerun()

# --- صفحة البحث وإدارة العملاء (البيانات الكاملة) ---
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
            with st.expander(f"👤 {name} | 📍 {row.get('المنطقة', '---')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📞 **الأرقام:** {row.get('الأرقام', '---')}")
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    st.write(f"📅 **تاريخ التركيب:** {row.get('تاريخ التركيب', '---')}")
                with c2:
                    st.write(f"🔄 **دورة الصيانة:** كل {row.get('دورة الصيانة', '3')} شهور")
                    loc = row.get('اللوكيشن', '')
                    if pd.notna(loc) and "http" in str(loc):
                        st.markdown(f"[📍 افتح اللوكيشن]({loc})")

                # عرض سجل الصيانات كامل
                st.markdown("### 📜 سجل الصيانات السابقة")
                if not df_maint.empty:
                    cust_maint = df_maint[df_maint['الاسم'].astype(str).str.strip() == name].copy()
                    if not cust_maint.empty:
                        # التنبيه بالتذكير الخاص
                        if 'تاريخ تذكير خاص' in cust_maint.columns:
                            special = cust_maint['تاريخ تذكير خاص'].iloc[0]
                            if pd.notna(special) and str(special).strip() != "":
                                st.warning(f"🔔 موعد استثنائي: {special}")
                        
                        shama3at = ['P1','P2','P3','ممبرين','بوست كاربون','كالسيت','انفرا ريد']
                        for col in shama3at:
                            if col in cust_maint.columns:
                                cust_maint[col] = cust_maint[col].apply(lambda x: "✅" if str(x).strip() == "تم" else "❌")
                        
                        cols = ['تاريخ الزيارة'] + shama3at + ['اخري', 'التكلفه', 'ملاحظات']
                        st.table(cust_maint[[c for c in cols if c in cust_maint.columns]])

# --- صفحة تسجيل عميل جديد ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ تسجيل عميل جديد")
    with st.form("new_customer"):
        f1, f2 = st.columns(2)
        with f1:
            n_name = st.text_input("الاسم بالكامل")
            n_phone = st.text_input("أرقام الهاتف")
        with f2:
            n_area = st.text_input("المنطقة")
            n_inst = st.date_input("تاريخ التركيب")
        if st.form_submit_button("تجهيز البيانات"): st.success("تم!")

# --- صفحة إضافة سجل صيانة ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 إضافة سجل صيانة")
    # ... كود نموذج إضافة الصيانة بنفس الترتيب ...
