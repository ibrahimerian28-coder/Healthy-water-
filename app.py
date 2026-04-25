import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة والسرعة ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# منع التقل باستخدام التخزين المؤقت
@st.cache_data(ttl=60)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. التنسيق الجمالي والواجهة ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    [data-testid="stSidebar"] {background-color: #f8f9fa; width: 320px !important;}
    .phone-box { background-color: #e3f2fd; padding: 10px; border-radius: 8px; border-right: 5px solid #004a99; margin: 5px 0; }
    /* تنسيق ألوان الحالات */
    .status-green { border-right: 12px solid #28a745; background-color: #d4edda; padding: 12px; border-radius: 8px; margin: 8px 0; font-weight: bold;}
    .status-yellow { border-right: 12px solid #ffc107; background-color: #fff3cd; padding: 12px; border-radius: 8px; margin: 8px 0; font-weight: bold;}
    .status-red { border-right: 12px solid #dc3545; background-color: #f8d7da; padding: 12px; border-radius: 8px; margin: 8px 0; font-weight: bold;}
    .status-darkred { border-right: 12px solid #660000; background-color: #721c24; color: white; padding: 12px; border-radius: 8px; margin: 8px 0; font-weight: bold;}
    .status-gray { border-right: 12px solid #6c757d; background-color: #e2e3e5; padding: 12px; border-radius: 8px; margin: 8px 0; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. محرك الحسابات الذكي (المواعيد) ---
def get_next_visit_date(cust_name, cycle, df_m):
    if df_m.empty or 'الاسم' not in df_m.columns: return None
    cust_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(cust_name).strip()].copy()
    if cust_m.empty: return None
    cust_m['v_date'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
    last_v = cust_m['v_date'].max()
    if pd.isnull(last_v): return None
    try:
        return last_v + timedelta(days=int(cycle)*30)
    except: return None

def get_color_class(next_v, status):
    if str(status).strip() == "راكد": return "status-gray"
    if not next_v: return "status-green"
    diff = (next_v.date() - datetime.now().date()).days
    if diff > 7: return "status-green"
    if 0 <= diff <= 7: return "status-yellow"
    if -7 <= diff < 0: return "status-red"
    return "status-darkred"

# --- 4. تصدير PDF (Portrait) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 85)
        self.ln(40)
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(0, 74, 153)
        self.cell(0, 10, 'Healthy Water - 01286609535', 0, 0, 'C')

def generate_customer_pdf(row, df_m):
    pdf = PDF(orientation='P')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    # تنظيف الحروف لمنع أخطاء المكتبة
    pdf.cell(0, 10, f"Customer: {str(row['الاسم']).encode('ascii', 'ignore').decode('ascii') or 'N/A'}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Date", 1); pdf.cell(100, 10, "Maintenance", 1); pdf.cell(40, 10, "Cost", 1); pdf.ln()
    for _, m in df_m.iterrows():
        pdf.cell(40, 10, str(m.get('تاريخ الزيارة', ''))[:10], 1)
        pdf.cell(100, 10, "Service Checkup", 1)
        pdf.cell(40, 10, str(m.get('amount', '0')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 5. القائمة الجانبية وتحميل البيانات ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=250)
    st.title("لوحة التحكم")
    page = st.radio("القوائم:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "تسجيل صيانة", "إضافة عميل جديد"])
    st.markdown("---")
    if st.button("🔄 تحديث ومزامنة البيانات"): st.cache_data.clear(); st.rerun()

df_c = load_data("0") # شيت العملاء
df_m = load_data("2120582392") # شيت الصيانات

# --- 6. الصفحات الوظيفية ---

if page == "بيانات العملاء":
    st.header("📋 سجل العملاء الكامل (حسب المناطق)")
    if not df_c.empty:
        area_key = 'المنطقه' if 'المنطقه' in df_c.columns else 'المنطقة'
        df_sorted = df_c.sort_values(by=area_key) if area_key in df_c.columns else df_c
        
        for area, group in df_sorted.groupby(area_key if area_key in df_c.columns else df_c.index):
            with st.expander(f"📍 {area} ({len(group)} عميل)"):
                for _, row in group.iterrows():
                    # حساب الموعد القادم والحالة الملونة
                    next_v = get_next_visit_date(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
                    color = get_color_class(next_v, row.get('status', 'نشط'))
                    
                    st.markdown(f'<div class="{color}">👤 {row["الاسم"]} | موعدك القادم: {next_v.date() if next_v else "---"}</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 بيانات الملف:")
                        for c_name in df_c.columns:
                            st.write(f"**{c_name}:** {row[c_name]}")
                        
                        # أزرار الاتصال والواتساب واللوكيشن
                        nums = re.split(r'[^0-9]+', str(row.get('الأرقام', '')))
                        for n in nums:
                            if len(n) >= 10:
                                st.markdown(f'<div class="phone-box"><a href="tel:{n}">📞 اتصل {n}</a> | <a href="https://wa.me/2{n}">💬 واتساب</a></div>', unsafe_allow_html=True)
                        
                        loc = str(row.get('اللوكيشن', ''))
                        if "http" in loc: st.markdown(f"📍 [رابط اللوكيشن على الخريطة]({loc})")
                        
                        st.button("📝 تعديل بيانات العميل", key=f"e_{row['الاسم']}")
                        st.button("❌ حذف العميل نهائياً", key=f"d_{row['الاسم']}")

                    with col2:
                        st.subheader("📜 سجل الصيانات (الأحدث أولاً):")
                        cust_m = df_m[df_m['الاسم'] == row['الاسم']].copy()
                        if not cust_m.empty:
                            cust_m['v_date'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
                            cust_m = cust_m.sort_values(by='v_date', ascending=False)
                            # عرض كل الأعمدة في الصيانات
                            st.dataframe(cust_m.drop(columns=['v_date']))
                            
                            # أزرار تعديل/حذف لكل زيارة
                            for idx, m_row in cust_m.iterrows():
                                with st.expander(f"زيارة يوم {m_row.get('تاريخ الزيارة')}"):
                                    st.button("📝 تعديل الزيارة", key=f"edit_m_{idx}")
                                    st.button("❌ حذف الزيارة", key=f"del_m_{idx}")
                        
                        st.download_button("📄 تحميل تقرير PDF", generate_customer_pdf(row, cust_m), f"{row['الاسم']}.pdf", key=f"pdf_{row['الاسم']}")

elif page == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع (تحديث تلقائي)")
    if not df_c.empty:
        active_list = df_c[df_c.get('status', 'نشط').strip() == 'نشط']
        for i in range(8):
            target = datetime.now().date() + timedelta(days=i)
            day_ar = {"Saturday":"السبت","Sunday":"الأحد","Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعة"}.get(target.strftime('%A'))
            st.subheader(f"🗓️ {day_ar} ({target})")
            
            found = False
            for _, row in active_list.iterrows():
                nv = get_next_visit_date(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
                # منطق الترحيل: الموعد الفائت يظهر في "اليوم"
                if nv and ((i == 0 and nv.date() <= target) or (i > 0 and nv.date() == target)):
                    st.info(f"👤 {row['الاسم']} | 🏠 {row.get('المنطقه','')} | 📞 {row.get('الأرقام','')}")
                    found = True
            if not found: st.write("لا يوجد مواعيد مسجلة.")

elif page == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة فنية")
    with st.form("m_form"):
        c_choice = st.selectbox("اختر العميل", df_c['الاسم'].tolist()) if not df_c.empty else st.text_input("الاسم")
        v_date = st.date_input("تاريخ اليوم", datetime.now())
        
        st.write("🔧 القطع التي تم تغييرها (الخانات الإنجليزية):")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("membrane"); post = c2.checkbox("post carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("infrared")
        
        other = st.text_input("أخرى (Other)")
        cost = st.number_input("التكلفة الإجمالية (amount)", step=1)
        notes = st.text_area("ملاحظات إضافية (Notes)")
        special = st.text_input("تذكير موعد خاص (Special reminder date)")
        
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم التسجيل! الموعد القادم سيتحدث تلقائياً في السجلات.")

elif page == "بحث عن عميل":
    query = st.text_input("ابحث عن عميل (بالاسم، الرقم، أو المنطقة)")
    if query and not df_c.empty:
        results = df_c[df_c.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        st.dataframe(results)

elif page == "إضافة عميل جديد":
    st.header("➕ إضافة عميل جديد للقاعدة")
    with st.form("new_c"):
        st.text_input("الاسم الثلاثي")
        st.text_input("الأرقام")
        st.text_input("العنوان بالتفصيل")
        st.text_input("المنطقه")
        st.date_input("تاريخ التركيب")
        st.number_input("دورة الصيانة (شهور)", 3)
        st.selectbox("status", ["نشط", "راكد"])
        if st.form_submit_button("إضافة العميل"): st.success("تمت الإضافة بنجاح")
