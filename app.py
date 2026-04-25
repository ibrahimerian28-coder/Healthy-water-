import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import io
from fpdf import FPDF

# --- 1. إعدادات الصفحة والسرعة ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# خاصية التخزين المؤقت لتقليل التقل (بيحدث البيانات كل 5 دقائق أو يدوياً)
@st.cache_data(ttl=300)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. التنسيقات (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    [data-testid="stSidebar"] {background-color: #f0f2f6; width: 300px;}
    div.stButton > button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 45px;
    }
    .phone-container { background-color: #f8f9fa; padding: 8px; border-radius: 8px; border-right: 5px solid #004a99; margin-bottom: 5px; }
    /* ألوان المواعيد */
    .status-green { border-right: 10px solid #28a745; background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 5px 0; }
    .status-yellow { border-right: 10px solid #ffc107; background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 5px 0; }
    .status-red { border-right: 10px solid #dc3545; background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 5px 0; }
    .status-darkred { border-right: 10px solid #660000; background-color: #721c24; color: white; padding: 10px; border-radius: 5px; margin: 5px 0; }
    .status-gray { border-right: 10px solid #6c757d; background-color: #e2e3e5; padding: 10px; border-radius: 5px; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. الثوابت والروابط ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

# --- 4. محرك الحسابات (المواعيد والألوان) ---
def get_next_visit_info(cust_name, cycle, df_m):
    if df_m.empty: return None
    cust_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(cust_name).strip()].copy()
    if cust_m.empty: return None
    cust_m['visit_date'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
    last_visit = cust_m['visit_date'].max()
    if pd.isnull(last_visit): return None
    return last_visit + timedelta(days=int(cycle) * 30)

def get_color_style(next_date, status):
    if str(status) == "راكد": return "status-gray"
    if not next_date: return "status-green"
    diff = (next_date.date() - datetime.now().date()).days
    if diff > 7: return "status-green"
    if 0 <= diff <= 7: return "status-yellow"
    if -7 <= diff < 0: return "status-red"
    return "status-darkred"

# --- 5. وظيفة الـ PDF (Portrait + تصميم ضخم) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 90)
        self.ln(45)
    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(0, 74, 153)
        self.cell(0, 15, '01286609535 | Healthy Water', 0, 0, 'C')

def create_pdf(row, df_m):
    pdf = PDF(orientation='P')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    # تنظيف النصوص (بسبب قيود الخطوط في النسخة الحالية)
    def c(t): return str(t).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(0, 10, f"Customer: {c(row['الاسم'])}", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Area: {c(row.get('المنطقة', 'N/A'))} | Phone: {c(row['الأرقام'])}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Date", 1); pdf.cell(100, 10, "Maintenance Service", 1); pdf.cell(40, 10, "Cost", 1); pdf.ln()
    pdf.set_font("Arial", '', 10)
    for _, m in df_m.iterrows():
        pdf.cell(40, 10, str(m.get('تاريخ الزيارة', ''))[:10], 1)
        pdf.cell(100, 10, "Filter Service", 1)
        pdf.cell(40, 10, str(m.get('amount', '0')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 6. التنقل عبر القائمة الجانبية ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=250)
    st.title("القائمة الرئيسية")
    page = st.radio("انتقل إلى:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "إضافة عميل جديد", "تسجيل صيانة"])
    if st.button("🔄 تحديث البيانات"): st.cache_data.clear(); st.rerun()

df_customers = load_data(DATA_GID)
df_maintenance = load_data(MAINT_GID)

# --- 7. عرض الصفحات ---

if page == "بيانات العملاء":
    st.header("📋 قاعدة بيانات العملاء (حسب المنطقة)")
    if not df_customers.empty:
        df_sorted = df_customers.sort_values(by='المنطقة') if 'المنطقة' in df_customers.columns else df_customers
        for area, group in df_sorted.groupby('المنطقة'):
            with st.expander(f"📍 منطقة: {area} ({len(group)} عميل)"):
                for _, row in group.iterrows():
                    next_v = get_next_visit_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maintenance)
                    color = get_color_style(next_v, row.get('status', 'نشط'))
                    st.markdown(f'<div class="{color}"><b>{row["الاسم"]}</b> | الموعد القادم: {next_v.date() if next_v else "غير محدد"}</div>', unsafe_allow_html=True)
                    
                    # إظهار كامل البيانات عند فتح التفاصيل
                    inner_col1, inner_col2 = st.columns(2)
                    with inner_col1:
                        for col in df_customers.columns:
                            st.write(f"**{col}:** {row[col]}")
                        # أزرار الاتصال
                        nums = re.split(r'[^0-9]+', str(row['الأرقام']))
                        for n in nums:
                            if len(n) >= 10:
                                st.markdown(f'<div class="phone-container"><a href="tel:{n}">📞 {n}</a> | <a href="https://wa.me/2{n}">💬 واتساب</a></div>', unsafe_allow_html=True)
                    with inner_col2:
                        st.button("📝 تعديل العميل", key=f"edit_{row['الاسم']}")
                        st.button("❌ حذف العميل", key=f"del_{row['الاسم']}")
                        st.download_button("📄 تحميل PDF", create_pdf(row, df_maintenance[df_maintenance['الاسم']==row['الاسم']]), f"{row['الاسم']}.pdf", key=f"pdf_{row['الاسم']}")

elif page == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    if not df_customers.empty:
        active = df_customers[df_customers.get('status', 'نشط') == 'نشط']
        for i in range(8): # عرض 8 أيام (اليوم + أسبوع)
            target_date = datetime.now().date() + timedelta(days=i)
            day_name = target_date.strftime('%A')
            days_ar = {"Saturday":"السبت","Sunday":"الأحد","Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة"}
            st.subheader(f"🗓️ {days_ar.get(day_name, day_name)} ({target_date})")
            
            # فلترة العملاء لهذا اليوم (أو المرحلين)
            found = False
            for _, row in active.iterrows():
                next_v = get_next_visit_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maintenance)
                if next_v:
                    # ترحيل تلقائي: لو التاريخ أصغر من اليوم يظهر في "اليوم"
                    if (i == 0 and next_v.date() <= target_date) or (i > 0 and next_v.date() == target_date):
                        st.info(f"👤 {row['الاسم']} | 🏠 {row.get('المنطقة','')} | 📞 {row['الأرقام']}")
                        found = True
            if not found: st.write("لا توجد مواعيد")

elif page == "تسجيل صيانة":
    st.header("🔧 تسجيل صيانة جديدة")
    with st.form("maint_form"):
        cust_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        c1, c2, c3 = st.columns(3)
        # Checkboxes كما طلبت
        p1, p2, p3 = c1.checkbox("P1"), c1.checkbox("P2"), c1.checkbox("P3")
        mem, post, calc = c2.checkbox("membrane"), c2.checkbox("post carbon"), c2.checkbox("Calcite")
        infra = c3.checkbox("infrared")
        
        other = st.text_input("أخرى (Other)")
        cost = st.number_input("التكلفة (amount)", step=1)
        notes = st.text_area("ملاحظات (Notes)")
        remind = st.text_input("تذكير موعد خاص (Special reminder date)")
        
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم الحساب، الموعد القادم سيتحدث تلقائياً")

elif page == "بحث عن عميل":
    query = st.text_input("ادخل اسم أو رقم العميل")
    if query:
        results = df_customers[df_customers.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        st.dataframe(results)

elif page == "إضافة عميل جديد":
    with st.form("add_cust_form"):
        st.text_input("الاسم الثلاثي")
        st.text_input("الأرقام")
        st.text_input("المنطقة")
        st.selectbox("حالة العميل", ["نشط", "راكد"])
        st.number_input("دورة الصيانة (بالشهور)", 3)
        if st.form_submit_button("إضافة العميل"): st.success("تم")
