import streamlit as st
import pandas as pd
from datetime import datetime
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
    
    /* تنسيق الأزرار المستطيلة الواضحة */
    div.stButton > button {
        width: 100%;
        height: 65px !important;
        background-color: #ffffff;
        color: #004a99;
        border: 2px solid #004a99;
        border-radius: 10px;
        font-size: 18px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    div.stButton > button:hover {background-color: #f0f7ff;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. وظائف التصدير (Export) ---

def to_excel(cust_row, maint_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame([cust_row]).to_excel(writer, sheet_name='Customer_Info', index=False)
        if not maint_df.empty:
            maint_df.to_excel(writer, sheet_name='Maint_History', index=False)
    return output.getvalue()

def create_pdf(name, phones, area, maint_history):
    pdf = FPDF()
    pdf.add_page()
    
    # اللوجو أعلى اليسار (لو الملف موجود)
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 30)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.ln(20)
    pdf.cell(0, 10, f"Customer: {name}", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Phones: {phones}", ln=True)
    pdf.cell(0, 10, f"Area: {area}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 0, "", "T", ln=True) # خط فاصـل
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Last Maintenance Records:", ln=True)
    
    pdf.set_font("Arial", '', 10)
    if not maint_history.empty:
        for _, r in maint_history.head(15).iterrows():
            date_str = str(r.get('تاريخ الزيارة', ''))[:10]
            cost = r.get('التكلفه', 0)
            pdf.cell(0, 8, f"- {date_str} | Cost: {cost} EGP", ln=True)

    # الفوتر الثابت
    pdf.set_y(-25)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Contact: 01286609535 | WhatsApp & Call", align='C', ln=True)
    
    return pdf.output()

# --- 4. جلب البيانات ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        if 'التكلفه' in df.columns:
            df['التكلفه'] = pd.to_numeric(df['التكلفه'], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

# --- 5. الهيدر (اللوجو) ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=180) # حجم يمنع البكسلة

# --- 6. الصفحات ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

if st.session_state.page == 'Home':
    st.markdown("<h4 style='color: #666; text-align: center;'>الرئيسية</h4>", unsafe_allow_html=True)
    if st.button("🔍 البحث"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()

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
            with st.expander(f"👤 {name} | {row.get('المنطقة', '')}"):
                # عرض الأرقام والاتصال
                raw_phones = str(row.get('الأرقام', ''))
                phones_list = re.split(r'[ ,/-]+', raw_phones)
                for p in phones_list:
                    p = p.strip()
                    if len(p) > 5:
                        st.markdown(f'📞 <a href="tel:{p}">{p}</a> | <a href="https://wa.me/{p}">💬 WhatsApp</a>', unsafe_allow_html=True)
                
                st.write(f"🏠 العنوان: {row.get('العنوان', '---')}")
                
                # عرض سجل الصيانة
                st.markdown("---")
                cust_maint = pd.DataFrame()
                if not df_maint.empty:
                    cust_maint = df_maint[df_maint['الاسم'].astype(str).str.strip() == name].copy()
                    if not cust_maint.empty:
                        st.write("📜 الصيانات السابقة:")
                        st.table(cust_maint.head(5))

                # --- منطقة الـ Export ---
                st.write("📥 استخراج تقرير:")
                ex_c1, ex_c2 = st.columns(2)
                with ex_c1:
                    exc_file = to_excel(row.to_dict(), cust_maint)
                    st.download_button("📊 Excel", exc_file, f"{name}.xlsx", key=f"ex_{name}")
                with ex_c2:
                    pdf_file = create_pdf(name, raw_phones, row.get('المنطقة', ''), cust_maint)
                    st.download_button("📄 PDF", pdf_file, f"{name}.pdf", key=f"pdf_{name}")

# (صفحات إضافة عميل وصيانة تظل كما هي بكل خاناتها)
elif st.session_state.page == 'add_customer':
    if st.button("🔙"): st.session_state.page = 'Home'; st.rerun()
    with st.form("add"):
        n1, n2 = st.columns(2)
        name_in = n1.text_input("الاسم")
        phone_in = n1.text_input("الأرقام")
        area_in = n1.text_input("المنطقة")
        addr_in = n2.text_area("العنوان")
        inst_in = n2.date_input("التركيب")
        cycl_in = n2.number_input("الدورة", 3)
        loc_in = st.text_input("اللوكيشن")
        if st.form_submit_button("تجهيز"): st.success("جاهز")

elif st.session_state.page == 'add_maint':
    if st.button("🔙"): st.session_state.page = 'Home'; st.rerun()
    df_c = load_data(DATA_GID)
    with st.form("maint"):
        m_name = st.selectbox("الاسم", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("الاسم")
        m_date = st.date_input("التاريخ")
        c1, c2, c3 = st.columns(3)
        p1, p2, p3 = c1.checkbox("P1"), c1.checkbox("P2"), c1.checkbox("P3")
        mem, post, calc = c2.checkbox("ممبرين"), c2.checkbox("بوست"), c2.checkbox("كالسيت")
        infra = c3.checkbox("انفرا")
        cost_in = st.number_input("التكلفة", step=1)
        if st.form_submit_button("حفظ"): st.success("تم")
