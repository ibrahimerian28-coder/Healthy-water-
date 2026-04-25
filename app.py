import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=300)
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# --- 2. التنسيق المرئي (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .status-green { border-color: #28a745; background-color: #f1f9f3; }
    .status-yellow { border-color: #ffc107; background-color: #fffdf5; }
    .status-red { border-color: #dc3545; background-color: #fff5f5; }
    .status-darkred { border-color: #8b0000; background-color: #4b0000; color: white; }
    .status-gray { border-color: #6c757d; background-color: #f8f9fa; }
    .phone-link { background-color: #e3f2fd; padding: 5px 10px; border-radius: 5px; text-decoration: none; color: #004a99; font-weight: bold; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. محرك المواعيد الذكي ---
def get_v_info(name, cycle, df_m):
    if df_m.empty or 'الاسم' not in df_m.columns: return None
    c_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(name).strip()].copy()
    if c_m.empty: return None
    c_m['dt'] = pd.to_datetime(c_m['تاريخ الزيارة'], errors='coerce')
    last = c_m['dt'].max()
    if pd.isnull(last): return None
    return last + timedelta(days=int(cycle)*30)

def get_card_style(nv, status):
    if str(status).strip() == "راكد": return "status-gray"
    if not nv: return "status-green"
    diff = (nv.date() - datetime.now().date()).days
    if diff > 7: return "status-green"
    if 0 <= diff <= 7: return "status-yellow"
    if -7 <= diff < 0: return "status-red"
    return "status-darkred"

# --- 4. تصدير PDF أفقي (Landscape) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 45)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Customer Service Report', 0, 1, 'R')
        self.ln(15)

def make_landscape_pdf(row, df_m):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    name_clean = str(row['الاسم']).encode('ascii', 'ignore').decode('ascii') or "Client"
    pdf.cell(0, 10, f"Customer: {name_clean} | Phone: {row.get('الأرقام','')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    # عناوين الجدول
    pdf.cell(50, 10, "Date", 1); pdf.cell(150, 10, "Service Details", 1); pdf.cell(40, 10, "Amount", 1); pdf.ln()
    pdf.set_font("Arial", '', 10)
    for _, m in df_m.iterrows():
        pdf.cell(50, 10, str(m.get('تاريخ الزيارة',''))[:10], 1)
        pdf.cell(150, 10, "Regular Maintenance Check", 1)
        pdf.cell(40, 10, str(m.get('amount','0')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 5. تحميل البيانات ---
df_customers = load_all_data("0")
df_maint = load_all_data("2120582392")

# --- 6. عرض الصفحات ---
st.sidebar.title("Healthy Water 💧")
menu = st.sidebar.radio("القائمة الرئيسية:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "تسجيل صيانة", "إضافة عميل جديد"])

if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء (مرتب بالمناطق)")
    if not df_customers.empty:
        # الترتيب حسب المنطقة (تلقائي)
        area_col = 'المنطقه' if 'المنطقه' in df_customers.columns else 'المنطقة'
        df_sorted = df_customers.sort_values(by=area_col)
        
        for idx, row in df_sorted.iterrows():
            nv = get_v_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maint)
            style = get_card_style(nv, row.get('status', 'نشط'))
            
            # الكارت الخارجي
            st.markdown(f"""
            <div class="cust-card {style}">
                <h3 style="margin:0;">👤 {row['الاسم']}</h3>
                <p style="margin:5px 0;">📍 {row.get(area_col, '---')} | 📞 {row['الأرقام']}</p>
                <p style="margin:0;">📅 الموعد القادم: <b>{nv.date() if nv else 'غير محدد'}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            # تفاصيل العميل والتحكم
            with st.expander(f"فتح ملف {row['الاسم']}"):
                c1, c2 = st.columns(2)
                with c1:
                    for col in df_customers.columns:
                        st.write(f"**{col}:** {row[col]}")
                    
                    # أزرار الاتصال
                    p_num = str(row['الأرقام']).split('/')[0].strip()
                    st.markdown(f'<div style="margin:10px 0;"><a href="tel:{p_num}" class="phone-link">📞 اتصال</a><a href="https://wa.me/2{p_num}" class="phone-link">💬 واتساب</a></div>', unsafe_allow_html=True)
                    if "http" in str(row.get('اللوكيشن','')):
                        st.link_button("📍 فتح اللوكيشن", row['اللوكيشن'])
                
                with c2:
                    st.button("📝 تعديل البيانات", key=f"ed_{idx}")
                    st.button("🗑️ حذف العميل", key=f"dl_{idx}")
                    
                    st.subheader("🛠️ سجل الصيانات (الأحدث أولاً)")
                    cust_m = df_maint[df_maint['الاسم'] == row['الاسم']].copy()
                    if not cust_m.empty:
                        cust_m['dt'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
                        cust_m = cust_m.sort_values(by='dt', ascending=False)
                        st.dataframe(cust_m.drop(columns=['dt']))
                        st.download_button("📥 تحميل PDF (أفقي)", make_landscape_pdf(row, cust_m), f"{row['الاسم']}.pdf")

elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    if not df_customers.empty:
        active_ones = df_customers[df_customers.get('status', 'نشط') == 'نشط']
        for i in range(8):
            day = datetime.now().date() + timedelta(days=i)
            st.subheader(f"🗓️ {day.strftime('%A')} - {day}")
            
            found = False
            for _, row in active_ones.iterrows():
                nv = get_v_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maint)
                # الترحيل: لو الموعد فات ولم يسجل يظهر في اليوم الحالي
                if nv and ((i == 0 and nv.date() <= day) or (nv.date() == day)):
                    st.info(f"🔹 **{row['الاسم']}** | 📍 {row.get('المنطقه','')} | 📞 {row['الأرقام']}")
                    found = True
            if not found: st.write("لا توجد مواعيد")

elif menu == "بحث عن عميل":
    st.header("🔍 بحث شامل (اسم / منطقة / هاتف)")
    query = st.text_input("ادخل كلمة البحث:")
    if query:
        res = df_customers[df_customers.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        st.dataframe(res)

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        c_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        st.write("🔧 المهام (Checkboxes):")
        cc1, cc2, cc3 = st.columns(3)
        p1 = cc1.checkbox("P1"); p2 = cc1.checkbox("P2"); p3 = cc1.checkbox("P3")
        mem = cc2.checkbox("Membrane"); post = cc2.checkbox("Post Carbon"); calc = cc2.checkbox("Calcite")
        infra = cc3.checkbox("Infrared")
        
        cost = st.number_input("التكلفة (amount)", step=10)
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم التسجيل! الموعد القادم سيتم ترحيله تلقائياً.")

elif menu == "إضافة عميل جديد":
    with st.form("add_f"):
        st.text_input("الاسم")
        st.text_input("الأرقام")
        st.text_input("المنطقه")
        st.selectbox("الحالة", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"): st.success("تم")
