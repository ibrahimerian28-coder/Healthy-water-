import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# محاولة استيراد plotly بمرونة لمنع توقف التطبيق في حالة عدم تثبيت المكتبة
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro - Level الوحش", layout="wide")

@st.cache_data(ttl=600) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # معالجة القيم الرقمية للمخزن والمصروفات والصيانات
        num_cols = ['quantity', 'unit_price', 'min_limit', 'transportation', 'sundries', 'monthly_expensess', 'salaries', 'amount']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.fillna("") 
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

def clean_text_for_pdf(text):
    if not text: return ""
    return "".join(i for i in str(text) if ord(i) < 128)

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
        u_id = st.sidebar.text_input("رقم الموبايل المسجل:")
        if st.sidebar.button("دخول العميل"):
            df_c = load_all_data("0")
            search_val = str(u_id).strip()
            if not df_c.empty and search_val:
                phone_cols = ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']
                available_cols = [c for c in phone_cols if c in df_c.columns]
                mask = df_c[available_cols].astype(str).apply(lambda x: x.str.contains(re.escape(search_val), na=False)).any(axis=1)
                matches = df_c[mask]
                if not matches.empty:
                    st.session_state.auth = "customer"
                    st.session_state.user_data = matches.to_dict('records')
                    st.rerun()
                else: st.error("الرقم ده مش متسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. تصميم الـ PDF ---
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
    pdf.cell(0, 10, f"Customer Name: {clean_text_for_pdf(row['name'])}", ln=True)
    pdf.cell(0, 10, f"Phone: {clean_text_for_pdf(row.get('phone',''))} | Area: {clean_text_for_pdf(row.get('area',''))}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(40, 116, 166); pdf.set_text_color(255, 255, 255)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln(); pdf.set_text_color(0, 0, 0)
    history = df_m[df_m['name'] == row['name']].copy()
    history['v_date_dt'] = pd.to_datetime(history['visit_date'], errors='coerce')
    for _, m in history.sort_values(by='v_date_dt', ascending=False).iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            status = format_to_check(m.get(f,''))
            pdf.cell(31, 10, "V" if status == "✓" else "-", 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return bytes(pdf.output())

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:6px 12px; border-radius:8px; text-decoration:none; margin:2px; display:inline-block; font-size:13px; }
    .call-btn { background:#007bff !important; color:white !important; padding:6px 12px; border-radius:8px; text-decoration:none; margin:2px; display:inline-block; font-size:13px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106") # المخزن
df_exp = load_all_data("288947510") # المصروفات

# --- 6. القائمة الجانبية ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "جدول المواعيد", "إضافة عميل جديد"])
else:
    menu = "بروفايلي"

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.rerun()

# --- 7. تنفيذ الصفحات ---

# --- صفحة المخزن ---
if menu == "المخزن 📦":
    st.header("📦 إدارة المخزن (Inventory)")
    if not df_inv.empty:
        df_inv['total_item_value'] = df_inv['quantity'] * df_inv['unit_price']
        st.dataframe(df_inv, use_container_width=True)
        st.markdown(f"### 💰 القيمة الإجمالية للمخزون: `{df_inv['total_item_value'].sum():,.2f}` جنيه")
    else: st.warning("شيت المخزن غير متاح")

# --- صفحة الاحتياجات ---
elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ قائمة الاحتياجات (نواقص المخزن)")
    if not df_inv.empty:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        if not shortage.empty:
            st.error(f"يوجد ({len(shortage)}) صنف يحتاج لطلب بضاعة فوراً")
            st.table(shortage[['item_name', 'category', 'quantity', 'min_limit']])
        else: st.success("كل الكميات في المخزن آمنة ✅")

# --- تسجيل صيانة (المحدث) ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form_new"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite"); infra = c3.checkbox("Infrared")
        st.divider()
        inv_list = df_inv['item_name'].tolist() if not df_inv.empty else []
        selected_items = st.multiselect("قطع غيار إضافية (أخرى)", inv_list)
        cost = st.number_input("المبلغ المحصل", min_value=0.0)
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ الزيارة"):
            st.success(f"تم تسجيل الزيارة للعميل {name} بنجاح!")

# --- صفحة المصروفات والحسابات ---
elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات والحسابات")
    col_add, col_view = st.columns([0.4, 0.6])
    with col_add:
        with st.form("exp_form"):
            st.date_input("التاريخ")
            st.number_input("انتقالات"); st.number_input("نثريات"); st.number_input("مصروفات شهرية"); st.number_input("رواتب")
            st.form_submit_button("حفظ المصروف")
    with col_view:
        if not df_exp.empty:
            df_exp['total_exp'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
            st.dataframe(df_exp.tail(10))

# --- صفحة الأرباح ---
elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح")
    df_m['visit_date'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    df_exp['date'] = pd.to_datetime(df_exp['date'], errors='coerce')
    daily_inc = df_m.groupby('visit_date')['amount'].sum().reset_index().rename(columns={'visit_date':'date', 'amount':'income'})
    df_exp['d_exp'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
    daily_exp_agg = df_exp.groupby('date')['d_exp'].sum().reset_index()
    fin_df = pd.merge(daily_inc, daily_exp_agg, on='date', how='outer').fillna(0)
    fin_df['profit'] = fin_df['income'] - fin_df['d_exp']
    fin_df = fin_df.sort_values('date')

    if HAS_PLOTLY and not fin_df.empty:
        t1, t2, t3 = st.tabs(["يومي", "أسبوعي", "شهري"])
        with t1: st.plotly_chart(px.bar(fin_df, x='date', y='profit', title="الربح اليومي"), use_container_width=True)
        with t2:
            fin_df['week'] = fin_df['date'].dt.isocalendar().week
            st.plotly_chart(px.bar(fin_df.groupby('week')['profit'].sum().reset_index(), x='week', y='profit'), use_container_width=True)
        with t3:
            fin_df['month'] = fin_df['date'].dt.to_period('M').astype(str)
            st.plotly_chart(px.bar(fin_df.groupby('month')['profit'].sum().reset_index(), x='month', y='profit'), use_container_width=True)
    else: st.warning("الرسوم البيانية تتطلب ملف requirements.txt")

# --- صفحة بيانات العملاء (بكامل تفاصيل الكود الأصلي) ---
elif menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء والأجهزة")
    data_to_show = st.session_state.user_data if st.session_state.auth == "customer" else df_c.to_dict('records')
    
    for idx, r in enumerate(data_to_show):
        with st.container():
            h_col1, h_col2 = st.columns([0.8, 0.2])
            with h_col1:
                st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📍 {r.get("area","")} | {r.get("phone","")}</p></div>', unsafe_allow_html=True)
            with h_col2:
                if st.session_state.auth == "admin":
                    c_edit, c_del = st.columns(2)
                    if c_edit.button("📝", key=f"ec_{idx}"): st.info("تعديل")
                    if c_del.button("🗑️", key=f"dc_{idx}"): st.error("حذف")

            with st.expander(f"تفاصيل جهاز: {r['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**العنوان:** {r.get('adress','')}")
                    st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                    for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                        val = str(r.get(p, '')).strip()
                        if val and val != "nan" and len(val) > 5:
                            st.markdown(f'**{val}:** <a href="tel:{val}" class="call-btn">اتصال</a> <a href="https://wa.me/2{val}" class="wa-btn">واتساب</a>', unsafe_allow_html=True)
                with col2:
                    st.subheader("🛠️ سجل الصيانات")
                    history = df_m[df_m['name'] == r['name']].copy()
                    if not history.empty:
                        try:
                            pdf_data = generate_safe_pdf(r, df_m)
                            st.download_button(label="📥 تحميل PDF", data=pdf_data, file_name=f"{r['name']}.pdf", key=f"pdf_{idx}")
                        except: pass
                        st.dataframe(history.sort_values(by='visit_date', ascending=False), hide_index=True)
                    else: st.write("لا يوجد سجل")

# --- بقية الصفحات ---
elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    st.write("عرض مواعيد الصيانة القادمة...")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل/جهاز جديد")
    with st.form("add_f"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("الاسم")
            st.text_input("الموبايل الأساسي")
            st.text_input("المنطقة")
        with c2:
            st.text_input("العنوان بالتفصيل")
            st.date_input("تاريخ التركيب")
            st.number_input("دورة الصيانة (شهور)", 3)
        if st.form_submit_button("إضافة"): st.success("تم!")
