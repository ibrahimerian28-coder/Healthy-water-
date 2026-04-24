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

# --- 3. وظيفة إنشاء الـ PDF المطورة ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 45) # حجم اللوجو كبير وواضح
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Maintenance Report', 0, 0, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'B', 14) # خط الفوتر كبير وواضح
        self.set_text_color(0, 74, 153)
        self.cell(0, 10, 'Contact: 01286609535 | Healthy Water - Quality First', 0, 0, 'C')

def create_pdf_bytes(cust_row, maint_df):
    pdf = PDF()
    pdf.add_page()
    
    # بيانات العميل
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Customer Name: {cust_row.get('الاسم', 'N/A')}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Phone: {cust_row.get('الأرقام', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Area: {cust_row.get('المنطقة', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Address: {cust_row.get('العنوان', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # جدول الصيانات
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Maintenance History:", ln=True)
    pdf.set_font("Arial", 'B', 10)
    
    # رؤوس الجدول
    pdf.cell(30, 8, 'Date', 1)
    pdf.cell(120, 8, 'Services / Filters', 1)
    pdf.cell(35, 8, 'Cost (EGP)', 1)
    pdf.ln()

    pdf.set_font("Arial", '', 9)
    if not maint_df.empty:
        for _, m_row in maint_df.iterrows():
            date_val = str(m_row.get('تاريخ الزيارة', ''))[:10]
            # تجميع الشمعات التي تم تغييرها
            filters = []
            for f in ['P1', 'P2', 'P3', 'ممبرين', 'بوست', 'كالسيت', 'انفرا']:
                if str(m_row.get(f, '')).lower() in ['true', '1', 'checked', 'تم']:
                    filters.append(f)
            
            filter_str = ", ".join(filters) if filters else "General Service"
            cost_val = str(m_row.get('التكلفه', '0')).split('.')[0] # إزالة الأصفار العشرية
            
            pdf.cell(30, 8, date_val, 1)
            pdf.cell(120, 8, filter_str, 1)
            pdf.cell(35, 8, cost_val, 1)
            pdf.ln()
    
    return bytes(pdf.output())

# --- 4. الهيدر وإدارة الصفحات ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=220) # تكبير اللوجو في التطبيق أيضاً

if 'page' not in st.session_state: st.session_state.page = 'Home'

# الصفحة الرئيسية
if st.session_state.page == 'Home':
    st.markdown("<h4 style='text-align: center;'>الرئيسية</h4>", unsafe_allow_html=True)
    if st.button("🔍 البحث في العملاء"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل جديد"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()
    if st.button("📋 جدول المواعيد"): st.session_state.page = 'schedule'; st.rerun()

# صفحة البحث والبيانات
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
                
                if not this_m.empty:
                    # تحويل القيم لـ Checkboxes للعرض
                    display_m = this_m.copy()
                    for f in ['P1', 'P2', 'P3', 'ممبرين', 'بوست', 'كالسيت', 'انفرا']:
                        if f in display_m.columns:
                            display_m[f] = display_m[f].apply(lambda x: "✅ تم" if str(x).lower() in ['true', '1', 'تم'] else "❌")
                    st.table(display_m)
                
                st.write("📥 تصدير التقرير:")
                pdf_btn_data = create_pdf_bytes(row, this_m)
                st.download_button("📄 تحميل تقرير PDF شامل", pdf_btn_data, f"{c_name}.pdf", "application/pdf", key=f"pdf_{c_name}")

# صفحة المواعيد
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("📋 جدول المواعيد")
    df_c = load_data(DATA_GID)
    if not df_c.empty:
        st.dataframe(df_c[['الاسم', 'المنطقة', 'الأرقام', 'دورة الصيانة', 'تاريخ التركيب']])

# صفحة تسجيل صيانة (الخانات الكاملة)
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 تسجيل صيانة")
    df_c = load_data(DATA_GID)
    with st.form("m_form"):
        m_name = st.selectbox("العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("الاسم")
        m_date = st.date_input("التاريخ", datetime.now())
        st.write("الشمعات المستبدلة:")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1")
        p2 = c1.checkbox("P2")
        p3 = c1.checkbox("P3")
        mem = c2.checkbox("ممبرين")
        post = c2.checkbox("بوست")
        calc = c2.checkbox("كالسيت")
        infra = c3.checkbox("انفرا")
        m_other = st.text_input("أخرى")
        m_cost = st.number_input("التكلفة", step=1, value=0)
        m_notes = st.text_area("ملاحظات")
        m_special = st.text_input("تذكير موعد خاص")
        if st.form_submit_button("حفظ الزيارة"):
            st.success(f"تم التجهيز لزيارة {m_name}")

# صفحة إضافة عميل
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ إضافة عميل")
    with st.form("a_form"):
        col_a, col_b = st.columns(2)
        n_name = col_a.text_input("الاسم الثلاثي")
        n_phone = col_a.text_input("الأرقام (يفضل فواصل بينها)")
        n_area = col_a.text_input("المنطقة")
        n_addr = col_b.text_area("العنوان")
        n_inst = col_b.date_input("تاريخ التركيب")
        n_cycle = col_b.number_input("دورة الصيانة (شهور)", 3)
        n_loc = st.text_input("رابط اللوكيشن")
        if st.form_submit_button("حفظ بيانات العميل"):
            st.success("تم التجهيز")
