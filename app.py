import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=600) # تخزين البيانات 10 دقائق لسرعة خارقة
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # معالجة القيم الفارغة فوراً لمنع الأخطاء
        df = df.fillna("")
        return df
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

# --- 2. نظام تسجيل الدخول المحسن ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'user_data' not in st.session_state: st.session_state.user_data = None

def login():
    st.title("💧 Healthy Water Management")
    role = st.sidebar.selectbox("دخول بصفتك:", ["أدمن", "عميل"])
    if role == "أدمن":
        pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
        if st.sidebar.button("دخول"):
            if pwd == "HgM18082019$&)":
                st.session_state.auth = "admin"
                st.rerun()
            else: st.error("الباسورد غلط يا هندسة!")
    else:
        u_id = st.sidebar.text_input("رقم الموبايل (ID):")
        if st.sidebar.button("دخول العميل"):
            df_c = load_all_data("0")
            # بحث مرن يحول كل شيء لنصوص لمنع خطأ الـ ID
            match = df_c[df_c['phone'].astype(str).str.contains(str(u_id))] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("الرقم ده مش متسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. تصميم الـ PDF الأفقي (Landscape) ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 45) # اللوجو كبير يساراً
        except: pass
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Service Report', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Healthy Water Company - Support: 01286609535', 0, 0, 'C')

def generate_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    # بيانات العميل
    pdf.cell(0, 10, f"Customer: {str(row['name'])}", ln=True)
    pdf.cell(0, 10, f"Phone: {str(row.get('phone',''))} | Area: {str(row.get('area',''))}", ln=True)
    pdf.ln(5)
    # الجدول
    pdf.set_fill_color(240, 240, 240)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()
    # ترتيب الصيانات من الأحدث
    df_m['dt_sort'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    sorted_df = df_m.sort_values(by='dt_sort', ascending=False)
    pdf.set_font("Arial", '', 10)
    for _, m in sorted_df.iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            check = "V" if format_to_check(m.get(f,'')) == "✓" else "X"
            pdf.cell(31, 10, check, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    .call-btn { background:#007bff !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")

# --- 6. القائمة الجانبية ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "تسجيل صيانة", "إضافة عميل جديد"])
else:
    menu = "بروفايلي"
    st.sidebar.markdown("### 📞 اتصل بنا")
    st.sidebar.markdown('<a href="tel:01286609535" class="call-btn">📞 اتصل الآن</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="https://wa.me/201286609535" class="wa-btn">💬 واتساب الشركة</a>', unsafe_allow_html=True)

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.session_state.user_data = None
    st.rerun()

# --- 7. الصفحات ---
if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    
    if st.session_state.auth == "customer":
        st.info("مرحباً بك! يمكنك التواصل معنا مباشرة عبر الأزرار في القائمة الجانبية.")
        data_to_show = [st.session_state.user_data.to_dict()]
    else:
        data_to_show = df_c.to_dict('records')
    
    for r in data_to_show:
        st.markdown(f'<div class="cust-card"><h3>👤 {str(r["name"])}</h3><p>📍 {str(r.get("area",""))} | 📞 {str(r.get("phone",""))}</p></div>', unsafe_allow_html=True)
        with st.expander("فتح التفاصيل الكاملة"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Address:** {str(r.get('adress',''))}")
                st.write(f"**Setup Date:** {str(r.get('setup_date',''))}")
                # معالجة أرقام التليفونات المتعددة بأمان
                phone_str = str(r.get('phone',''))
                nums = re.findall(r'01\d{9}', phone_str)
                if nums:
                    for n in nums:
                        st.markdown(f'<a href="tel:{n}" class="call-btn">📞 Call {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
                if "http" in str(r.get('location','')): st.link_button("📍 Location", r['location'])
            with col2:
                st.subheader("🛠️ Maintenance History")
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    # زر تحميل PDF (المطلوب)
                    pdf_bytes = generate_pdf(r, history)
                    st.download_button(f"📥 Download Report ({str(r['name'])})", pdf_bytes, f"{str(r['name'])}.pdf", "application/pdf")
                    
                    for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                        if f in history.columns: history[f] = history[f].apply(format_to_check)
                    st.dataframe(history.sort_values(by='visit_date', ascending=False))

# (بقية صفحات جدول المواعيد وتسجيل الزيارات تظل كما هي لضمان الاستقرار)
elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    # ... (كما في كودك الأصلي تماماً)
elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    # ... (كما في كودك الأصلي تماماً)
elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل")
    # ... (كما في كودك الأصلي تماماً)
