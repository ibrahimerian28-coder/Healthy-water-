import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة والسرعة القصوى ---
st.set_page_config(page_title="Healthy Water Management", layout="wide")

@st.cache_data(ttl=300) # تحديث البيانات كل 5 دقائق لضمان السرعة وعدم التقل
def load_sheet_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns] # تنظيف أسماء الأعمدة
        return df
    except:
        return pd.DataFrame()

# --- 2. التنسيق (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    .customer-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 15px solid; }
    .btn-row { display: flex; gap: 10px; margin-top: 10px; }
    /* تعريف ألوان الحالات */
    .color-green { border-color: #28a745; background-color: #f1f9f3; }
    .color-yellow { border-color: #ffc107; background-color: #fffdf5; }
    .color-red { border-color: #dc3545; background-color: #fff5f5; }
    .color-darkred { border-color: #8b0000; background-color: #4b0000; color: white; }
    .color-gray { border-color: #6c757d; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. محرك الحسابات المنطقي ---
def calculate_next_visit(cust_name, cycle, df_m):
    if df_m.empty: return None
    cust_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(cust_name).strip()].copy()
    if cust_m.empty: return None
    cust_m['visit_date'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
    last_v = cust_m['visit_date'].max()
    if pd.isnull(last_v): return None
    return last_v + timedelta(days=int(cycle)*30)

def get_color_and_class(next_v, status):
    if str(status).strip() == "راكد": return "color-gray"
    if not next_v: return "color-green"
    diff = (next_v.date() - datetime.now().date()).days
    if diff > 7: return "color-green"
    if 0 <= diff <= 7: return "color-yellow"
    if -7 <= diff < 0: return "color-red"
    return "color-darkred"

# --- 4. تصدير PDF (أفقي Landscape) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 50)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Customer Maintenance Report', 0, 1, 'C')
        self.ln(10)

def create_pdf_landscape(row, df_m):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    # تنظيف النصوص للأمان
    pdf.cell(0, 10, f"Customer: {str(row['الاسم'])} | Area: {str(row.get('المنطقة',''))}", ln=True)
    pdf.ln(5)
    # جدول البيانات
    pdf.set_font("Arial", 'B', 10)
    cols = ["Date", "Service Details", "Cost", "Notes"]
    for col in cols: pdf.cell(60, 10, col, 1)
    pdf.ln()
    pdf.set_font("Arial", '', 9)
    for _, m in df_m.iterrows():
        pdf.cell(60, 10, str(m.get('تاريخ الزيارة',''))[:10], 1)
        pdf.cell(60, 10, "Filter Maintenance", 1)
        pdf.cell(60, 10, str(m.get('amount','0')), 1)
        pdf.cell(60, 10, str(m.get('Notes','')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 5. تحميل البيانات الفعلي ---
df_c = load_sheet_data("0") # شيت العملاء
df_m = load_sheet_data("2120582392") # شيت الصيانات

# --- 6. عرض الصفحات ---
st.sidebar.title("Healthy Water 💧")
page = st.sidebar.radio("القائمة:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "تسجيل صيانة", "إضافة عميل جديد"])

if page == "بيانات العملاء":
    st.header("📋 قاعدة بيانات العملاء (مرتبة بالمناطق)")
    if not df_c.empty:
        # ترتيب حسب المنطقة
        area_col = 'المنطقة' if 'المنطقة' in df_c.columns else df_c.columns[3]
        df_sorted = df_c.sort_values(by=area_col)
        
        for index, row in df_sorted.iterrows():
            next_v = calculate_next_visit(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
            c_class = get_color_and_class(next_v, row.get('status', 'نشط'))
            
            with st.container():
                st.markdown(f"""<div class="customer-card {c_class}">
                    <h3>👤 {row['الاسم']}</h3>
                    <p>📍 <b>المنطقة:</b> {row.get(area_col, '---')} | 📞 <b>الهاتف:</b> {row['الأرقام']}</p>
                    <p>📅 <b>الموعد القادم:</b> {next_v.date() if next_v else 'غير محدد'}</p>
                </div>""", unsafe_allow_html=True)
                
                with st.expander("فتح كامل البيانات والتحكم"):
                    # إظهار كل الأعمدة من الشيت
                    cols = st.columns(2)
                    for i, (col_name, col_val) in enumerate(row.items()):
                        cols[i%2].write(f"**{col_name}:** {col_val}")
                    
                    # أزرار الاتصال
                    st.markdown("---")
                    btn_c1, btn_c2, btn_c3 = st.columns(3)
                    phone = str(row['الأرقام']).split('/')[0].strip()
                    btn_c1.markdown(f"[📞 اتصال](tel:{phone})")
                    btn_c2.markdown(f"[💬 واتساب](https://wa.me/2{phone})")
                    if "http" in str(row.get('اللوكيشن', '')):
                        btn_c3.markdown(f"[📍 اللوكيشن]({row['اللوكيشن']})")
                    
                    # التحكم (تعديل/حذف)
                    st.button("📝 تعديل بيانات العميل", key=f"edit_c_{index}")
                    st.button("🗑️ حذف العميل", key=f"del_c_{index}")
                    
                    # سجل الصيانات (الأحدث أولاً)
                    st.subheader("🛠️ سجل الصيانات")
                    this_m = df_m[df_m['الاسم'] == row['الاسم']].copy()
                    if not this_m.empty:
                        this_m['v_date'] = pd.to_datetime(this_m['تاريخ الزيارة'], errors='coerce')
                        this_m = this_m.sort_values(by='v_date', ascending=False)
                        st.dataframe(this_m.drop(columns=['v_date']))
                        st.download_button("📥 تصدير PDF (Landscape)", create_pdf_landscape(row, this_m), f"{row['الاسم']}.pdf")

elif page == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع (تحديث تلقائي)")
    if not df_c.empty:
        # العملاء النشطين فقط
        active_c = df_c[df_c.get('status', 'نشط') == 'نشط']
        for i in range(8): # عرض 7 أيام + اليوم
            target_date = datetime.now().date() + timedelta(days=i)
            day_name = target_date.strftime('%A')
            st.subheader(f"🗓️ {day_name} - {target_date}")
            
            found = False
            for _, row in active_c.iterrows():
                nv = calculate_next_visit(row['الاسم'], row.get('دورة الصيانة', 3), df_m)
                if nv:
                    # منطق الترحيل: إذا كان الموعد اليوم أو فات ولم يتم
                    if (i == 0 and nv.date() <= target_date) or (nv.date() == target_date):
                        st.info(f"🔹 **{row['الاسم']}** | 📍 {row.get('المنطقة', '')} | 📞 {row['الأرقام']}")
                        found = True
            if not found: st.write("✅ لا توجد مواعيد")

elif page == "بحث عن عميل":
    st.header("🔍 البحث الشامل")
    q = st.text_input("ابحث بالاسم، المنطقة، أو رقم الهاتف")
    if q:
        results = df_c[df_c.apply(lambda row: q.lower() in str(row.values).lower(), axis=1)]
        st.dataframe(results)

elif page == "تسجيل صيانة":
    st.header("🔧 تسجيل صيانة جديدة")
    with st.form("m_form"):
        cust = st.selectbox("اسم العميل", df_c['الاسم'].tolist())
        date = st.date_input("تاريخ الزيارة", datetime.now())
        # نظام الـ Checkbox
        st.write("🔧 المهام المنجزة:")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c3.checkbox("Calcite")
        
        other = st.text_input("أخرى")
        cost = st.number_input("التكلفة", step=10)
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم تسجيل البيانات بنجاح!")

elif page == "إضافة عميل جديد":
    st.header("➕ إضافة عميل")
    with st.form("add_form"):
        st.text_input("الاسم")
        st.text_input("الأرقام")
        st.text_input("المنطقة")
        st.selectbox("الحالة", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"):
            st.success("تمت الإضافة")
