import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import io

# --- 1. الإعدادات والروابط المركزية ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwSW9s7nKgp5_fPRh9P7a5UqJ84bYfJrs7jkwTkCVRAFvHY3DZEcQfZ0PBGY4ksapT-aw/exec"
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

@st.cache_data(ttl=1)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # إضافة row_index_internal ليتطابق مع ترتيب شيت الاكسيل (يبدأ من 2 لأن الصف 1 هو العناوين)
        df['row_index_internal'] = range(2, len(df) + 2)
        return df.fillna("")
    except: return pd.DataFrame()

def parse_dt(val):
    if not val or str(val).strip() == "": return None
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

# تحضير البيانات المالية والمواعيد
if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)
if not df_exp.empty:
    df_exp['exp_date_dt'] = df_exp['date'].apply(parse_dt)

# --- 4. وظيفة توليد الـ PDF (تصحيح AttributeError وتعديل التنسيق) ---
def generate_customer_pdf(cust_row, history_df):
    # استخدام التنسيق الأفقي 'L' كما طلبت
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # محاولة إضافة اللوجو
    try: pdf.image(LOGO_PATH, x=10, y=10, w=35)
    except: pass
    
    pdf.set_font("Arial", 'B', 16)
    # تنظيف البيانات لتجنب أخطاء الترميز
    name_str = str(cust_row['name']).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"Customer Report: {name_str}", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    install_date = str(cust_row.get('install_date', ''))
    pdf.cell(0, 10, f"Installation Date: {install_date}", ln=True, align='L')
    pdf.ln(5)
    
    # جدول الصيانات
    cols = ['Date', 'P1', 'P2', 'P3', 'Mem', 'Post', 'Calc', 'Infra', 'Amt', 'Notes']
    widths = [25, 12, 12, 12, 12, 12, 12, 12, 20, 140]
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", 'B', 10)
    for i, c in enumerate(cols):
        pdf.cell(widths[i], 10, c, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", '', 9)
    fill = False
    for _, r in history_df.iterrows():
        if fill: pdf.set_fill_color(240, 240, 240)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(widths[0], 10, str(r['visit_date']), 1, 0, 'C', True)
        for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            val = "V" if str(r.get(part, '')).lower() in ['true', '1', '✅'] else ""
            pdf.cell(12, 10, val, 1, 0, 'C', True)
        
        pdf.cell(widths[8], 10, str(r['amount']), 1, 0, 'C', True)
        notes_str = str(r['notes'])[:80].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(widths[9], 10, notes_str, 1, 1, 'L', True)
        fill = not fill
    
    # الفوتر
    pdf.set_y(-20)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Healthy Water: {COMPANY_PHONE}", align='C')
    
    # حل مشكلة AttributeError وتوافق الترميز
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        return pdf_bytes.encode('latin-1', errors='ignore')
    return pdf_bytes

# --- 5. نظام الدخول ---
if 'user_type' not in st.session_state: st.session_state.user_type = None

if st.session_state.user_type is None:
    st.title("🚰 Healthy Water System")
    t1, t2 = st.tabs(["🔒 الأدمن", "👤 العميل"])
    with t1:
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول الأدمن"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.user_type = "admin"; st.rerun()
    with t2:
        phone = st.text_input("رقم الهاتف المسجل")
        if st.button("دخول العميل"):
            match = df_c[df_c[['phone','phone_1','phone_2','phone_3','phone_4']].astype(str).apply(lambda x: x.str.contains(phone)).any(axis=1)]
            if not match.empty:
                st.session_state.user_type = "customer"; st.session_state.customer_data = match; st.rerun()

# --- 6. واجهة الأدمن ---
elif st.session_state.user_type == "admin":
    st.sidebar.image(LOGO_PATH, use_column_width=True)
    if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "بيانات العملاء"
    
    # تحديث المنيو بناءً على الاختيار من داخل الصفحات
    menu = st.sidebar.radio("القائمة", 
        ["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈"],
        index=["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈"].index(st.session_state.menu_choice)
    )
    st.session_state.menu_choice = menu # تحديث الحالة عند الضغط اليدوي)
    # --- صفحة إضافة عميل جديد (طلب رقم 2) ---
    if menu == "إضافة عميل جديد":
        st.header("➕ إضافة عميل جديد")
        with st.form("add_customer_form"):
            # جلب المناطق المسجلة فعلياً في الشيت لضمان ظهور أي منطقة جديدة تضاف
            existing_areas = sorted(df_c['area'].unique().tolist()) if not df_c.empty else []
            default_areas = ["مدينتي", "بدر", "الشروق", "المستقبل", "الرحاب", "مدينة نصر"]
            areas_list = list(set(existing_areas + default_areas))"]
            c1, c2 = st.columns(2)
            name = c1.text_input("الاسم (name)")
            phone = c2.text_input("الهاتف الأساسي (phone)")
            p1 = c1.text_input("هاتف 1")
            p2 = c2.text_input("هاتف 2")
            p3 = c1.text_input("هاتف 3")
            p4 = c2.text_input("هاتف 4")
            address = st.text_area("العنوان بالتفصيل (adress)")
            area = st.selectbox("المنطقة (area)", areas_list)
            new_area = st.text_input("أو أضف منطقة جديدة")
            final_area = new_area if new_area else area
            loc = st.text_input("رابط اللوكيشن (location_url)")
            inst_date = st.date_input("تاريخ التركيب (install_date)")
            cycle = st.number_input("دورة الصيانة بالشهر (cycle)", value=3)
            status = st.selectbox("الحالة (status)", ["نشط", "راكد"])
            
            if st.form_submit_button("حفظ العميل الجديد"):
                data = [name, phone, p1, p2, p3, p4, address, final_area, loc, str(inst_date), cycle, status]
                if execute_gsheet_action("append", "Customers", data):
                    st.success("تم الحفظ بنجاح!"); st.rerun()

    elif menu == "بيانات العملاء":
        st.header("👥 إدارة العملاء")
        search = st.text_input("🔍 بحث (اسم، هاتف، منطقة، ID)")
        
        # تصفية البحث
        if search:
            mask = df_c.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered = df_c[mask]
        else:
            filtered = df_c

        # الترتيب حسب المنطقة
        for area, group in filtered.groupby('area'):
            st.markdown(f"### 📍 {area}")
            for _, r in group.iterrows():
                with st.expander(f"👤 {r['name']} | 📞 {r['phone']}"):
                    c1, c2 = st.columns(2)
                    # عرض البيانات مع معالجة "غير مسجل" (تصحيح طلب رقم 1)
                    addr = r.get('adress', '')
                    c1.write(f"🏠 **العنوان:** {addr if addr else 'غير مسجل'}")
                    c1.write(f"📍 **المنطقة:** {r.get('area', 'غير مسجل')}")
                    c1.write(f"🗺️ **اللوكيشن:** {r.get('location_url', 'غير مسجل')}")
                    c1.write(f"📅 **تاريخ التركيب:** {r.get('install_date', 'غير مسجل')}")
                    c1.write(f"🔄 **دورة الصيانة:** {r.get('cycle', '0')} شهر")
                    
                    # حساب الموعد القادم (طلب رقم 1)
                    cust_hist = df_m[df_m['name'] == r['name']].sort_values('v_date_dt', ascending=False)
                    if not cust_hist.empty:
                        last_v = cust_hist.iloc[0]['v_date_dt']
                        next_v = last_v + timedelta(days=to_num(r['cycle'])*30)
                        st.warning(f"🕒 **تاريخ الزيارة القادمة المتوقع:** {next_v.date()}")
                    
                   # أزرار الاتصال الملونة
                    phones = [r.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(r.get(p, '')).strip() != ""]
                    for ph in phones:
                        st.markdown(f"""
                        <div style='display: flex; gap: 10px; align-items: center; margin-bottom: 10px;'>
                            <b style='min-width: 100px;'>📞 {ph}</b>
                            <a href='tel:{ph}' style='background-color: #007bff; color: white; padding: 5px 15px; text-decoration: none; border-radius: 5px; font-size: 14px;'>اتصال 📞</a>
                            <a href='https://wa.me/2{ph}' target='_blank' style='background-color: #25D366; color: white; padding: 5px 15px; text-decoration: none; border-radius: 5px; font-size: 14px;'>واتساب 💬</a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # جدول الصيانات (تصحيح الـ X والـ Check)
                    st.write("🛠️ **سجل الصيانات:**")
                    if not cust_hist.empty:
                        # تحويل True/False إلى رموز
                        display_hist = cust_hist.copy()
                        for col in ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']:
                            display_hist[col] = display_hist[col].apply(lambda x: "✅" if str(x).lower() in ['true', '1'] else "❌")
                        
                        # الأعمدة المطلوبة بالترتيب
                        show_cols = ['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared', 'other', 'amount', 'notes']
                        st.dataframe(display_hist[show_cols], use_container_width=True)
                        
                        # أزرار الـ PDF والحذف
                        if st.button("📄 تحميل تقرير PDF", key=f"pdf_{r['row_index_internal']}"):
                            pdf_data = generate_customer_pdf(r, cust_hist)
                            st.download_button("اضغط لبدء التحميل", pdf_data, f"{r['name']}.pdf", "application/pdf")
                    else:
                        st.info("لا يوجد سجل صيانات لهذا العميل.")

                    # زر إضافة صيانة مع انتقال فوري
                    if st.button("➕ تسجيل صيانة لهذا العميل", key=f"add_m_{r['row_index_internal']}"):
                        st.session_state.target_customer = r['name']
                        st.session_state.menu_choice = "تسجيل صيانة" # سنعدل الراديو ليقرأ هذه القيمة
                        st.rerun()

    elif menu == "جدول المواعيد 📅":
        st.header("📅 جدول مواعيد الصيانة")
        today = datetime.now().date()
        # توليد 7 أيام متتالية مع استثناء الجمعة
        days_to_show = []
        curr = today
        while len(days_to_show) < 7:
            if curr.weekday() != 4: # 4 هو الجمعة
                days_to_show.append(curr)
            curr += timedelta(days=1)
        
        for d in days_to_show:
            st.subheader(f"📆 {d.strftime('%A, %Y-%m-%d')}")
            # منطق الفلترة المتقدم (طلب رقم 2)
            day_list = []
            for _, cust in df_c[df_c['status'] == "نشط"].iterrows():
                last_m_all = df_m[df_m['name'] == cust['name']].sort_values('v_date_dt')
                if not last_m_all.empty:
                    last_m = last_m_all.iloc[-1]
                    # حساب الموعد (عادي أو استثنائي)
                    spec_date = parse_dt(last_m.get('special_date', ""))
                    next_v = spec_date.date() if spec_date else (last_m['v_date_dt'] + timedelta(days=to_num(cust['cycle'])*30)).date()
                    
                    # تحديد الحالة واللون
                    color = ""
                    if next_v == d: color = "yellow"
                    elif next_v < today and d == days_to_show[0]: color = "red" # متأخر يظهر في أول يوم
                    
                    if next_v == d or (next_v < today and d == days_to_show[0]):
                        st.markdown(f"""
                        <div style="border-right: 10px solid {color}; padding:10px; background:#f0f2f6; margin-bottom:5px; border-radius:5px">
                            <b>{cust['name']}</b> | {cust['area']} | 📞 {cust['phone']}
                        </div>
                        """, unsafe_allow_html=True)

    elif menu == "تسجيل صيانة":
        st.header("🔧 تسجيل زيارة صيانة")
        # العميل المختار من صفحة العملاء
        default_idx = 0
        if 'target_customer' in st.session_state:
            try: default_idx = df_c['name'].tolist().index(st.session_state.target_customer)
            except: pass
        
        with st.form("main_m_form"):
            selected_name = st.selectbox("اختر العميل", df_c['name'].tolist(), index=default_idx)
            v_date = st.date_input("تاريخ الزيارة", datetime.now())
            
            st.write("--- الشمعات الأساسية ---")
            c1, c2, c3 = st.columns(3)
            p1 = c1.checkbox("P1"); p2 = c2.checkbox("P2"); p3 = c3.checkbox("P3")
            mem = c1.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
            calc = c3.checkbox("Calcite"); infra = c1.checkbox("Infrared")
            
            # قائمة منسدلة للأصناف الأخرى (طلب رقم 3)
            other_items = df_inv[~df_inv['item_name'].isin(['p1','p2','p3','membrane','post carbon','calcite','infrared'])]['item_name'].tolist()
            other_choice = st.selectbox("قطع غيار أخرى (Other)", [""] + other_items)
            
            amt = st.number_input("المبلغ المحصل (Amount)", step=1)
            nts = st.text_area("ملاحظات")
            spec_d = st.date_input("موعد زيارة استثنائي (اختياري)", value=None)
            
            if st.form_submit_button("حفظ الزيارة"):
                # استخراج ID العميل تلقائياً
                cid = df_c[df_c['name'] == selected_name]['phone'].values[0] # نستخدم الفون كمعرف
                data = [selected_name, str(v_date), p1, p2, p3, mem, post, calc, infra, other_choice, amt, nts, str(spec_d) if spec_d else "", cid]
                if execute_gsheet_action("append", "Maintenance", data):
                    st.success("تم التسجيل بنجاح!"); st.rerun()

   elif menu == "المخزن 📦":
        st.header("📦 إدارة المخزن")
        total_cap = 0
        for i, r in df_inv.iterrows():
            with st.expander(f"⚙️ {r['item_name']} - الرصيد: {r['quantity']}"):
                with st.form(f"inv_edit_{i}"):
                    c1, c2, c3 = st.columns(3)
                    u_qty = c1.number_input("الكمية", value=to_num(r['quantity']))
                    u_cost = c2.number_input("التكلفة", value=to_num(r['cost_price']))
                    u_min = c3.number_input("حد الأمان", value=to_num(r['min_limit']))
                    total_cap += (u_qty * u_cost)
                    if st.form_submit_button("تحديث البيانات"):
                        execute_gsheet_action("update", "Inventory", [r['item_name'], u_qty, u_cost, u_min], row_index=r['row_index_internal'])
                        st.success("تم التحديث"); st.rerun()
        st.sidebar.metric("إجمالي رأس المال", f"{total_cap} ج.م")

    elif menu == "الاحتياجات 🚨": # طلب رقم 4
        st.header("🚨 أصناف تحت حد الأمان")
        needs = df_inv[df_inv['quantity'].apply(to_num) <= df_inv['min_limit'].apply(to_num)]
        if not needs.empty:
            st.table(needs[['item_name', 'quantity', 'min_limit']])
        else:
            st.success("كل الأصناف متوفرة فوق حد الأمان.")

    elif menu == "المصروفات":
        st.header("💵 المصروفات")
        # حساب أوتوماتيكي لتكلفة قطع الغيار (طلب رقم 5)
        selected_date = st.date_input("التاريخ", datetime.now())
        
        # البحث عن صيانات اليوم وحساب تكلفتها
        todays_m = df_m[df_m['v_date_dt'].dt.date == selected_date]
        auto_parts_cost = 0
        for _, m_row in todays_m.iterrows():
            for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                if str(m_row.get(part, '')).lower() in ['true', '1']:
                    # جلب السعر من المخزن
                    price = to_num(df_inv[df_inv['item_name'].str.lower() == part.lower()]['cost_price'].values[0]) if not df_inv[df_inv['item_name'].str.lower() == part.lower()].empty else 0
                    auto_parts_cost += price
        
        st.info(f"تكلفة قطع الغيار التلقائية لهذا اليوم: {auto_parts_cost} ج.م")
        
        with st.form("exp_form"):
            c1, c2 = st.columns(2)
            trans = c1.number_input("انتقالات", 0)
            neth = c2.number_input("نثريات", 0)
            month_exp = c1.number_input("مصروفات شهرية", 0)
            salaries = c2.number_input("رواتب", 0)
            other_exp = st.number_input("أخرى", 0)
            total_today = auto_parts_cost + trans + neth + month_exp + salaries + other_exp
            st.write(f"**إجمالي المصروفات:** {total_today}")
            
            if st.form_submit_button("حفظ المصروفات"):
                # يتم الحفظ في شيت Expenses
                # الأعمدة: date, transportation, sundries, monthly_expensess, salaries, notes (سجلنا فيها التوتال مؤقتاً)
                execute_gsheet_action("append", "Expenses", [str(selected_date), trans, neth, month_exp, salaries, f"Total: {total_today}"])
                st.success("تم الحفظ")

    elif menu == "الأرباح 📈":
        st.header("📈 تقارير الأرباح والتحليل المالي")
        # فلتر الشهر
        df_m['month'] = df_m['v_date_dt'].dt.strftime('%Y-%m')
        m_list = sorted(df_m['month'].unique().tolist(), reverse=True)
        sel_m = st.selectbox("اختر الشهر", m_list)
        
        m_data = df_m[df_m['month'] == sel_m]
        rev = m_data['amount_num'].sum()
        
        # حساب التكاليف (الشمعات)
        cost_parts = 0
        for _, r in m_data.iterrows():
            for p in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                if str(r.get(p)).lower() in ['true','1']:
                    p_price = to_num(df_inv[df_inv['item_name'].str.lower()==p.lower()]['cost_price'].values[0]) if p.lower() in df_inv['item_name'].str.lower().values else 0
                    cost_parts += p_price
        
        st.columns(3)[0].metric("إجمالي الإيرادات", f"{rev} ج.م")
        st.columns(3)[1].metric("تكلفة قطع الغيار", f"{cost_parts} ج.م")
        st.columns(3)[2].metric("صافي الربح التقديري", f"{rev - cost_parts} ج.م")
        
        fig = px.bar(m_data, x='visit_date', y='amount_num', title="الإيرادات اليومية للشهر")
        st.plotly_chart(fig)

# --- 7. واجهة العميل ---
elif st.session_state.user_type == "customer":
    st.title("👋 أهلاً بك في Healthy Water")
    for _, row in st.session_state.customer_data.iterrows():
        st.subheader(f"العميل: {row['name']}")
        st.write(f"العنوان: {row['adress']}")
        
        # عرض الصيانات الخاصة به فقط
        my_m = df_m[df_m['name'] == row['name']].sort_values('v_date_dt', ascending=False)
        st.write("**🔧 سجل الصيانات الخاص بك:**")
        if not my_m.empty:
            st.table(my_m[['visit_date', 'notes']])
        
        st.divider()
        st.write("للتواصل معنا:")
        c1, c2 = st.columns(2)
        c1.link_button("📞 اتصال هاتفي", f"tel:{COMPANY_PHONE}")
        c2.link_button("💬 واتساب", f"https://wa.me/{COMPANY_PHONE}")
        
    if st.button("خروج"): st.session_state.user_type = None; st.rerun()
