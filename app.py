import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. كود التنسيق (CSS) - تحويل الأزرار لصفوف مستطيلة واضحة ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}
    
    /* تنسيق الأزرار لتكون مستطيلة وتحت بعضها (صفوف) */
    div.stButton > button {
        width: 100%;
        height: 80px !important; /* شكل مستطيل */
        background-color: #ffffff;
        color: #004a99;
        border: 2px solid #004a99;
        border-radius: 12px;
        font-size: 22px !important; /* خط واضح وكبير */
        font-weight: bold;
        margin-bottom: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    div.stButton > button:hover {
        background-color: #f0f7ff;
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
        # تنظيف خانة التكلفة من الأصفار الزائدة وتحويلها لأرقام صحيحة
        if 'التكلفه' in df.columns:
            df['التكلفه'] = pd.to_numeric(df['التكلفه'], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

# --- 4. إدارة الصفحات ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 5. الهيدر (حل مشكلة اللوجو والبكسلة) ---
if os.path.exists("logo.png"):
    # عرض اللوجو بالطريقة الرسمية وبحجم متوازن لمنع البكسلة
    st.image("logo.png", width=200)

# --- 6. عرض المحتوى ---

# --- صفحة الرئيسية ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666; text-align: center;'>الرئيسية - Healthy Water</h4>", unsafe_allow_html=True)
    
    # أزرار في صفوف تحت بعضها بخط واضح
    if st.button("🔍 البحث في العملاء"):
        st.session_state.page = 'search'
        st.rerun()
    if st.button("➕ إضافة عميل جديد"):
        st.session_state.page = 'add_customer'
        st.rerun()
    if st.button("📋 جدول المواعيد"):
        st.session_state.page = 'schedule'
        st.rerun()
    if st.button("🔧 تسجيل صيانة"):
        st.session_state.page = 'add_maint'
        st.rerun()

# --- صفحة البحث وإدارة العملاء ---
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
                c1, c2 = st.columns(2)
                with c1:
                    phone = str(row.get('الأرقام', ''))
                    st.write(f"📞 **الأرقام:**")
                    # إمكانية الضغط للاتصال أو واتساب
                    if phone != '':
                        st.markdown(f'<a href="tel:{phone}" style="text-decoration:none; color:green; font-size:18px;">📞 اتصال مباشر</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="https://wa.me/{phone}" style="text-decoration:none; color:#25D366; font-size:18px;">💬 واتساب</a>', unsafe_allow_html=True)
                    else:
                        st.write("---")
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
                        
                        # تنظيف أرقام التكلفة في سجل الصيانة
                        if 'التكلفه' in cust_maint.columns:
                            cust_maint['التكلفه'] = pd.to_numeric(cust_maint['التكلفه'], errors='coerce').fillna(0).astype(int)
                        
                        shama3at = ['P1','P2','P3','ممبرين','بوست كاربون','كالسيت','انفرا ريد']
                        for col in shama3at:
                            if col in cust_maint.columns:
                                cust_maint[col] = cust_maint[col].apply(lambda x: "✅" if str(x).strip() == "تم" else "❌")
                        
                        cols = ['تاريخ الزيارة'] + shama3at + ['اخري', 'التكلفه', 'ملاحظات', 'تاريخ تذكير خاص']
                        available = [c for c in cols if c in cust_maint.columns]
                        st.table(cust_maint[available])

# --- صفحة تسجيل عميل جديد ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ تسجيل عميل جديد")
    with st.form("new_customer_form"):
        f1, f2 = st.columns(2)
        with f1:
            n_name = st.text_input("الاسم بالكامل")
            n_phone = st.text_input("أرقام الهاتف")
        with f2:
            n_area = st.text_input("المنطقة")
            n_cycle = st.number_input("دورة الصيانة", value=3)
        if st.form_submit_button("حفظ"):
            st.success("تم التجهيز")

# --- صفحة إضافة سجل صيانة ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 إضافة سجل صيانة")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        with st.form("maint_form"):
            m_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
            m_date = st.date_input("تاريخ الزيارة")
            m_cost = st.number_input("التكلفة (أرقام صحيحة)", step=1, format="%d")
            if st.form_submit_button("تجهيز الزيارة"):
                st.success("جاهز")
