import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. كود التنسيق (CSS) ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}
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
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    div.stButton > button:hover {
        background-color: #f0f7ff;
        transform: scale(1.02);
        transition: 0.2s;
    }
    .stTable {background-color: white; border-radius: 10px;}
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
    except: return pd.DataFrame()

# --- 4. إدارة الصفحات ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 5. الهيدر ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

# --- 6. عرض المحتوى ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666;'>الرئيسية</h4>", unsafe_allow_html=True)
    grid_col1, grid_col2 = st.columns(2)
    with grid_col1:
        if st.button("🔍\nالبحث"):
            st.session_state.page = 'search'
            st.rerun()
        if st.button("➕\nإضافة عميل"):
            st.session_state.page = 'add_customer'
            st.rerun()
    with grid_col2:
        if st.button("📋\nالمواعيد"):
            st.session_state.page = 'schedule'
            st.rerun()
        if st.button("🔧\nسجل صيانة"):
            st.session_state.page = 'add_maint'
            st.rerun()

elif st.session_state.page == 'search':
    if st.button("🔙"): st.session_state.page = 'Home'; st.rerun()
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
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📞 **الأرقام:** {row.get('الأرقام', '---')}")
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                with c2:
                    st.write(f"🔄 **دورة الصيانة:** كل {row.get('دورة الصيانة', '3')} شهور")
                    loc = row.get('اللوكيشن', '')
                    if pd.notna(loc) and "http" in str(loc):
                        st.markdown(f"[📍 افتح اللوكيشن]({loc})")

                st.markdown("### 📜 سجل الصيانات السابقة")
                if not df_maint.empty:
                    cust_maint = df_maint[df_maint['الاسم'].astype(str).str.strip() == name].copy()
                    if not cust_maint.empty:
                        cust_maint['تاريخ الزيارة'] = pd.to_datetime(cust_maint['تاريخ الزيارة'], errors='coerce')
                        cust_maint = cust_maint.sort_values(by='تاريخ الزيارة', ascending=False)
                        shama3at = ['P1','P2','P3','ممبرين','بوست كاربون','كالسيت','انفرا ريد']
                        for col in shama3at:
                            if col in cust_maint.columns:
                                cust_maint[col] = cust_maint[col].apply(lambda x: "✅" if str(x).strip() == "تم" else "❌")
                        cols = ['تاريخ الزيارة'] + shama3at + ['اخري', 'التكلفه', 'ملاحظات', 'تاريخ تذكير خاص']
                        available = [c for c in cols if c in cust_maint.columns]
                        st.table(cust_maint[available])

elif st.session_state.page == 'add_customer':
    if st.button("🔙"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ تسجيل عميل جديد")
    with st.form("new_customer_form"):
        f1, f2 = st.columns(2)
        with f1:
            n_name = st.text_input("الاسم بالكامل")
            n_phone = st.text_input("أرقام الهاتف")
            n_area = st.text_input("المنطقة")
        with f2:
            n_addr = st.text_area("العنوان بالتفصيل")
            n_inst = st.date_input("تاريخ التركيب")
            n_cycle = st.number_input("دورة الصيانة", value=3)
        n_loc = st.text_input("رابط اللوكيشن")
        if st.form_submit_button("تجهيز البيانات"):
            res = [n_name, n_phone, n_addr, n_area, n_loc, n_inst.strftime('%Y-%m-%d'), n_cycle]
            st.code(" | ".join(map(str, res)))

elif st.session_state.page == 'add_maint':
    if st.button("🔙"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 إضافة سجل صيانة")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        with st.form("maint_form"):
            m_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
            m_date = st.date_input("تاريخ الزيارة")
            c1, c2, c3 = st.columns(3)
            with c1: p1, p2, p3 = st.checkbox("P1"), st.checkbox("P2"), st.checkbox("P3")
            with c2: mem, post, calc = st.checkbox("ممبرين"), st.checkbox("بوست"), st.checkbox("كالسيت")
            with c3: infra = st.checkbox("انفرا ريد")
            m_other = st.text_input("أخرى")
            m_cost = st.number_input("التكلفة")
            m_notes = st.text_area("ملاحظات")
            m_special = st.text_input("تاريخ تذكير خاص")
            if st.form_submit_button("تجهيز الزيارة"):
                st.success("تم التجهيز")
