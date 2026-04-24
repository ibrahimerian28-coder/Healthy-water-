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

# --- 2. جلب البيانات من Google Sheets ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    # استخدام Timestamp لتجاوز الكاش وضمان تحديث البيانات
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cache={datetime.now().timestamp()}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 3. وظائف التصدير (PDF & Excel) ---
def create_pdf(name, phones, area):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 30)
    pdf.set_font("Arial", 'B', 16)
    pdf.ln(20)
    pdf.cell(0, 10, "Healthy Water - Customer Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Customer Info: {phones}", ln=True)
    pdf.cell(0, 10, f"Area: {area}", ln=True)
    pdf.ln(10)
    pdf.set_y(-25)
    pdf.cell(0, 10, "Contact us: 01286609535 | WhatsApp & Call", align='C')
    return pdf.output()

def create_excel(cust_data, maint_data):
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

# --- صفحة الرئيسية ---
if st.session_state.page == 'Home':
    st.markdown("<h4 style='text-align: center; color: #555;'>لوحة التحكم</h4>", unsafe_allow_html=True)
    if st.button("🔍 البحث في العملاء"): st.session_state.page = 'search'; st.rerun()
    if st.button("➕ إضافة عميل جديد"): st.session_state.page = 'add_customer'; st.rerun()
    if st.button("🔧 تسجيل صيانة"): st.session_state.page = 'add_maint'; st.rerun()
    if st.button("📋 جدول المواعيد"): st.session_state.page = 'schedule'; st.rerun()

# --- صفحة البحث والبيانات ---
elif st.session_state.page == 'search':
    if st.button("🔙 رجوع للرئيسية"): st.session_state.page = 'Home'; st.rerun()
    df_c = load_data(DATA_GID)
    df_m = load_data(MAINT_GID)
    
    query = st.text_input("ابحث بالاسم، الرقم، أو المنطقة")
    if not df_c.empty:
        if query:
            df_c = df_c[df_c.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        
        for _, row in df_c.iterrows():
            c_name = str(row.get('الاسم', '---')).strip()
            with st.expander(f"👤 {c_name} | 📍 {row.get('المنطقة', '')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    # تقسيم الأرقام والروابط
                    p_raw = str(row.get('الأرقام', ''))
                    p_list = re.split(r'[ ,/-]+', p_raw)
                    for p in p_list:
                        if len(p.strip()) > 5:
                            st.markdown(f'📞 <a href="tel:{p}">{p}</a> | <a href="https://wa.me/{p}">💬 واتساب</a>', unsafe_allow_html=True)
                with col2:
                    st.write(f"🔄 **الدورة:** كل {row.get('دورة الصيانة', '3')} شهور")
                    st.write(f"📅 **تاريخ التركيب:** {row.get('تاريخ التركيب', '---')}")
                    if "http" in str(row.get('اللوكيشن', '')):
                        st.markdown(f"[📍 فتح الموقع على الخريطة]({row.get('اللوكيشن')})")

                # سجل الصيانات الكامل
                st.markdown("---")
                st.write("📜 **تاريخ الصيانات:**")
                if not df_m.empty:
                    this_cust_m = df_m[df_m['الاسم'].astype(str).str.strip() == c_name].copy()
                    if not this_cust_m.empty:
                        st.table(this_cust_m)
                    else:
                        st.info("لا توجد سجلات صيانة لهذا العميل")
                
                # أزرار التصدير (Export)
                st.write("📥 **تصدير تقرير العميل:**")
                ex1, ex2 = st.columns(2)
                with ex1:
                    pdf_bytes = create_pdf(c_name, p_raw, str(row.get('المنطقة', '')))
                    st.download_button("📄 PDF Report", pdf_bytes, f"{c_name}.pdf", "application/pdf", key=f"pdf_{c_name}")
                with ex2:
                    excel_bytes = create_excel(pd.DataFrame([row]), this_cust_m if 'this_cust_m' in locals() else pd.DataFrame())
                    st.download_button("📊 Excel Sheet", excel_bytes, f"{c_name}.xlsx", key=f"ex_{c_name}")

# --- صفحة المواعيد الأسبوعية ---
elif st.session_state.page == 'schedule':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("📋 جدول مواعيد الصيانة")
    df_c = load_data(DATA_GID)
    if not df_c.empty:
        # عرض بسيط للجدول (يمكن تطويره لحساب المواعيد تلقائياً)
        st.dataframe(df_c[['الاسم', 'المنطقة', 'الأرقام', 'دورة الصيانة', 'تاريخ التركيب']])

# --- صفحة تسجيل صيانة (الخانات الكاملة) ---
elif st.session_state.page == 'add_maint':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("🔧 تسجيل زيارة صيانة")
    df_c = load_data(DATA_GID)
    with st.form("maint_form"):
        m_name = st.selectbox("اسم العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("اسم العميل")
        m_date = st.date_input("تاريخ الزيارة", datetime.now())
        st.write("🏷️ الشمعات المستبدلة:")
        c1, c2, c3 = st.columns(3)
        with c1: s1, s2, s3 = st.checkbox("P1"), st.checkbox("P2"), st.checkbox("P3")
        with c2: s4, s5, s6 = st.checkbox("ممبرين"), st.checkbox("بوست كاربون"), st.checkbox("كالسيت")
        with c3: s7 = st.checkbox("انفرا ريد")
        
        m_other = st.text_input("قطع غيار أخرى")
        m_cost = st.number_input("إجمالي التكلفة (EGP)", min_value=0, step=10)
        m_notes = st.text_area("ملاحظات إضافية")
        m_special = st.text_input("تاريخ تذكير خاص (اختياري)")
        
        if st.form_submit_button("تأكيد وحفظ البيانات"):
            st.success("تم التجهيز! انسخ البيانات للشيت الآن.")

# --- صفحة إضافة عميل جديد (الخانات الكاملة) ---
elif st.session_state.page == 'add_customer':
    if st.button("🔙 رجوع"): st.session_state.page = 'Home'; st.rerun()
    st.header("➕ إضافة عميل جديد")
    with st.form("cust_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            n_name = st.text_input("الاسم الثلاثي")
            n_phone = st.text_input("أرقام الهاتف (فواصل بين الأرقام)")
            n_area = st.text_input("المنطقة / الحي")
        with col_b:
            n_addr = st.text_area("العنوان بالتفصيل")
            n_inst = st.date_input("تاريخ التركيب المبدئي")
            n_cycle = st.number_input("دورة الصيانة (شهور)", value=3, min_value=1)
        
        n_loc = st.text_input("رابط لوكيشن جوجل مابس")
        
        if st.form_submit_button("إضافة للجدول"):
            st.info("جاهز للإضافة إلى قاعدة البيانات")
