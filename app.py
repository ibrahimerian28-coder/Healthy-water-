import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة والأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=300) # تخزين البيانات لمدة 5 دقائق لزيادة السرعة
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

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
            else: st.error("الباسورد غلط يا هندسة!")
    else:
        u_id = st.sidebar.text_input("رقم الموبايل (ID):")
        if st.sidebar.button("دخول العميل"):
            df_c = load_all_data("0")
            # بحث مرن يقبل أي جزء من الرقم لسهولة الدخول
            match = df_c[df_c['phone'].astype(str).str.contains(u_id)] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("الرقم ده مش متسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. تصميم الـ PDF (أفقي + لوجو + فوتر) ---
class MY_PDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 50) # لوجو بحجم كبير
        except: pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 102, 204)
        self.cell(0, 15, 'Healthy Water Service Report', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Healthy Water Company - Technical Support: 01286609535', 0, 0, 'C')

def create_pdf(row, df_m):
    pdf = MY_PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    # بيانات العميل في الهيدر
    pdf.cell(0, 10, f"Customer Name: {row['name']} | Phone: {row['phone']}", ln=True)
    pdf.cell(0, 10, f"Area: {row.get('area','')} | Address: {row.get('adress','')}", ln=True)
    pdf.ln(5)
    
    # الجدول
    pdf.set_fill_color(240, 240, 240)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()
    
    # ترتيب الصيانات من الأحدث للأقدم
    df_m['dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    sorted_m = df_m.sort_values(by='dt', ascending=False)
    
    pdf.set_font("Arial", '', 11)
    for _, m in sorted_m.iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for c in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            mark = "V" if format_to_check(m.get(c, '')) == "✓" else "X"
            pdf.cell(31, 10, mark, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    .call-btn { background:#007bff !important; color:white !important; padding:8px 15px; border-radius:8px; text-decoration:none; margin:5px; display:inline-block; font-weight:bold; }
    .contact-header { background:#f1f3f5; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px; border:1px solid #dee2e6; }
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
    st.rerun()

# --- 7. الصفحات ---

if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    
    if st.session_state.auth == "customer":
        st.markdown(f"""<div class="contact-header"><h3>اهلا بك يا هندسة</h3><p>لطلب صيانة أو استفسار تواصل معنا مباشرة:</p>
        <a href="tel:01286609535" class="call-btn">📞 01286609535</a>
        <a href="https://wa.me/201286609535" class="wa-btn">💬 واتساب الشركة</a></div>""", unsafe_allow_html=True)
        data_to_show = [st.session_state.user_data.to_dict()]
    else:
        data_to_show = df_c.to_dict('records')
    
    for r in data_to_show:
        st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📍 {r.get("area","")} | 📞 {r.get("phone","")}</p></div>', unsafe_allow_html=True)
        with st.expander("فتح الملف الكامل"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                # تحسين لقط أرقام الهاتف المتعددة وصناعة أزرار لها
                nums = re.findall(r'01\d{9}', str(r['phone']))
                if nums:
                    st.write("**📱 أرقام العميل:**")
                    for n in nums:
                        st.markdown(f'<a href="tel:{n}" class="call-btn">📞 {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)
                if "http" in str(r.get('location','')): st.link_button("📍 فتح اللوكيشن", r['location'])
            with col2:
                st.subheader("🛠️ سجل الصيانات")
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    history['visit_date'] = pd.to_datetime(history['visit_date'], errors='coerce')
                    st.dataframe(history.sort_values(by='visit_date', ascending=False))
                    # زر تحميل PDF
                    pdf_bytes = create_pdf(r, history)
                    st.download_button(f"📥 تحميل تقرير {r['name']}", pdf_bytes, f"{r['name']}.pdf", "application/pdf")

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    tab1, tab2 = st.tabs(["المواعيد الدورية", "🔔 مواعيد استثنائية (Special)"])
    with tab2:
        if 'Special_reminder_date' in df_m.columns:
            specials = df_m[df_m['Special_reminder_date'].notna()]
            st.dataframe(specials[['name', 'Special_reminder_date', 'other']])

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        v_date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post_carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        st.divider()
        other = st.text_input("أخرى (Other)")
        spec_date = st.date_input("موعد استثنائي (Special reminder date)", value=None)
        cost = st.number_input("التكلفة (amount)")
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"): st.success("تم!")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل جديد لبيانات Healthy Water")
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
        if st.form_submit_button("إضافة"): st.success("تم الحفظ!")
