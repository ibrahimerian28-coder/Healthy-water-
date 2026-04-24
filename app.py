import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import io
from fpdf import FPDF

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
        height: 60px !important;
        background-color: #ffffff;
        color: #004a99;
        border: 2px solid #004a99;
        border-radius: 10px;
        font-size: 18px !important;
        font-weight: bold;
    }
    .stTable {background-color: white; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. جلب البيانات (مع معالجة اختفاء البيانات) ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    # إضافة طابع زمني للرابط لإجبار جوجل على تحديث البيانات
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&t={datetime.now().timestamp()}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        if 'التكلفه' in df.columns:
            df['التكلفه'] = pd.to_numeric(df['التكلفه'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()

# --- 4. وظائف التصدير (PDF & Excel) ---
def create_pdf_report(name_str, phone_str):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 30)
    pdf.set_font("Arial", 'B', 16)
    pdf.ln(20)
    pdf.cell(0, 10, "Maintenance Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Customer: {phone_str}", ln=True) # استخدمنا الرقم لتفادي خطأ اللغة العربية
    pdf.ln(10)
    pdf.set_y(-30)
    pdf.cell(0, 10, "Contact: 01286609535 | WhatsApp & Call", align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- 5. الهيدر ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

# --- 6. إدارة الصفحات ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- الصفحة الرئيسية ---
if st.session_state.page == 'Home':
    st.markdown("<h3 style='text-align: center;'>الرئيسية</h3>", unsafe_allow_html=True)
    if st.button("🔍 البحث في العملاء"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل جديد"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("📋 جدول المواعيد"): st.session_state.page = 'schedule'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()

# --- صفحة البحث والبيانات ---
elif st.session_state.page == 'search':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)
    
    search = st.text_input("ابحث بالاسم أو الرقم")
    if not df_customers.empty:
        if search:
            df_customers = df_customers[df_customers.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)]
        
        for _, row in df_customers.iterrows():
            name = str(row.get('الاسم', '---')).strip()
            with st.expander(f"👤 {name} | 📍 {row.get('المنطقة', '---')}"):
                c1, c2 = st.columns(2)
                with c1:
                    phones = re.split(r'[ ,/-]+', str(row.get('الأرقام', '')))
                    for p in phones:
                        if len(p.strip()) > 5:
                            st.markdown(f'📞 <a href="tel:{p}">اتصال {p}</a> | <a href="https://wa.me/{p}">💬 واتساب</a>', unsafe_allow_html=True)
                    st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                with c2:
                    st.write(f"🔄 الدورة: {row.get('دورة الصيانة', '3')} شهور")
                    loc = row.get('اللوكيشن', '')
                    if "http" in str(loc): st.markdown(f"[📍 اللوكيشن]({loc})")

                # سجل الصيانة للعميل
                st.markdown("---")
                if not df_maint.empty:
                    cust_m = df_maint[df_maint['الاسم'].astype(str).str.strip() == name].copy()
                    if not cust_m.empty:
                        st.write("📜 الصيانات السابقة:")
                        st.table(cust_m.head(10))
                
                # أزرار التصدير
                st.write("📥 تصدير التقرير:")
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    st.download_button("📄 PDF (Basic)", create_pdf_report(name, str(row.get('الأرقام', ''))), f"{name}.pdf", key=f"pdf_{name}")
                with col_ex2:
                    st.button("📊 Excel (قريباً)", key=f"ex_{name}")

# --- صفحة المواعيد (التي كانت مختفية) ---
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("📋 مواعيد الصيانة القادمة")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        st.write("سيتم عرض المواعيد بناءً على تاريخ التركيب ودورة الصيانة هنا.")
        st.dataframe(df_customers[['الاسم', 'المنطقة', 'تاريخ التركيب', 'دورة الصيانة']])

# --- صفحة تسجيل صيانة (الخانات الكاملة) ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 تسجيل صيانة جديدة")
    df_c = load_data(DATA_GID)
    with st.form("maint_form"):
        m_name = st.selectbox("اختر العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("اسم العميل")
        m_date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        with c1: p1, p2, p3 = st.checkbox("P1"), st.checkbox("P2"), st.checkbox("P3")
        with c2: mem, post, calc = st.checkbox("ممبرين"), st.checkbox("بوست"), st.checkbox("كالسيت")
        with c3: infra = st.checkbox("انفرا ريد")
        m_other = st.text_input("أخرى (قطع غيار إضافية)")
        m_cost = st.number_input("التكلفة (أرقام صحيحة)", step=1)
        m_notes = st.text_area("ملاحظات الفني")
        m_special = st.text_input("تاريخ تذكير خاص (مثلاً: 2026-10-01)")
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم التجهيز للنسخ إلى شيت الإكسيل")

# --- صفحة إضافة عميل جديد ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ إضافة عميل جديد")
    with st.form("add_cust"):
        f1, f2 = st.columns(2)
        with f1:
            n_name = st.text_input("الاسم بالكامل")
            n_phone = st.text_input("أرقام الهاتف")
            n_area = st.text_input("المنطقة")
        with f2:
            n_addr = st.text_area("العنوان بالتفصيل")
            n_inst = st.date_input("تاريخ التركيب")
            n_cycle = st.number_input("دورة الصيانة (بالشهور)", value=3)
        n_loc = st.text_input("رابط اللوكيشن (Google Maps)")
        if st.form_submit_button("تجهيز بيانات العميل"):
            st.code(f"{n_name} | {n_phone} | {n_area} | {n_addr} | {n_inst} | {n_cycle}")
