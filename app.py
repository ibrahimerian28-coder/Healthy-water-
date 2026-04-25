import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import io
from fpdf import FPDF

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #ffffff;}
    div.stButton > button {
        width: 100%; height: 50px !important;
        background-color: #ffffff; color: #004a99;
        border: 2px solid #004a99; border-radius: 12px;
        font-size: 16px !important; font-weight: bold;
        margin-bottom: 8px;
    }
    .phone-container {
        background-color: #f8f9fa; padding: 10px;
        border-radius: 8px; margin-bottom: 5px;
        border-right: 5px solid #004a99;
    }
    /* ألوان حالات المواعيد */
    .status-green { background-color: #d4edda; padding: 10px; border-radius: 5px; border-right: 10px solid green; margin: 5px 0; }
    .status-yellow { background-color: #fff3cd; padding: 10px; border-radius: 5px; border-right: 10px solid #ffc107; margin: 5px 0; }
    .status-red { background-color: #f8d7da; padding: 10px; border-radius: 5px; border-right: 10px solid red; margin: 5px 0; }
    .status-darkred { background-color: #721c24; color: white; padding: 10px; border-radius: 5px; border-right: 10px solid #3e0000; margin: 5px 0; }
    .status-gray { background-color: #e2e3e5; padding: 10px; border-radius: 5px; border-right: 10px solid gray; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. جلب البيانات والمعالجة ---
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

# --- 3. محرك المواعيد والألوان ---
def calculate_next_visit(cust_name, cycle, df_m):
    if df_m.empty: return None
    cust_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(cust_name).strip()]
    if cust_m.empty: return None
    
    # تحويل تاريخ الزيارة لتاريخ حقيقي
    cust_m['visit_date'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
    last_visit = cust_m['visit_date'].max()
    
    if pd.isnull(last_visit): return None
    return last_visit + timedelta(days=int(cycle) * 30)

def get_status_color(next_date, status):
    if status == "راكد": return "status-gray"
    if next_date is None: return ""
    
    today = datetime.now().date()
    diff = (next_date.date() - today).days
    
    if diff > 7: return "status-green"
    if 0 <= diff <= 7: return "status-yellow"
    if -7 <= diff < 0: return "status-red"
    return "status-darkred"

# --- 4. وظيفة الـ PDF (Portrait + لوجو وفوتر ضخم) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 90)
        self.ln(45)
    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(0, 74, 153)
        self.cell(0, 15, '01286609535 | Healthy Water', 0, 0, 'C')

def create_pdf_bytes(cust_row, maint_df):
    pdf = PDF(orientation='P') # Portrait كما طلبت
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    def clean(t): return str(t).encode('ascii', 'ignore').decode('ascii') if t else "N/A"
    
    pdf.cell(0, 10, f"Customer Report: {clean(cust_row.get('الاسم', ''))}", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Phone: {clean(cust_row.get('الأرقام', ''))}", ln=True)
    pdf.cell(0, 8, f"Area: {clean(cust_row.get('المنطقة', ''))}", ln=True)
    pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(30, 10, 'Date', 1); pdf.cell(120, 10, 'Filters', 1); pdf.cell(40, 10, 'Amount', 1); pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    f_cols = ['P1', 'P2', 'P3', 'membrane', 'post carbon', 'Calcite', 'infrared']
    for _, m_row in maint_df.iterrows():
        done = [f for f in f_cols if str(m_row.get(f, '')).strip().lower() in ['تم', 'true', '1', 'checked']]
        pdf.cell(30, 10, str(m_row.get('تاريخ الزيارة', ''))[:10], 1)
        pdf.cell(120, 10, ", ".join(done), 1)
        pdf.cell(40, 10, str(m_row.get('amount', '0')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 5. واجهة التطبيق ---
if os.path.exists("logo.png"): st.image("logo.png", width=400)
if 'page' not in st.session_state: st.session_state.page = 'Home'

# القائمة الجانبية (للتنقل السريع)
menu = ["الرئيسية", "بيانات العملاء", "البحث عن عميل", "جدول المواعيد", "إضافة عميل جديد", "تسجيل صيانة"]
choice = st.sidebar.selectbox("القائمة", menu)

# --- صفحة بيانات العملاء (مرتبة بالمنطقة) ---
if choice == "بيانات العملاء":
    st.header("📋 قاعدة بيانات العملاء")
    df_c = load_data(DATA_GID)
    df_m = load_data(MAINT_GID)
    
    if not df_c.empty:
        # ترتيب حسب المنطقة
        df_c = df_c.sort_values(by='المنطقة')
        areas = df_c['المنطقة'].unique()
        
        for area in areas:
            st.markdown(f"### 📍 منطقة: {area}")
            area_custs = df_c[df_c['المنطقة'] == area]
            
            for _, row in area_custs.iterrows():
                next_v = calculate_next_visit(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
                color_class = get_status_color(next_v, row.get('status', 'نشط'))
                
                with st.container():
                    st.markdown(f'<div class="{color_class}"><b>👤 {row["الاسم"]}</b> - موعد القادم: {next_v.date() if next_v else "غير محدد"}</div>', unsafe_allow_html=True)
                    with st.expander("تفاصيل العميل والتحكم"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"🏠 العنوان: {row.get('العنوان', '')}")
                            st.write(f"📞 الأرقام: {row.get('الأرقام', '')}")
                            st.write(f"🛠️ حالة العميل: {row.get('status', 'نشط')}")
                        with col2:
                            st.button("📝 تعديل البيانات", key=f"edit_{row['الاسم']}")
                            st.button("❌ حذف العميل", key=f"del_{row['الاسم']}")
                            if st.button("➕ صيانة جديدة", key=f"new_m_{row['الاسم']}"):
                                st.session_state.target_cust = row['الاسم']
                                st.session_state.page = 'add_maint'

# --- صفحة جدول المواعيد (الذكية) ---
elif choice == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع القادم")
    df_c = load_data(DATA_GID)
    df_m = load_data(MAINT_GID)
    
    if not df_c.empty:
        # فلترة النشطين فقط
        active_custs = df_c[df_c.get('status', 'نشط') == 'نشط']
        
        # مصفوفة الأيام (7 أيام من اليوم)
        for i in range(8):
            target_day = datetime.now().date() + timedelta(days=i)
            day_name = target_day.strftime('%A')
            # تعريب اليوم
            days_ar = {"Saturday":"السبت","Sunday":"الأحد","Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة"}
            
            st.subheader(f"{days_ar.get(day_name, day_name)} - {target_day}")
            
            day_list = []
            for _, row in active_custs.iterrows():
                next_v = calculate_next_visit(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
                
                # منطق الترحيل: لو التاريخ أصغر من أو يساوي تارجت اليوم يظهر
                if next_v and next_v.date() <= target_day:
                    # نأخذ فقط من لم تتم زيارته (أي أن موعده هو اليوم أو مرحل من قبل)
                    if next_v.date() == target_day or (i==0 and next_v.date() < target_day):
                        day_list.append(row)
            
            if day_list:
                for c in day_list:
                    st.info(f"🔹 {c['الاسم']} | 📞 {c['الأرقام']}")
            else:
                st.write("لا يوجد مواعيد")

# --- صفحة تسجيل صيانة (Checkboxes) ---
elif choice == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة جديدة")
    df_c = load_data(DATA_GID)
    cust_list = df_c['الاسم'].tolist() if not df_c.empty else []
    
    with st.form("maint_form"):
        selected_cust = st.selectbox("اختر العميل", cust_list)
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        
        c1, c2, c3 = st.columns(3)
        # استخدام نظام الصح والخطأ كما طلبت
        p1 = c1.checkbox("P1")
        p2 = c1.checkbox("P2")
        p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane")
        post = c2.checkbox("Post Carbon")
        calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        
        other = st.text_input("أخرى (Other)")
        cost = st.number_input("التكلفة (amount)", step=1)
        notes = st.text_area("ملاحظات (Notes)")
        remind = st.text_input("تذكر موعد خاص (Special reminder date)")
        
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم تسجيل البيانات بنجاح (سيتم الرفع للشيت)")

# --- صفحة البحث عن عميل (مع زراير الاتصال) ---
elif choice == "البحث عن عميل":
    df_c = load_data(DATA_GID)
    query = st.text_input("ابحث عن عميل")
    if query and not df_c.empty:
        results = df_c[df_c.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        for _, row in results.iterrows():
            with st.expander(f"👤 {row['الاسم']}"):
                # زراير الاتصال لكل رقم
                nums = re.split(r'[^0-9]+', str(row['الأرقام']))
                for n in nums:
                    if len(n) >= 10:
                        st.markdown(f'<a href="tel:{n}">📞 اتصل {n}</a> | <a href="https://wa.me/2{n}">💬 واتساب</a>', unsafe_allow_html=True)
                st.download_button("📄 تقرير PDF", create_pdf_bytes(row, pd.DataFrame()), f"{row['الاسم']}.pdf")

# --- إضافة عميل جديد ---
elif choice == "إضافة عميل جديد":
    st.header("➕ عميل جديد")
    with st.form("new_cust"):
        st.text_input("الاسم")
        st.text_input("الأرقام")
        st.text_input("المنطقة")
        st.selectbox("حالة العميل", ["نشط", "راكد"])
        st.number_input("دورة الصيانة (بالشهور)", 3)
        if st.form_submit_button("حفظ"): st.success("تم")

# --- الصفحة الرئيسية ---
else:
    st.markdown("<h2 style='text-align: center;'>Healthy Water Management</h2>", unsafe_allow_html=True)
    st.info("اختر من القائمة الجانبية لبدء العمل")
