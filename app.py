import streamlit as st
import pandas as pd
from datetime import datetime
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
        width: 100%; height: 60px !important;
        background-color: #ffffff; color: #004a99;
        border: 2px solid #004a99; border-radius: 12px;
        font-size: 18px !important; font-weight: bold;
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

# --- 3. وظيفة الـ PDF المطورة (متوافقة مع الإنجليزية) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 45)
        self.set_font('Arial', 'B', 15)
        self.cell(80); self.cell(30, 10, 'Maintenance Report', 0, 0, 'C')
        self.ln(25)
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 74, 153)
        self.cell(0, 10, 'Contact: 01286609535 | Healthy Water', 0, 0, 'C')

def create_pdf_bytes(cust_row, maint_df):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    
    # دالة لتنظيف النص من أي حروف عربية تسبب Error في الـ PDF
    def clean(t): return str(t).encode('ascii', 'ignore').decode('ascii') if t else ""

    pdf.cell(0, 10, f"Customer: {clean(cust_row.get('الاسم', ''))}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Phone: {clean(cust_row.get('الأرقام', ''))}", ln=True)
    pdf.cell(0, 8, f"Area: {clean(cust_row.get('المنطقة', ''))}", ln=True)
    pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "Maintenance History:", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 8, 'Date', 1); pdf.cell(120, 8, 'Filters Changed', 1); pdf.cell(35, 8, 'Amount', 1)
    pdf.ln()

    pdf.set_font("Arial", '', 9)
    # قائمة الأعمدة الجديدة بالإنجليزي
    filter_cols = ['P1', 'P2', 'P3', 'membrane', 'post carbon', 'Calcite', 'infrared']
    
    if not maint_df.empty:
        for _, m_row in maint_df.iterrows():
            d = str(m_row.get('تاريخ الزيارة', ''))[:10]
            # قراءة التكلفة من العمود الجديد amount
            cost = str(m_row.get('amount', '0')).split('.')[0]
            
            # تجميع الشمعات اللي تم تغييرها
            done = [f for f in filter_cols if str(m_row.get(f, '')).strip().lower() in ['تم', 'true', '1', 'checked']]
            
            pdf.cell(30, 8, d, 1)
            pdf.cell(120, 8, ", ".join(done) if done else "General", 1)
            pdf.cell(35, 8, cost, 1)
            pdf.ln()
    
    return bytes(pdf.output())

# --- 4. إدارة الصفحات ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=220)

if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- الصفحة الرئيسية ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='text-align: center;'>الرئيسية</h4>", unsafe_allow_html=True)
    if st.button("🔍 البحث في العملاء"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل جديد"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()
    if st.button("📋 جدول المواعيد"): st.session_state.page = 'schedule'; st.rerun()

# --- صفحة البحث ---
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
                with col2:
                    st.write(f"🔄 الدورة: كل {row.get('دورة الصيانة', '3')} شهور")

                st.markdown("---")
                st.write("📜 سجل الصيانات:")
                this_m = df_m[df_m['الاسم'].astype(str).str.strip() == c_name].copy() if not df_m.empty else pd.DataFrame()
                
                if not this_m.empty:
                    disp_m = this_m.copy()
                    # تحويل القيم لعلامة صح لكل الأعمدة (العربي والإنجليزي لضمان العمل)
                    f_cols = ['P1','P2','P3','membrane','post carbon','Calcite','infrared','ممبرين','بوست كاربون']
                    for f in f_cols:
                        if f in disp_m.columns:
                            disp_m[f] = disp_m[f].apply(lambda x: "✅" if str(x).strip().lower() in ['تم','true','1'] else "❌")
                    st.table(disp_m)
                
                st.download_button("📄 تحميل تقرير PDF", create_pdf_bytes(row, this_m), f"{c_name}.pdf", key=f"pdf_{c_name}")

# --- صفحة المواعيد ---
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("📋 جدول المواعيد")
    df_c = load_data(DATA_GID)
    if not df_c.empty:
        st.dataframe(df_c)

# --- تسجيل صيانة ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 تسجيل صيانة")
    df_c = load_data(DATA_GID)
    with st.form("m_form"):
        m_name = st.selectbox("العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("الاسم")
        m_date = st.date_input("التاريخ", datetime.now())
        c1, c2, c3 = st.columns(3)
        p1, p2, p3 = c1.checkbox("P1"), c1.checkbox("P2"), c1.checkbox("P3")
        # استخدام الأسماء الجديدة في العرض
        mem = c2.checkbox("Membrane")
        post = c2.checkbox("Post Carbon")
        calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        m_other = st.text_input("Other (أخرى)")
        m_cost = st.number_input("Amount (التكلفة)", step=1)
        m_notes = st.text_area("Notes (ملاحظات)")
        m_remind = st.text_input("Special reminder date")
        if st.form_submit_button("حفظ"): st.success("تم")

# --- إضافة عميل ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ إضافة عميل")
    with st.form("a_form"):
        n_name = st.text_input("الاسم")
        n_phone = st.text_input("الأرقام")
        n_area = st.text_input("المنطقة")
        n_inst = st.date_input("تاريخ التركيب")
        if st.form_submit_button("حفظ"): st.success("تم")
