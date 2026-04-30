import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px

# --- 1. الإعدادات والروابط المركزية ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxfVHx-0xlBE64oIS8DzQ0SXaw8AFXThOUQLiFEyqWcoEWGhgmbW6UAIakuZYiU6T8TaA/exec"
LOGO_PATH = "logo.png"
ADMIN_PASSWORD = "HgM18082019$&)"
COMPANY_PHONE = "01286609535"

st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="🚰")

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

# معالجة التواريخ والأرقام فور التحميل لضمان دقة الحسابات
if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)
if not df_exp.empty:
    df_exp['exp_date_dt'] = df_exp['date'].apply(parse_dt)
    df_exp['total_exp_num'] = df_exp['notes'].apply(to_num) # نفترض أن notes يخزن الإجمالي

# --- 4. وظيفة توليد الـ PDF الاحترافي ---
def generate_customer_pdf(cust_row, history_df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    try: pdf.image(LOGO_PATH, x=10, y=10, w=35)
    except: pass
    pdf.set_font("Arial", 'B', 16)
    # تحويل النصوص لتجنب خطأ التشفير للغة العربية
    safe_name = str(cust_row['name']).encode('latin-1', 'replace').decode('latin-1')
    safe_address = str(cust_row.get('adress', '')).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.cell(0, 10, f"Customer Maintenance Report: {safe_name}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Address: {safe_address} | Phone: {cust_row['phone']}", ln=True)
    pdf.ln(5)
    
    cols = ['Date', 'P1', 'P2', 'P3', 'Mem', 'Post', 'Calc', 'Infra', 'Amount', 'Notes']
    widths = [25, 12, 12, 12, 12, 12, 12, 12, 20, 140]
    pdf.set_fill_color(200, 200, 200); pdf.set_font("Arial", 'B', 10)
    for i, c in enumerate(cols): pdf.cell(widths[i], 10, c, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", '', 9)
    for _, r in history_df.iterrows():
        pdf.cell(widths[0], 10, str(r['visit_date']), 1)
        for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            # وضع حرف x بدلا من صح، وتركها فارغة بدلا من خطأ لتجنب مشاكل PDF
            val = "x" if str(r.get(part, '')).lower() in ['true', '1'] else ""
            pdf.cell(12, 10, val, 1, 0, 'C')
        
        pdf.cell(widths[8], 10, str(r['amount']), 1, 0, 'C')
        safe_notes = str(r['notes'])[:80].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(widths[9], 10, safe_notes, 1, 1)
    return pdf.output(dest='S').encode('latin-1', errors='ignore')
    
    cols = ['Date', 'P1', 'P2', 'P3', 'Mem', 'Post', 'Calc', 'Infra', 'Amount', 'Notes']
    widths = [25, 12, 12, 12, 12, 12, 12, 12, 20, 140]
    pdf.set_fill_color(200, 200, 200); pdf.set_font("Arial", 'B', 10)
    for i, c in enumerate(cols): pdf.cell(widths[i], 10, c, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", '', 9)
    for _, r in history_df.iterrows():
        pdf.cell(widths[0], 10, str(r['visit_date']), 1)
        for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            val = "V" if str(r.get(part,'')).lower() == 'true' else "-"
            pdf.cell(12, 10, val, 1, 0, 'C')
        pdf.cell(widths[8], 10, str(r['amount']), 1, 0, 'C')
        pdf.cell(widths[9], 10, str(r['notes'])[:80], 1, 1)
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- 5. نظام الدخول ---
if 'user_type' not in st.session_state: st.session_state.user_type = None

if st.session_state.user_type is None:
    st.title("🚰 Healthy Water System")
    t1, t2 = st.tabs(["🔒 الأدمن", "👤 العميل"])
    with t1:
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.user_type = "admin"; st.rerun()
    with t2:
        phone = st.text_input("رقم الهاتف")
        if st.button("دخول العميل"):
            match = df_c[df_c[['phone','phone_1','phone_2','phone_3','phone_4']].astype(str).apply(lambda x: x.str.contains(phone)).any(axis=1)]
            if not match.empty:
                st.session_state.user_type = "customer"; st.session_state.customer_data = match; st.rerun()

# --- 6. واجهة الأدمن ---
elif st.session_state.user_type == "admin":
    st.sidebar.image(LOGO_PATH, use_column_width=True) # إضافة اللوجو للقائمة الجانبية
    menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "المصروفات", "الأرباح 📈"])

    if menu == "بيانات العملاء":
        st.header("👥 إدارة العملاء")
        search = st.text_input("🔍 بحث بالاسم، رقم الهاتف، أو المنطقة")
        
        # فلترة البحث الشاملة
        if search:
            filtered = df_c[df_c.apply(lambda r: search in str(r.get('name','')) or search in str(r.get('phone','')) or search in str(r.get('area','')), axis=1)]
        else:
            filtered = df_c
        
        for area, group in filtered.groupby('area'):
            st.subheader(f"📍 {area}")
            for _, r in group.iterrows():
                with st.expander(f"👤 {r['name']}"):
                    c1, c2 = st.columns(2)
                    addr = r.get('adress', '')
                    c1.write(f"🏠 العنوان: {addr if addr else 'غير مسجل'}")
                    c1.write(f"🗺️ اللوكيشن: {r.get('location', 'غير مسجل')}")
                    c1.write(f"🔄 الدورة: {r['cycle']} شهر")
                    
                    # أزرار الاتصال والواتساب الملونة
                    phones = [r.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if p in r and str(r.get(p)).strip() != ""]
                    for ph in phones:
                        html_buttons = f"""
                        <div style='display: flex; gap: 10px; margin-bottom: 5px;'>
                            <span style='padding: 5px; font-weight: bold;'>📞 {ph}</span>
                            <a href='tel:{ph}' style='background-color: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 5px;'>اتصال 📞</a>
                            <a href='https://wa.me/{ph}' target='_blank' style='background-color: #25D366; color: white; padding: 5px 10px; text-decoration: none; border-radius: 5px;'>واتساب 💬</a>
                        </div>
                        """
                        c2.markdown(html_buttons, unsafe_allow_html=True)
                    
                    st.divider()
                    st.write("**🛠️ جدول الصيانات:**")
                    hist = df_m[df_m['name'] == r['name']].sort_values('v_date_dt', ascending=False).copy()
                    
                    # تحويل True/False إلى صح وخطأ
                    bool_cols = ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']
                    for bc in bool_cols:
                        if bc in hist.columns:
                            hist[bc] = hist[bc].apply(lambda x: "✅" if str(x).lower() == 'true' else "❌")
                    
                    # عرض كل الأعمدة
                    display_cols = [c for c in hist.columns if c not in ['v_date_dt', 'amount_num', 'row_index_internal', 'month']]
                    st.dataframe(hist[display_cols], use_container_width=True)
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    if col_btn1.button("📄 تحميل PDF", key=f"pdf_{r['row_index_internal']}"):
                        st.download_button("تأكيد التحميل", generate_customer_pdf(r, hist), f"{r['name']}.pdf")
                    
                    # أزرار الحذف والتعديل مع تحذير
                    if col_btn2.button("✏️ تعديل بيانات العميل", key=f"edit_{r['row_index_internal']}"):
                        st.warning("لتفعيل التعديل، يرجى ربط دالة Update مع Google Script.")
                    
                    if col_btn3.button("🗑️ حذف العميل", key=f"del_{r['row_index_internal']}", type="primary"):
                        st.error("⚠️ تحذير: هل أنت متأكد من الحذف النهائي؟ (يجب ربط زر التأكيد بالسكريبت)")
    # 6.2 جدول المواعيد 📅 (مواعيد الأسبوع القادم فقط)
    elif menu == "جدول المواعيد 📅":
        st.header("📅 جدول مواعيد الأسبوع القادم")
        today_date = datetime.now().date()
        next_week_date = today_date + timedelta(days=7)
        upcoming_list = []
        
        for _, cust in df_c.iterrows():
            last_m = df_m[df_m['name'] == cust['name']].sort_values('v_date_dt').iloc[-1:]
            if not last_m.empty:
                last_v = last_m.iloc[0]['v_date_dt']
                spec_date = parse_dt(last_m.iloc[0].get('spec_date', ""))
                next_v = spec_date if pd.notna(spec_date) else last_v + timedelta(days=to_num(cust['cycle'])*30)
                
                # إضافة الشرط: يظهر فقط إذا كان الموعد القادم خلال 7 أيام من اليوم
                if today_date <= next_v.date() <= next_week_date:
                    upcoming_list.append({'العميل': cust['name'], 'المنطقة': cust['area'], 'الهاتف': cust['phone'], 'الموعد القادم': next_v.date()})
        
        if upcoming_list:
            up_df = pd.DataFrame(upcoming_list).sort_values('الموعد القادم')
            st.table(up_df)
        else:
            st.info("لا توجد مواعيد صيانة مجدولة خلال السبعة أيام القادمة.")

    # 6.3 تسجيل صيانة
    elif menu == "تسجيل صيانة":
        st.header("🔧 إضافة صيانة")
        with st.form("m_form"):
            name = st.selectbox("الاسم", df_c['name'].tolist())
            date = st.date_input("التاريخ")
            col1, col2, col3 = st.columns(3)
            p1 = col1.checkbox("P1"); p2 = col1.checkbox("P2"); p3 = col1.checkbox("P3")
            mem = col2.checkbox("Membrane"); pc = col2.checkbox("Post Carbon")
            calc = col3.checkbox("Calcite"); infra = col3.checkbox("Infrared")
            other = st.text_input("قطع أخرى")
            amt = st.number_input("المبلغ", step=1)
            nts = st.text_area("ملاحظات")
            spec = st.date_input("موعد استثنائي قادم (اختياري)", value=None)
            if st.form_submit_button("حفظ"):
                execute_gsheet_action("append", "Maintenance", [name, str(date), p1, p2, p3, mem, pc, calc, infra, other, amt, nts, str(spec)])
                st.success("تم الحفظ!")

    # 6.4 المخزن 📦
    elif menu == "المخزن 📦":
        st.header("📦 حالة المخزن وقيمة رأس المال")
        total_capital = 0
        
        for index, row in df_inv.iterrows():
            with st.expander(f"⚙️ {row['item_name']} - الكمية: {row['quantity']}"):
                with st.form(f"inv_form_{index}"):
                    c1, c2, c3, c4 = st.columns(4)
                    new_name = c1.text_input("اسم العنصر", value=row['item_name'])
                    new_qty = c2.number_input("الكمية المتاحة", value=to_num(row['quantity']))
                    new_cost = c3.number_input("سعر التكلفة", value=to_num(row.get('cost_price', 0)))
                    new_min = c4.number_input("الحد الأدنى (Min Limit)", value=to_num(row.get('min_limit', 0)))
                    
                    item_total_value = new_qty * new_cost
                    total_capital += item_total_value
                    
                    st.write(f"**إجمالي قيمة هذا العنصر في المخزن:** {item_total_value} ج.م")
                    
                    if new_qty <= new_min:
                        st.error("🚨 الرصيد وصل للحد الأدنى أو أقل!")
                        
                    if st.form_submit_button("تحديث العنصر 🔄"):
                        # هنا نرسل أمر التحديث لجوجل شيت
                        execute_gsheet_action("update", "Inventory", [new_name, new_qty, new_cost, new_min], row_index=row['row_index_internal'])
                        st.success("تم إرسال طلب التحديث! (قم بتحديث الصفحة)")
        
        st.divider()
        st.success(f"💰 **إجمالي قيمة رأس المال بالمخزن:** {total_capital} ج.م")

    # 6.5 المصروفات 💵
    elif menu == "المصروفات":
        st.header("💵 إدارة المصروفات")
        selected_date = st.date_input("اختر التاريخ للبحث أو التسجيل", datetime.now().date())
        
        # عرض المصروفات المسجلة في هذا التاريخ
        day_expenses = df_exp[df_exp['exp_date_dt'].dt.date == selected_date]
        if not day_expenses.empty:
            st.info(f"المصروفات المسجلة مسبقاً ليوم {selected_date}:")
            st.dataframe(day_expenses)
        
        with st.form("exp"):
            st.write("تسجيل مصروفات جديدة / تحديث:")
            c1, c2 = st.columns(2)
            spare_cost = c1.number_input("تكلفة قطع الغيار المستخدمة", step=1)
            salaries = c2.number_input("رواتب / يوميات", step=1)
            monthly_exp = c1.number_input("مصروفات شهرية (إيجار، فواتير)", step=1)
            trans = c2.number_input("انتقالات / نثريات", step=1)
            notes = st.text_area("ملاحظات")
            
            tot = spare_cost + salaries + monthly_exp + trans
            st.write(f"**الإجمالي المحسوب:** {tot} ج.م")
            
            if st.form_submit_button("حفظ / تحديث المصروفات"):
                # الأعمدة المتوقعة في جوجل شيت: date, spare_parts, salaries, monthly_exp, trans, total, notes
                execute_gsheet_action("append", "Expenses", [str(selected_date), spare_cost, salaries, monthly_exp, trans, tot, notes])
                st.success("تم حفظ المصروفات (وستنعكس تلقائياً في صفحة الأرباح)!")

    # 6.6 الأرباح (تطوير شامل)
    elif menu == "الأرباح 📈":
        st.header("📈 تقارير الأرباح والنمو")
        
        # تجميع البيانات
        daily_inc = df_m.groupby(df_m['v_date_dt'].dt.date)['amount_num'].sum()
        daily_exp = df_exp.groupby(df_exp['exp_date_dt'].dt.date)['total_exp_num'].sum()
        
        # حسابات الفترات
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        def calc_profit(start_date):
            inc = daily_inc[daily_inc.index >= start_date].sum()
            exp = daily_exp[daily_exp.index >= start_date].sum()
            return inc - exp

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ربح اليوم", f"{daily_inc.get(today, 0) - daily_exp.get(today, 0)} ج.م")
        m2.metric("ربح الأسبوع", f"{calc_profit(week_ago)} ج.م")
        m3.metric("ربح الشهر", f"{calc_profit(month_start)} ج.م")
        m4.metric("ربح السنة", f"{calc_profit(year_start)} ج.م")
        
        # الرسوم البيانية
        st.subheader("📊 تحليل بياني")
        chart_type = st.selectbox("عرض حسب:", ["يومي", "شهري"])
        if chart_type == "يومي":
            fig = px.bar(daily_inc, title="الدخل اليومي")
        else:
            df_m['month'] = df_m['v_date_dt'].dt.strftime('%Y-%m')
            fig = px.line(df_m.groupby('month')['amount_num'].sum(), title="الدخل الشهري")
        st.plotly_chart(fig, use_container_width=True)

    if st.sidebar.button("خروج"):
        st.session_state.user_type = None; st.rerun()

# --- 7. واجهة العميل ---
elif st.session_state.user_type == "customer":
    st.title("👋 أهلاً بك في Healthy Water")
    for _, row in st.session_state.customer_data.iterrows():
        st.info(f"العميل: {row['name']} | العنوان: {row['adress']}")
        hist = df_m[df_m['name'] == row['name']].sort_values('v_date_dt', ascending=False)
        st.subheader("🛠️ تاريخ صياناتك")
        st.table(hist[['visit_date', 'notes']])
    
    st.divider()
    st.link_button("📞 اتصل بالدعم", f"tel:{COMPANY_PHONE}")
    if st.button("خروج"): st.session_state.user_type = None; st.rerun()
