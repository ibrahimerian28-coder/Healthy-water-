import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF # تأكد من تنصيب fpdf2 في الـ requirements

# --- 1. إعدادات الصفحة وسرعة الأداء القصوى ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# دالة ذكية لتحميل البيانات وتخزينها في الجلسة لمنع التقل
def get_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# تخزين البيانات في الـ Session State عشان التطبيق يبقى سريع جداً
if 'df_c' not in st.session_state:
    st.session_state.df_c = get_data("0")
if 'df_m' not in st.session_state:
    st.session_state.df_m = get_data("2120582392")

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

# --- 2. نظام تسجيل الدخول ---
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
            else: st.error("الباسورد غلط!")
    else:
        u_id = st.sidebar.text_input("رقم الموبايل (ID):")
        if st.sidebar.button("دخول العميل"):
            df = st.session_state.df_c
            # بحث مرن عن الـ ID في خانة الـ phone
            match = df[df['phone'].astype(str).str.contains(u_id)] if not df.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("الرقم ده مش مسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. تصميم PDF أفقي احترافي (علاج الـ Unicode Error) ---
class SAFE_PDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 45) # اللوجو كبير عاليسار
        except: pass
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Healthy Water - Service Report', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'B', 12)
        # بيانات الشركة في الفوتر بخط كبير
        self.cell(0, 10, 'Healthy Water Company | Support: 01286609535', 0, 0, 'C')

def create_pdf(row, df_m):
    pdf = SAFE_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    
    # تحويل البيانات لنص آمن لتجنب أخطاء اللغة
    name_safe = "".join([i if ord(i) < 128 else "" for i in str(row['name'])])
    pdf.cell(0, 10, f"Customer: {name_safe} | Phone: {row.get('phone','')}", ln=True)
    pdf.cell(0, 10, f"Area: {row.get('area','')} | Setup Date: {row.get('setup_date','')}", ln=True)
    pdf.ln(5)

    # جدول الصيانات (مرتب من الأحدث)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    pdf.set_fill_color(230, 230, 230)
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    df_m['dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    sorted_m = df_m.sort_values(by='dt', ascending=False)

    for _, m in sorted_m.iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for c in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            check = "V" if format_to_check(m.get(c,'')) == "✓" else "X"
            pdf.cell(31, 10, check, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 12px solid #007bff; background-color: #f8f9fa; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:6px 12px; border-radius:6px; text-decoration:none; margin:3px; display:inline-block; font-weight:bold; }
    .call-btn { background:#007bff !important; color:white !important; padding:6px 12px; border-radius:6px; text-decoration:none; margin:3px; display:inline-block; font-weight:bold; }
    .contact-box { background:#e9ecef; padding:20px; border-radius:15px; text-align:center; border:2px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. القائمة الجانبية ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "تسجيل صيانة", "إضافة عميل جديد"])
    if st.sidebar.button("تحديث البيانات 🔄"):
        st.session_state.clear()
        st.rerun()
else:
    menu = "بروفايلي"
    st.sidebar.markdown("### 📞 اتصل بنا")
    st.sidebar.markdown('<a href="tel:01286609535" class="call-btn">اتصال هاتفي</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="https://wa.me/201286609535" class="wa-btn">واتساب الشركة</a>', unsafe_allow_html=True)

if st.sidebar.button("خروج 🚪"):
    st.session_state.auth = None
    st.rerun()

# --- 6. الصفحات ---
if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    
    if st.session_state.auth == "customer":
        st.markdown(f"""<div class="contact-box"><h3>مرحباً بك في Healthy Water</h3><p>للدعم الفني أو طلب صيانة:</p>
        <a href="tel:01286609535" class="call-btn">📞 01286609535</a>
        <a href="https://wa.me/201286609535" class="wa-btn">💬 واتساب الدعم</a></div>""", unsafe_allow_html=True)
        data_to_show = [st.session_state.user_data.to_dict()]
    else:
        data_to_show = st.session_state.df_c.to_dict('records')
    
    for r in data_to_show:
        st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📞 {r.get("phone","")} | 📍 {r.get("area","")}</p></div>', unsafe_allow_html=True)
        with st.expander("فتح الملف الكامل وسجل الصيانات"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                # حل مشكلة أرقام التليفونات المتعددة
                all_nums = re.findall(r'01\d{9}', str(r['phone']))
                if all_nums:
                    st.write("**📱 اتصل بالعميل:**")
                    for n in all_nums:
                        st.markdown(f'<a href="tel:{n}" class="call-btn">📞 {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">واتساب</a>', unsafe_allow_html=True)
                if "http" in str(r.get('location','')): st.link_button("📍 اللوكيشن", r['location'])
            with c2:
                st.subheader("🛠️ سجل الصيانات")
                history = st.session_state.df_m[st.session_state.df_m['name'] == r['name']].copy()
                if not history.empty:
                    history['visit_date'] = pd.to_datetime(history['visit_date'], errors='coerce')
                    st.dataframe(history.sort_values(by='visit_date', ascending=False))
                    # زر تحميل PDF المعدل
                    pdf_bytes = create_pdf(r, history)
                    st.download_button(f"📥 تحميل تقرير {r['name']}", pdf_bytes, f"HealthyWater_{r['name']}.pdf", "application/pdf")

# (بقية صفحات المواعيد والتسجيل تظل كما هي مع استخدام st.session_state للسرعة)
