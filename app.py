import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import io
import base64

# --- 1. الإعدادات والروابط المركزية ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxfVHx-0xlBE64oIS8DzQ0SXaw8AFXThOUQLiFEyqWcoEWGhgmbW6UAIakuZYiU6T8TaA/exec"
LOGO_PATH = "logo.png"
ADMIN_PASSWORD = "HgM18082019$&)"
COMPANY_PHONE = "01286609535"

st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# --- 2. الدوال المساعدة ---
def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '').strip()))
    except: return 0

def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(WEB_APP_URL, json=payload, timeout=15)
        return response.status_code == 200
    except: return False

@st.cache_data(ttl=2)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        df['row_index_internal'] = range(2, len(df) + 2)
        return df.fillna("")
    except: return pd.DataFrame()

def parse_dt(val):
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

# --- 3. تحميل البيانات ---
df_c = load_data("0")          # Customers
df_m = load_data("2120582392") # Maintenance
df_inv = load_data("1767710106") # Inventory
df_exp = load_data("288947510")  # Expenses

if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

# --- 4. وظيفة توليد الـ PDF الاحترافي ---
def generate_customer_pdf(cust_row, history_df):
    pdf = FPDF(orientation='L', unit='mm', format='A4') # تنسيق أفقي
    pdf.add_page()
    
    # إضافة اللوجو (أعلى اليسار)
    try: pdf.image(LOGO_PATH, x=10, y=10, w=40)
    except: pdf.cell(40, 10, "LOGO MISSING", 1)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Customer Service Report - {cust_row['name']}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(100, 10, f"Customer Name: {cust_row['name']}", ln=0)
    pdf.cell(100, 10, f"Installation Date: {cust_row.get('install_date','')}", ln=1)
    pdf.ln(5)

    # جدول الصيانات
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(200, 200, 200)
    cols = ['Date', 'P1', 'P2', 'P3', 'Membrane', 'Post C', 'Calcite', 'Infrared', 'Other', 'Amount', 'Notes']
    col_widths = [25, 15, 15, 15, 20, 20, 20, 20, 30, 20, 60]
    
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 10, col, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", '', 9)
    fill = False
    for _, row in history_df.iterrows():
        if fill: pdf.set_fill_color(240, 240, 240)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(col_widths[0], 10, str(row['visit_date']), 1, 0, 'C', True)
        for part in ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']:
            val = "V" if str(row.get(part,'')).lower() == 'true' else "X"
            pdf.cell(15 if part in ['P1','P2','P3'] else 20, 10, val, 1, 0, 'C', True)
        
        pdf.cell(col_widths[8], 10, str(row.get('other','')), 1, 0, 'C', True)
        pdf.cell(col_widths[9], 10, str(row.get('amount','0')), 1, 0, 'C', True)
        pdf.cell(col_widths[10], 10, str(row.get('notes',''))[:30], 1, 0, 'C', True)
        pdf.ln()
        fill = not fill

    # الفوتر
    pdf.set_y(-30)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 10, f"Healthy Water - Phone: {COMPANY_PHONE}", align='C', link=f"tel:{COMPANY_PHONE}")
    
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- 5. نظام تسجيل الدخول ---
if 'user_type' not in st.session_state: st.session_state.user_type = None

