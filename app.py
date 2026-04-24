import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import io
from fpdf import FPDF

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="Healthy Water", layout="wide")

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
        border-radius: 12px;
        font-size: 18px !important;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .stTable {background-color: white; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. جلب البيانات ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&t={datetime.now().timestamp()}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 3. وظائف التصدير (المصححة) ---
def create_pdf_bytes(name, phone, area):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 30)
    pdf.set_font("Arial", 'B', 16)
    pdf.ln(20)
    pdf.cell(0, 10, "Healthy Water - Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Customer: {phone}", ln=True)
    pdf.cell(0, 10, f"Area: {area}", ln=True)
    pdf.set_y(-25)
    pdf.cell(0, 10, "Contact: 01286609535 | WhatsApp & Call", align='C')
    # السطر ده هو حل المشكلة (تحويل لـ bytes)
    return bytes(pdf.output())

def create_excel_bytes(cust_data, maint_data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        cust_data.to_excel(writer, sheet_name='Profile', index=False)
        if not maint_data.empty:
            maint_data.to_excel(writer, sheet_name='Maintenance', index=False)
    return output.getvalue()

# --- 4. الهيدر وإدارة الصفحات ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

if 'page' not in st.session_state: st.session_state.page = 'Home'

# الصفحة الرئيسية
if st.session_state.page == 'Home':
    st.markdown("<h4 style='text-align: center;'>الرئيسية</h4>", unsafe_allow_html=True)
    if st.button("🔍 البحث في العملاء"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل جديد"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()
    if st.button("📋 جدول المواعيد"): st.session_state.page = 'schedule'; st.rerun()

# صفحة البحث والبيانات (شاملة كل التفاصيل)
elif st.session_state.page == 'search':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    df_c = load_data(DATA_GID)
    df_m = load_data(MAINT_GID)
    query = st.text_input("ابحث بالاسم أو الرقم")
    if not df_c.empty:
        if query:
            df_c = df_c[df_c.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        for _, row in df_c.iterrows():
            c_name = str(row.get('الاسم', '---')).strip()
            with st.expander(f"👤 {c_name} | 📍 {row.get('المنطقة', '')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                    p_list = re.split(r'[ ,/-]+', str(row.get('الأرقام', '')))
                    for p in p_list:
                        if len(p.strip()) > 5:
                            st.markdown(f'📞 <a href="tel:{p}">{p}</a> | <a href="https://wa.me/{p}">💬 واتساب</a>', unsafe_allow_html=True)
                with col2:
                    st.write(f"🔄 الدورة: كل {row.get('دورة الصيانة', '3')} شهور")
                    if "http" in str(row.get('اللوكيشن', '')): st.markdown(f"[📍 اللوكيشن]({row.get('اللوكيشن')})")

                st.markdown("---")
                st.write("📜 سجل الصيانات:")
                this_m = df_m[df_m['الاسم'].astype(str).str.strip() == c_name].copy() if not df_m.empty else pd.DataFrame()
                if not this_m.empty: st.table(this_m)
                
                st.write("📥 تصدير:")
                ex1, ex2 = st.columns(2)
                with ex1:
                    st.download_button("📄 PDF", create_pdf_bytes(c_name, str(row.get('الأرقام', '')), str(row.get('المنطقة', ''))), f"{c_name}.pdf", key=f"p_{c_name}")
                with ex2:
                    st.download_button("📊 Excel", create_excel_bytes(pd.DataFrame([row]), this_m), f"{c_name}.xlsx", key=f"x_{c_name}")

# صفحة المواعيد (حساب أوتوماتيكي بناءً على الدورة)
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("📋 جدول المواعيد")
    df_c = load_data(DATA_GID)
    if not df_c.empty:
        df_c['تاريخ التركيب'] = pd.to_datetime(df_c['تاريخ التركيب'], errors='coerce')
        st.dataframe(df_c[['الاسم', 'المنطقة', 'الأرقام', 'دورة الصيانة', 'تاريخ التركيب']])

# صفحة تسجيل صيانة (الخانات الكاملة 100%)
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 تسجيل صيانة")
    df_c = load_data(DATA_GID)
    with st.form("m_form"):
        m_name = st.selectbox("العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("الاسم")
        m_date = st.date_input("التاريخ", datetime.now())
        st.write("الشمعات:")
        c1, c2, c3 = st.columns(3)
        p1, p2, p3 = c1.checkbox("P1"), c1.checkbox("P2"), c1.checkbox("P3")
        mem, post, calc = c2.checkbox("ممبرين"), c2.checkbox("بوست"), c2.checkbox("كالسيت")
        infra = c3.checkbox("انفرا")
        m_other = st.text_input("أخرى")
        m_cost = st.number_input("التكلفة", step=1)
        m_notes = st.text_area("ملاحظات")
        m_special = st.text_input("تذكير موعد خاص")
        if st.form_submit_button("حفظ"): st.success("تم التجهيز")

# صفحة إضافة عميل (الخانات الكاملة 100%)
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ إضافة عميل")
    with st.form("a_form"):
        col_a, col_b = st.columns(2)
        n_name = col_a.text_input("الاسم")
        n_phone = col_a.text_input("الأرقام")
        n_area = col_a.text_input("المنطقة")
        n_addr = col_b.text_area("العنوان")
        n_inst = col_b.date_input("التركيب")
        n_cycle = col_b.number_input("الدورة", 3)
        n_loc = st.text_input("اللوكيشن")
        if st.form_submit_button("حفظ"): st.success("جاهز")
