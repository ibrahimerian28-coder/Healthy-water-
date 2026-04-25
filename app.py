import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF # تأكد من استخدام fpdf2

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=60)
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'نعم'] else "✗"

# --- 2. نظام تسجيل الدخول ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'user' not in st.session_state: st.session_state.user = None

def login():
    st.title("💧 Healthy Water Management")
    role = st.radio("دخول بصفتك:", ["أدمن", "عميل"])
    if role == "أدمن":
        pwd = st.text_input("باسورد المدير:", type="password")
        if st.button("دخول"):
            if pwd == "HgM18082019$&)":
                st.session_state.auth = "admin"
                st.rerun()
            else: st.error("غلط يا هندسة!")
    else:
        pid = st.text_input("رقم الموبايل المسجل:")
        if st.button("دخول العميل"):
            df_c = load_all_data("0")
            match = df_c[df_c['الأرقام'].astype(str).str.contains(pid)] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user = match.iloc[0]
                st.rerun()
            else: st.error("الرقم ده مش عندنا!")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. التنسيقات ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 10px; border-right: 10px solid #28a745; background: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .wa-btn { background:#25d366; color:white !important; padding:5px 10px; border-radius:5px; text-decoration:none; margin:2px; display:inline-block; }
    .call-btn { background:#007bff; color:white !important; padding:5px 10px; border-radius:5px; text-decoration:none; margin:2px; display:inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. الـ PDF (إصلاح خطأ Unicode) ---
def create_pdf(row, df_m):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, f"Customer Service Report - {row['الاسم']}", ln=True)
    pdf.set_font("helvetica", '', 12)
    pdf.ln(5)
    # جدول الصيانات
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(30, 10, h, 1, 0, 'C')
    pdf.ln()
    for _, m in df_m.iterrows():
        pdf.cell(30, 10, str(m.get('تاريخ الزيارة',''))[:10], 1)
        for c in ['P1','P2','P3','membrane','post carbon','Calcite','infrared']:
            mark = "V" if format_to_check(m.get(c,'')) == "✓" else "X"
            pdf.cell(30, 10, mark, 1, 0, 'C')
        pdf.cell(30, 10, str(m.get('amount','0')), 1); pdf.ln()
    return pdf.output()

# --- 5. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")

# --- 6. القائمة والصفحات ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "تسجيل صيانة", "إضافة عميل"])
    if st.sidebar.button("خروج"): st.session_state.auth = None; st.rerun()
else:
    menu = "بروفايلي"
    if st.sidebar.button("خروج"): st.session_state.auth = None; st.rerun()

# --- الصفحة الرئيسية ---
if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 ملفات العملاء")
    data = [st.session_state.user] if st.session_state.auth == "customer" else df_c.to_dict('records')
    
    for r in data:
        st.markdown(f'<div class="cust-card"><h3>👤 {r["الاسم"]}</h3><p>📍 {r.get("المنطقه","")} | 📞 {r.get("الأرقام","")}</p></div>', unsafe_allow_html=True)
        with st.expander("التفاصيل والسجلات"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**العنوان:** {r.get('العنوان','')}")
                st.write(f"**دورة الصيانة:** {r.get('دورة الصيانة','')} شهور")
                nums = re.findall(r'01[0-2,5]\d{8}', str(r['الأرقام']))
                for n in nums:
                    st.markdown(f'<a href="tel:{n}" class="call-btn">📞 {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)
            with col2:
                this_m = df_m[df_m['الاسم'] == r['الاسم']].copy()
                if not this_m.empty:
                    st.dataframe(this_m[['تاريخ الزيارة', 'amount']].sort_values(by='تاريخ الزيارة', ascending=False))
                    st.download_button("📥 تحميل التقرير PDF", create_pdf(r, this_m), f"{r['الاسم']}.pdf")

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد القادمة")
    # هنا يظهر الـ Special Reminder Date بشكل أساسي
    if 'Special reminder date' in df_m.columns:
        special = df_m[df_m['Special reminder date'].notna()]
        st.subheader("🔔 تنبيهات خاصة (مواعيد استثنائية)")
        st.write(special[['الاسم', 'Special reminder date', 'Other']])

elif menu == "تسجيل صيانة":
    st.header("🔧 إضافة سجل صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['الاسم'].tolist())
        date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c3.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        
        other = st.text_input("Other (بيانات أخرى)")
        special_date = st.date_input("Special reminder date (موعد استثنائي)", value=None)
        cost = st.number_input("التكلفة")
        if st.form_submit_button("حفظ"): st.success("تم!")

elif menu == "إضافة عميل":
    st.header("➕ عميل جديد")
    with st.form("a_form"):
        st.text_input("الاسم")
        st.text_input("الأرقام")
        st.text_input("المنطقه")
        st.text_input("العنوان")
        st.text_input("اللوكيشن")
        st.number_input("دورة الصيانة", 3)
        if st.form_submit_button("إضافة"): st.success("تم!")