if st.session_state.user_type is None:
    st.title("🚰 Healthy Water System")
    tab_admin, tab_cust = st.tabs(["🔒 دخول الأدمن", "👤 دخول العميل"])
    
    with tab_admin:
        pwd = st.text_input("كلمة السر", type="password", key="admin_pwd")
        if st.button("دخول كأدمن"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.user_type = "admin"
                st.rerun()
            else: st.error("كلمة السر غير صحيحة")
            
    with tab_cust:
        c_phone = st.text_input("رقم الهاتف المسجل", key="cust_phone")
        if st.button("دخول"):
            match = df_c[df_c[['phone','phone_1','phone_2','phone_3','phone_4']].apply(lambda x: x.astype(str).str.contains(c_phone)).any(axis=1)]
            if not match.empty:
                st.session_state.user_type = "customer"
                st.session_state.customer_data = match
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل لدينا")

# --- 6. واجهة العميل ---
elif st.session_state.user_type == "customer":
    st.title("👋 أهلاً بك في صفحتك الخاصة")
    for _, row in st.session_state.customer_data.iterrows():
        with st.expander(f"بيانات: {row['name']}", expanded=True):
            st.write(f"📍 المنطقة: {row['area']} | العنوان: {row['adress']}")
            history = df_m[df_m['name'] == row['name']].sort_values(by='v_date_dt', ascending=False)
            st.subheader("🛠️ سجل الصيانات الخاص بك")
            st.dataframe(history[['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'amount', 'notes']], hide_index=True)
            
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.link_button("📞 اتصل بنا", f"tel:{COMPANY_PHONE}")
    col2.link_button("💬 واتساب الشركة", f"https://wa.me/{COMPANY_PHONE}")
    col3.button("🔗 مشاركة التطبيق")
    if st.button("خروج"): 
        st.session_state.user_type = None
        st.rerun()

# --- 7. واجهة الأدمن (كافة الخصائص) ---
elif st.session_state.user_type == "admin":
    menu = st.sidebar.radio("التنقل", ["بيانات العملاء", "تسجيل صيانة", "المخزن 📦", "المصروفات والحسابات", "الأرباح 📈"])

    # 7.1 بيانات العملاء
    if menu == "بيانات العملاء":
        st.header("👥 إدارة العملاء")
        search = st.text_input("ابحث بالاسم، الهاتف، المنطقة، أو ID")
        
        filtered = df_c.copy()
        if search:
            filtered = filtered[filtered.apply(lambda row: search in str(row.values), axis=1)]
        
        filtered = filtered.sort_values(by=['area', 'name'])
        
        for area, group in filtered.groupby('area'):
            st.markdown(f"### 📍 منطقة: {area}")
            for _, r in group.iterrows():
                with st.expander(f"👤 {r['name']}"):
                    c1, c2 = st.columns(2)
                    c1.write(f"🏠 العنوان: {r['adress']}")
                    c1.write(f"🔄 الدورة: {r['cycle']} شهر")
                    c1.write(f"📅 تاريخ التركيب: {r['install_date']}")
                    
                    # هواتف العميل مع أزرار
                    for p in ['phone', 'phone_1', 'phone_2']:
                        if r[p]: 
                            st.write(f"📞 {r[p]} [اتصال](tel:{r[p]}) | [واتس](https://wa.me/{r[p]})")

                    # حساب الزيارة القادمة
                    cust_m = df_m[df_m['name'] == r['name']].sort_values('v_date_dt')
                    if not cust_m.empty:
                        last_v = cust_m.iloc[-1]['v_date_dt']
                        next_v = last_v + timedelta(days=to_num(r['cycle'])*30)
                        st.info(f"📅 موعد الزيارة القادمة: {next_v.date()}")

                    # جدول الصيانات للعميل
                    st.write("---")
                    st.write("📋 تاريخ الصيانات (من الأحدث)")
                    if not cust_m.empty:
                        m_hist = cust_m.sort_values('v_date_dt', ascending=False).copy()
                        for col in ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']:
                            m_hist[col] = m_hist[col].apply(lambda x: "✅" if str(x).lower() == 'true' else "❌")
                        st.dataframe(m_hist[['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared', 'other', 'amount', 'notes']], hide_index=True)
                    
                    # أزرار PDF والتعديل والحذف
                    col_p1, col_p2, col_p3 = st.columns(3)
                    if col_p1.button("📄 تحميل PDF", key=f"pdf_{r['row_index_internal']}"):
                        pdf_bytes = generate_customer_pdf(r, cust_m.sort_values('v_date_dt', ascending=False))
                        st.download_button("تحميل الملف", pdf_bytes, f"{r['name']}.pdf", "application/pdf")
                    
                    if col_p2.button("🗑️ حذف", key=f"del_{r['row_index_internal']}"):
                        if st.confirm("هل أنت متأكد من الحذف؟"):
                            execute_gsheet_action("delete", "Customers", row_index=r['row_index_internal'])
                            st.rerun()

    # 7.2 تسجيل صيانة
    elif menu == "تسجيل صيانة":
        st.header("🔧 إضافة زيارة صيانة")
        with st.form("m_form"):
            c_name = st.selectbox("العميل", df_c['name'].tolist())
            v_date = st.date_input("تاريخ الزيارة", datetime.now())
            
            st.write("الشمعات المبدلة:")
            col1, col2, col3 = st.columns(3)
            p1 = col1.checkbox("P1"); p2 = col1.checkbox("P2"); p3 = col1.checkbox("P3")
            mem = col2.checkbox("Membrane"); pc = col2.checkbox("Post Carbon")
            calc = col3.checkbox("Calcite"); infra = col3.checkbox("Infrared")
            
            others = ["لا يوجد"] + df_inv[~df_inv['item_name'].isin(['P1','P2','P3','membrane','post_carbon','Calcite','infrared'])]['item_name'].tolist()
            other_item = st.selectbox("قطع أخرى", others)
            
            amount = st.number_input("المبلغ المدفوع", step=1)
            notes = st.text_area("ملاحظات")
            spec_date = st.date_input("موعد استثنائي", value=None)
            
            if st.form_submit_button("حفظ"):
                data = [c_name, str(v_date), p1, p2, p3, mem, pc, calc, infra, other_item, amount, notes, str(spec_date), "", ""]
                execute_gsheet_action("append", "Maintenance", data)
                st.success("تم تسجيل الزيارة")

    # 7.3 المخزن
    elif menu == "المخزن 📦":
        st.header("📦 حالة المخزن")
        total_inv_value = 0
        for _, row in df_inv.iterrows():
            q = to_num(row['quantity'])
            p = to_num(row['cost_price'])
            val = q * p
            total_inv_value += val
            
            with st.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"**{row['item_name']}**")
                c2.write(f"الكمية: {q}")
                c3.write(f"التكلفة: {p}")
                c4.write(f"الإجمالي: {val}")
                if q <= to_num(row['min_limit']): st.error("⚠️ نقص في المخزن!")
                st.divider()
        st.metric("💰 إجمالي قيمة المخزن", f"{total_inv_value} ج.م")

    # 7.4 المصروفات والحسابات
    elif menu == "المصروفات والحسابات":
        st.header("💵 سجل المصروفات اليومي")
        target_date = st.date_input("التاريخ", datetime.now())
        
        # حساب أوتوماتيكي لتكلفة قطع الغيار المستخدمة اليوم
        daily_m = df_m[df_m['v_date_dt'].dt.date == target_date]
        auto_parts_cost = 0
        for _, m_row in daily_m.iterrows():
            for p in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                if str(m_row.get(p,'')).lower() == 'true':
                    inv_match = df_inv[df_inv['item_name'].str.lower() == p.lower()]
                    if not inv_match.empty: auto_parts_cost += to_num(inv_match.iloc[0]['cost_price'])
        
        st.info(f"تكلفة قطع غيار زيارات اليوم: {auto_parts_cost} ج.م")
        
        with st.form("exp_form"):
            trans = st.number_input("انتقالات", 0)
            sund = st.number_input("نثريات", 0)
            month = st.number_input("مصروفات شهرية", 0)
            sal = st.number_input("رواتب", 0)
            other = st.number_input("أخرى", 0)
            
            total_exp = auto_parts_cost + trans + sund + month + sal + other
            if st.form_submit_button("حفظ المصروفات"):
                exp_data = [str(target_date), trans, sund, month, sal, total_exp]
                execute_gsheet_action("append", "Expenses", exp_data)
                st.success(f"تم الحفظ. الإجمالي: {total_exp}")

    # 7.5 الأرباح والرسوم البيانية
    elif menu == "الأرباح 📈":
        st.header("📈 تقارير الأرباح والنمو")
        
        # حساب الأرباح
        def get_net_profit(date_obj):
            inc = to_num(df_m[df_m['v_date_dt'].dt.date == date_obj]['amount_num'].sum())
            exp = to_num(df_exp[df_exp['date'].apply(parse_dt).dt.date == date_obj]['notes'].sum()) # خانة الإجمالي مخزنة في notes
            return inc - exp

        sel_date = st.date_input("اختر تاريخ للعرض", datetime.now())
        st.metric("صافي الربح اليومي", f"{get_net_profit(sel_date)} ج.م")
        
        # الرسوم البيانية
        df_m['month'] = df_m['v_date_dt'].dt.strftime('%Y-%m')
        monthly_chart = df_m.groupby('month')['amount_num'].sum().reset_index()
        fig = px.line(monthly_chart, x='month', y='amount_num', title="تطور الدخل الشهري")
        st.plotly_chart(fig)

    if st.sidebar.button("خروج"):
        st.session_state.user_type = None
        st.rerun()
