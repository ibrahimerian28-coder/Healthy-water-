import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=60)
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        # تنظيف أسماء الأعمدة من أي مسافات زائدة
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'نعم'] else "✗"

# --- 2. نظام تسجيل الدخول (أدمن / عميل) ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'user_data' not in st.session_state: st.session_state.user_data = None

def login_page():
    st.title("💧 نظام Healthy Water Pro")
    tab1, tab2 = st.tabs(["دخول الإدارة (Admin)", "دخول العملاء (Client)"])
    
    with tab1:
        pwd = st.text_input("كلمة مرور الأدمن", type="password")
        if st.button("دخول كمسؤول"):
            if pwd == "HgM18082019$&)":
                st.session_state.auth = "admin"
                st.rerun()
            else: st.error("كلمة المرور خاطئة")
            
    with tab2:
        client_phone = st.text_input("أدخل رقم الهاتف المسجل لدينا")
        if st.button("دخول العميل"):
            df_c = load_all_data("0")
            # البحث عن العميل باستخدام أول رقم تليفون (أو احتواء الرقم)
            match = df_c[df_c['phone'].astype(str).str.contains(client_phone)] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل لدينا")

if st.session_state.auth is None:
    login_page()
    st.stop()

# --- 3. التنسيق المرئي (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f8f9fa; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .phone-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .call-link { background-color: #007bff; color: white !important; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    .wa-link { background-color: #25d366; color: white !important; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. محرك المواعيد الذكي ---
def get_v_info(name, cycle, df_m):
    if df_m.empty or 'name' not in df_m.columns: return None
    c_m = df_m[df_m['name'].astype(str).str.strip() == str(name).strip()].copy()
    if c_m.empty: return None
    c_m['dt'] = pd.to_datetime(c_m['visit_date'], errors='coerce')
    last = c_m['dt'].max()
    if pd.isnull(last): return None
    try: return last + timedelta(days=int(cycle)*30)
    except: return None

# --- 5. تصدير PDF ---
def make_comprehensive_pdf(row, df_m):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Customer: {str(row['name'])}", ln=True)
    pdf.ln(5)
    check_cols = ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']
    headers = ["Date"] + check_cols + ["Cost"]
    for h in headers: pdf.cell(32, 10, h, 1, 0, 'C')
    pdf.ln()
    for _, m in df_m.iterrows():
        pdf.cell(32, 10, str(m.get('visit_date',''))[:10], 1)
        for c in check_cols:
            pdf.cell(32, 10, "V" if format_to_check(m.get(c, '')) == "✓" else "X", 1)
        pdf.cell(32, 10, str(m.get('amount','0')), 1)
        pdf.ln()
    return bytes(pdf.output())

# --- 6. تحميل البيانات ---
df_customers = load_all_data("0")
df_maint = load_all_data("2120582392")

# --- 7. القائمة الجانبية بناءً على نوع المستخدم ---
st.sidebar.title("Healthy Water 💧")
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("القائمة الرئيسية:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "تسجيل صيانة", "إضافة عميل جديد"])
else:
    menu = "ملفي الشخصي"
    st.sidebar.info(f"مرحباً: {st.session_state.user_data['name']}")

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.auth = None
    st.rerun()

# --- 8. الصفحات ---

if menu == "بيانات العملاء" or menu == "ملفي الشخصي":
    st.header("📋 سجل العملاء")
    # إذا كان عميل يرى بياناته فقط، إذا كان أدمن يرى الجميع
    display_df = pd.DataFrame([st.session_state.user_data]) if st.session_state.auth == "customer" else df_customers
    
    if not display_df.empty:
        for idx, row in display_df.iterrows():
            nv = get_v_info(row['name'], row.get('cycle', 3), df_maint)
            st.markdown(f"""
            <div class="cust-card">
                <h3 style="margin:0;">👤 {row['name']}</h3>
                <p style="margin:5px 0;">📍 {row.get('area', '---')} | 📅 موعد الصيانة القادم: <b>{nv.date() if nv else 'غير محدد'}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"فتح ملف التفاصيل", expanded=(st.session_state.auth == "customer")):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**العنوان:** {row.get('adress','')}")
                    st.write(f"**تاريخ التركيب:** {row.get('setup_date','')}")
                    st.write(f"**الدورة:** كل {row.get('cycle',3)} شهور")
                    # أزرار الاتصال
                    nums = re.findall(r'01[0-2,5]\d{8}', str(row.get('phone','')))
                    for n in nums:
                        st.markdown(f'<div class="phone-container"><a href="tel:{n}" class="call-link">📞 اتصال {n}</a><a href="https://wa.me/2{n}" class="wa-link">💬 واتساب</a></div>', unsafe_allow_html=True)
                with c2:
                    st.subheader("🛠️ سجل الصيانات")
                    cust_m = df_maint[df_maint['name'] == row['name']].copy()
                    if not cust_m.empty:
                        cust_m['visit_date'] = pd.to_datetime(cust_m['visit_date'], errors='coerce')
                        st.dataframe(cust_m.sort_values(by='visit_date', ascending=False))
                        st.download_button("📥 تحميل PDF", make_comprehensive_pdf(row, cust_m), f"{row['name']}.pdf")

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد القادمة")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗓️ صيانة دورية (أسبوع قادم)")
        for i in range(8):
            day = datetime.now().date() + timedelta(days=i)
            found = False
            for _, row in df_customers[df_customers.get('status') == 'نشط'].iterrows():
                nv = get_v_info(row['name'], row.get('cycle', 3), df_maint)
                if nv and nv.date() == day:
                    st.info(f"🔹 {row['name']} | 📍 {row['area']}")
                    found = True

    with col2:
        st.subheader("🔔 تنبيهات خاصة (Special Reminders)")
        if 'Special_reminder_date' in df_maint.columns:
            df_maint['rem_dt'] = pd.to_datetime(df_maint['Special_reminder_date'], errors='coerce')
            upcoming_special = df_maint[df_maint['rem_dt'].dt.date >= datetime.now().date()]
            if not upcoming_special.empty:
                for _, s_row in upcoming_special.iterrows():
                    st.warning(f"📌 {s_row['rem_dt'].date()} : **{s_row['name']}** \n\n {s_row.get('other', 'لا توجد ملاحظات')}")
            else: st.write("لا توجد مواعيد استثنائية قريباً")

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة جديدة")
    with st.form("m_form"):
        c_name = st.selectbox("اسم العميل", df_customers['name'].tolist())
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        
        st.divider()
        other = st.text_input("إضافات أخرى (Other)")
        special_date = st.date_input("تاريخ زيارة استثنائية (Special reminder date)", value=None)
        cost = st.number_input("التكلفة (amount)", step=10)
        notes = st.text_area("ملاحظات")
        
        if st.form_submit_button("حفظ الزيارة"):
            st.success("تم التجهيز للحفظ. تأكد من ربط هذا الفورم بـ Google Sheets API")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل")
    with st.form("add_client"):
        st.text_input("Name")
        st.text_input("Phone")
        st.text_input("Area")
        st.number_input("Cycle", 3)
        st.form_submit_button("إضافة")

elif menu == "بحث عن عميل":
    query = st.text_input("ابحث بالاسم أو الرقم أو المنطقة")
    if query:
        res = df_customers[df_customers.apply(lambda r: query.lower() in str(r.values).lower(), axis=1)]
        st.dataframe(res)
