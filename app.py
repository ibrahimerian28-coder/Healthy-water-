import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=600) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df.fillna("") 
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

def clean_text_for_pdf(text):
    if not text: return ""
    return "".join(i for i in str(text) if ord(i) < 128)

# --- 2. نظام تسجيل الدخول (تم تصحيح البحث الشامل هنا) ---
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
        u_id = st.sidebar.text_input("رقم الموبايل أو الكود (ID):")
        if st.sidebar.button("دخول العميل"):
            df_c = load_all_data("0")
            search_val = str(u_id).strip()
            if not df_c.empty:
                # تصحيح البحث: التأكد من تحويل العمود لنصوص والبحث عن التطابق بداخلها
                match = df_c[df_c['phone'].astype(str).str.contains(re.escape(search_val), na=False)]
                if not match.empty:
                    st.session_state.auth = "customer"
                    st.session_state.user_data = match.iloc[0]
                    st.rerun()
                else: st.error("الرقم ده مش متسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. تصميم الـ PDF (تم تصحيح مخرجات الـ Bytes هنا) ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 50) 
        except: pass
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Service Report - Healthy Water', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Healthy Water Company - Support: 01286609535', 0, 0, 'C')

def generate_safe_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    
    c_name = clean_text_for_pdf(row['name'])
    c_phone = clean_text_for_pdf(row.get('phone',''))
    c_area = clean_text_for_pdf(row.get('area',''))
    
    pdf.cell(0, 10, f"Customer Name: {c_name}", ln=True)
    pdf.cell(0, 10, f"ID/Phone: {c_phone} | Area: {c_area}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()

    df_m['v_date_dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    sorted_m = df_m.sort_values(by='v_date_dt', ascending=False)

    pdf.set_font("Arial", '', 10)
    for _, m in sorted_m.iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            check = "V" if format_to_check(m.get(f,'')) == "✓" else "X"
            pdf.cell(31, 10, check, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    
    # تصحيح: إخراج الملف كـ bytes مباشرة متوافقة مع streamlit
    return bytes(pdf.output())

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    .call-btn { background:#007bff !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    .contact-section { background: #fff; padding: 20px; border-radius: 15px; border: 1px solid #ddd; text-align: center; margin-bottom: 20px; }
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
    st.sidebar.markdown('<a href="tel:01286609535" class="call-btn">📞 فون</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="https://wa.me/201286609535" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.session_state.user_data = None
    st.rerun()

# --- 7. الصفحات ---
if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    
    if st.session_state.auth == "customer":
        st.markdown("""<div class="contact-section"><h3>أهلاً بك.. كيف يمكننا مساعدتك اليوم؟</h3>
        <p>فريق الدعم الفني جاهز للرد على استفساراتك</p>
        <a href="tel:01286609535" class="call-btn">📞 اتصل بنا الآن</a>
        <a href="https://wa.me/201286609535" class="wa-btn">💬 مراسلة واتساب</a>
        </div>""", unsafe_allow_html=True)
        data_to_show = [st.session_state.user_data.to_dict()]
    else:
        data_to_show = df_c.to_dict('records')
    
    for r in data_to_show:
        st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📍 {r.get("area","")} | 📞 {r.get("phone","")}</p></div>', unsafe_allow_html=True)
        with st.expander("فتح التفاصيل الكاملة"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                st.write(f"**الدورة:** كل {r.get('cycle',3)} شهور")
                
                # تصحيح استخراج الأرقام المتعددة: استخراج كل ما يبدأ بـ 01 ويتبعه 9 أرقام مهما كان ما بينهم
                phone_val = str(r.get('phone',''))
                nums = re.findall(r'01\d{9}', phone_val) 
                if nums:
                    for n in nums:
                        st.markdown(f'<a href="tel:{n}" class="call-btn">📞 اتصال {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)
                
                if "http" in str(r.get('location','')): st.link_button("📍 فتح اللوكيشن", r['location'])
            with col2:
                st.subheader("🛠️ سجل الصيانات")
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    try:
                        pdf_output = generate_safe_pdf(r, history)
                        st.download_button(
                            label=f"📥 تحميل تقرير PDF ({r['name']})",
                            data=pdf_output,
                            file_name=f"{r['name']}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e: 
                        st.warning("عفواً، لا يمكن إنشاء PDF حالياً")
                    
                    for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                        if f in history.columns: history[f] = history[f].apply(format_to_check)
                    st.dataframe(history.sort_values(by='visit_date', ascending=False))

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    tab_a, tab_b = st.tabs(["الصيانات الدورية", "🔔 مواعيد استثنائية"])
    with tab_a:
        for i in range(8):
            day = datetime.now().date() + timedelta(days=i)
            st.write(f"**{day}**")
    with tab_b:
        if 'Special_reminder_date' in df_m.columns:
            df_m['rem_dt'] = pd.to_datetime(df_m['Special_reminder_date'], errors='coerce')
            specials = df_m[df_m['rem_dt'].notna()]
            st.dataframe(specials[['name', 'Special_reminder_date', 'other', 'notes']])

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        v_date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        st.divider()
        other = st.text_input("أخرى")
        spec_date = st.date_input("موعد استثنائي", value=None)
        cost = st.number_input("التكلفة")
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"): st.success("تم!")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل")
    with st.form("add_f"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("name")
            st.text_input("phone")
            st.text_input("adress")
            st.text_input("area")
        with col2:
            st.text_input("location")
            st.date_input("setup_date")
            st.number_input("cycle", 3)
            st.selectbox("status", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"): st.success("تم!")
