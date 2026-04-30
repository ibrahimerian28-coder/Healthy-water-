import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import io
import os
from arabic_reshaper import reshape
from bidi.algorithm import get_display

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

if 'user_type' not in st.session_state: st.session_state.user_type = None

if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)
if not df_exp.empty:
    df_exp['exp_date_dt'] = df_exp['date'].apply(parse_dt)

# --- 4. وظيفة توليد الـ PDF ---
# --- كلاس مخصص لضمان ظهور الفوتر في كل صفحة تلقائياً ---
class PDF_Report(FPDF):
    def footer(self):
        self.set_y(-15)
        try:
            self.add_font('ArabicFont', '', "Arial.ttf")
            self.set_font('ArabicFont', '', 11)
            footer_text = get_display(reshape(f"Healthy Water | للتواصل معنا: {COMPANY_PHONE} 📞 💬"))
        except:
            self.set_font('Arial', 'I', 10)
            footer_text = f"Healthy Water | Contact: {COMPANY_PHONE}"
        
        self.set_text_color(128, 128, 128)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 287, self.get_y())
        self.cell(0, 10, footer_text, 0, 0, 'C', False, f"tel:{COMPANY_PHONE}")

def generate_customer_pdf(cust_row, history_df):
    pdf = PDF_Report(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    font_path = os.path.join(os.getcwd(), "Arial.ttf")
    has_arabic = False
    if os.path.exists(font_path):
        try:
            pdf.add_font('ArabicFont', '', font_path)
            has_arabic = True
        except: pass

    def format_ar(text):
        if not text or str(text).strip() == "": return ""
        if not has_arabic: return "".join([c for c in str(text) if ord(c) < 128])
        return get_display(reshape(str(text)))

    # --- 1. الهيدر: وضع اللوجو في اليسار كمنطقة محجوزة ---
    try:
        # اللوجو في أقصى اليسار العلوي (حجم كبير جداً 90mm)
        pdf.image(LOGO_PATH, x=197, y=10, w=90) 
    except: pass

    # --- 2. العناوين: في أقصى اليمين (بعيداً تماماً عن منطقة اللوجو) ---
    # نحدد منطقة الكتابة في اليمين فقط (عرض 150mm من أصل 297mm)
    pdf.set_xy(10, 15) 
    
    if has_arabic: pdf.set_font('ArabicFont', '', 24)
    else: pdf.set_font('Arial', 'B', 22)
    
    # حجز خلية بعرض 150 ملم فقط في جهة اليمين لضمان عدم وصول النص لليسار
    pdf.cell(150, 15, format_ar(f"تقرير صيانة: {cust_row['name']}"), ln=True, align='R')
    
    if has_arabic: pdf.set_font('ArabicFont', '', 14)
    else: pdf.set_font('Arial', '', 12)
    
    pdf.set_x(10)
    pdf.cell(150, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    
    # مسافة أمان رأسية قبل بدء الجدول لضمان عدم التداخل مع اللوجو
    pdf.set_y(60) 

    # --- 3. إعداد الجدول ---
    # تغيير اسم "القطع" إلى "أخرى"
    cols = ['ملاحظات', 'المبلغ', 'أخرى', 'Infra', 'Calc', 'Post', 'Mem', 'P3', 'P2', 'P1', 'التاريخ']
    widths = [75, 17, 30, 15, 15, 15, 15, 15, 15, 15, 30]
    
    # رأس الجدول (أزرق فاتح)
    pdf.set_fill_color(173, 216, 230) 
    if has_arabic: pdf.set_font('ArabicFont', '', 11)
    
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 10, format_ar(col), 1, 0, 'C', True)
    pdf.ln()

    # --- 4. محتوى الجدول ---
    if has_arabic: pdf.set_font('ArabicFont', '', 10)
    fill = False
    for _, r in history_df.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(widths[0], 8, format_ar(r['notes']), 1, 0, 'R', fill)
        pdf.cell(widths[1], 8, str(r['amount']), 1, 0, 'C', fill)
        
        # خانة "أخرى" (التي تسحب من عمود other)
        other_val = str(r.get('other', ''))
        pdf.cell(widths[2], 8, format_ar(other_val), 1, 0, 'C', fill)
        
        # الشمعات
        for part in ['infrared', 'Calcite', 'post_carbon', 'membrane', 'P3', 'P2', 'P1']:
            val = format_ar("تم") if str(r.get(part, '')).lower() in ['true', '1', '✅'] else ""
            pdf.cell(15, 8, val, 1, 0, 'C', fill)
            
        pdf.cell(widths[10], 8, str(r['visit_date']), 1, 1, 'C', fill)
        fill = not fill 

    return bytes(pdf.output())

# --- 5. تسجيل الدخول ---
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
    
    menu = st.sidebar.radio("القائمة", 
        ["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈"],
        index=["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈"].index(st.session_state.menu_choice)
    )
    st.session_state.menu_choice = menu 
    
    if menu == "إضافة عميل جديد":
        st.header("➕ إضافة عميل جديد")
        with st.form("add_customer_form"):
            existing_areas = sorted(df_c['area'].unique().tolist()) if not df_c.empty else []
            default_areas = ["مدينتي", "بدر", "الشروق", "المستقبل", "الرحاب", "مدينة نصر"]
            areas_list = list(set(existing_areas + default_areas))
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
        filtered = df_c[df_c.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)] if search else df_c
        for area, group in filtered.groupby('area'):
            st.markdown(f"### 📍 {area}")
            for _, r in group.iterrows():
                with st.expander(f"👤 {r['name']} | 📞 {r['phone']}"):
                    c1, c2 = st.columns(2)
                    c1.write(f"🏠 **العنوان:** {r.get('adress', 'غير مسجل')}")
                    c1.write(f"📍 **المنطقة:** {r.get('area', 'غير مسجل')}")
                    c1.write(f"📅 **تاريخ التركيب:** {r.get('install_date', 'غير مسجل')}")
                    cust_hist = df_m[df_m['name'] == r['name']].sort_values('v_date_dt', ascending=False)
                    if not cust_hist.empty:
                        last_v = cust_hist.iloc[0]['v_date_dt']
                        next_v = last_v + timedelta(days=to_num(r['cycle'])*30)
                        st.warning(f"🕒 **تاريخ الزيارة القادمة المتوقع:** {next_v.date()}")
                    phones = [r.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(r.get(p, '')).strip() != ""]
                    for ph in phones:
                        st.markdown(f"<b>📞 {ph}</b> <a href='tel:{ph}'>اتصال</a> | <a href='https://wa.me/2{ph}'>واتساب</a>", unsafe_allow_html=True)
                    st.write("🛠️ **سجل الصيانات:**")
                    if not cust_hist.empty:
                        display_hist = cust_hist.copy()
                        show_cols = ['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared', 'amount', 'notes']
                        st.dataframe(display_hist[show_cols], use_container_width=True)
                        if st.button("📄 تحميل تقرير PDF", key=f"pdf_{r['row_index_internal']}"):
                            pdf_data = generate_customer_pdf(r, cust_hist)
                            st.download_button(label="اضغط لبدء التحميل", data=pdf_data, file_name=f"{r['name']}.pdf", mime="application/pdf")
                    else: st.info("لا يوجد سجل صيانات.")
                    if st.button("➕ تسجيل صيانة لهذا العميل", key=f"add_m_{r['row_index_internal']}"):
                        st.session_state.target_customer = r['name']; st.session_state.menu_choice = "تسجيل صيانة"; st.rerun()

    elif menu == "جدول المواعيد 📅":
        st.header("📅 جدول مواعيد الصيانة")
        today = datetime.now().date()
        days_to_show = []
        curr = today
        while len(days_to_show) < 7:
            if curr.weekday() != 4: days_to_show.append(curr)
            curr += timedelta(days=1)
        for d in days_to_show:
            st.subheader(f"📆 {d.strftime('%A, %Y-%m-%d')}")
            for _, cust in df_c[df_c['status'] == "نشط"].iterrows():
                last_m_all = df_m[df_m['name'] == cust['name']].sort_values('v_date_dt')
                if not last_m_all.empty:
                    last_m = last_m_all.iloc[-1]
                    spec_date = parse_dt(last_m.get('special_date', ""))
                    next_v = spec_date.date() if spec_date else (last_m['v_date_dt'] + timedelta(days=to_num(cust['cycle'])*30)).date()
                    if next_v == d or (next_v < today and d == days_to_show[0]):
                        if st.button(f"👤 {cust['name']} | {cust['area']} | 📞 {cust['phone']}", key=f"sch_{cust['row_index_internal']}_{d}"):
                            st.session_state.search_query = cust['name']; st.session_state.menu_choice = "بيانات العملاء"; st.rerun()

    elif menu == "تسجيل صيانة":
        st.header("🔧 تسجيل زيارة صيانة")
        default_idx = 0
        if 'target_customer' in st.session_state:
            try: default_idx = df_c['name'].tolist().index(st.session_state.target_customer)
            except: pass
        with st.form("main_m_form"):
            selected_name = st.selectbox("اختر العميل", df_c['name'].tolist(), index=default_idx)
            v_date = st.date_input("تاريخ الزيارة", datetime.now())
            c1, c2, c3 = st.columns(3)
            p1 = c1.checkbox("P1"); p2 = c2.checkbox("P2"); p3 = c3.checkbox("P3")
            mem = c1.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
            calc = c3.checkbox("Calcite"); infra = c1.checkbox("Infrared")
            other_choice = st.selectbox("قطع غيار أخرى (Other)", [""] + df_inv['item_name'].tolist())
            amt = st.number_input("المبلغ المحصل (Amount)", step=1)
            nts = st.text_area("ملاحظات")
            spec_d = st.date_input("موعد زيارة استثنائي (اختياري)", value=None)
            if st.form_submit_button("حفظ الزيارة"):
                cid = df_c[df_c['name'] == selected_name]['phone'].values[0]
                data = [selected_name, str(v_date), p1, p2, p3, mem, post, calc, infra, other_choice, amt, nts, str(spec_d) if spec_d else "", cid]
                if execute_gsheet_action("append", "Maintenance", data):
                    st.success("تم التسجيل بنجاح!"); st.rerun()

    elif menu == "المخزن 📦":
        st.header("📦 إدارة المخزن")
        total_cap = 0
        for i, r in df_inv.iterrows():
            with st.expander(f"⚙️ {r['item_name']} - الرصيد: {r['quantity']}"):
                with st.form(f"inv_edit_{i}"):
                    u_qty = st.number_input("الكمية", value=to_num(r['quantity']))
                    u_cost = st.number_input("التكلفة", value=to_num(r['cost_price']))
                    u_min = st.number_input("حد الأمان", value=to_num(r['min_limit']))
                    total_cap += (u_qty * u_cost)
                    if st.form_submit_button("تحديث البيانات"):
                        execute_gsheet_action("update", "Inventory", [r['item_name'], u_qty, u_cost, u_min], row_index=r['row_index_internal'])
                        st.success("تم التحديث"); st.rerun()
        st.sidebar.metric("إجمالي رأس المال", f"{total_cap} ج.م")

    elif menu == "الاحتياجات 🚨":
        st.header("🚨 أصناف تحت حد الأمان")
        needs = df_inv[df_inv['quantity'].apply(to_num) <= df_inv['min_limit'].apply(to_num)]
        if not needs.empty: st.table(needs[['item_name', 'quantity', 'min_limit']])
        else: st.success("كل الأصناف متوفرة فوق حد الأمان.")

    elif menu == "المصروفات":
        st.header("💵 المصروفات")
        selected_date = st.date_input("التاريخ", datetime.now())
        todays_m = df_m[df_m['v_date_dt'].dt.date == selected_date]
        auto_parts_cost = 0
        for _, m_row in todays_m.iterrows():
            for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                if str(m_row.get(part, '')).lower() in ['true', '1']:
                    price = to_num(df_inv[df_inv['item_name'].str.lower() == part.lower()]['cost_price'].values[0]) if not df_inv[df_inv['item_name'].str.lower() == part.lower()].empty else 0
                    auto_parts_cost += price
        st.info(f"تكلفة قطع الغيار التلقائية لهذا اليوم: {auto_parts_cost} ج.م")
        with st.form("exp_form"):
            trans = st.number_input("انتقالات", 0); neth = st.number_input("نثريات", 0)
            total_today = auto_parts_cost + trans + neth
            if st.form_submit_button("حفظ المصروفات"):
                execute_gsheet_action("append", "Expenses", [str(selected_date), trans, neth, 0, 0, f"Total: {total_today}"])
                st.success("تم الحفظ")

    elif menu == "الأرباح 📈":
        st.header("📈 تقارير الأرباح")
        df_m['month'] = df_m['v_date_dt'].dt.strftime('%Y-%m')
        m_list = sorted(df_m['month'].unique().tolist(), reverse=True)
        if m_list:
            sel_m = st.selectbox("اختر الشهر", m_list)
            m_data = df_m[df_m['month'] == sel_m]
            rev = m_data['amount_num'].sum()
            cost_parts = 0
            for _, r in m_data.iterrows():
                for p in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                    if str(r.get(p)).lower() in ['true','1']:
                        p_price = to_num(df_inv[df_inv['item_name'].str.lower()==p.lower()]['cost_price'].values[0]) if p.lower() in df_inv['item_name'].str.lower().values else 0
                        cost_parts += p_price
            st.metric("إجمالي الإيرادات", f"{rev} ج.م")
            st.metric("صافي الربح التقديري", f"{rev - cost_parts} ج.م")
            st.plotly_chart(px.bar(m_data, x='visit_date', y='amount_num'))

elif st.session_state.user_type == "customer":
    st.title("👋 أهلاً بك")
    for _, row in st.session_state.customer_data.iterrows():
        st.subheader(f"العميل: {row['name']}")
        my_m = df_m[df_m['name'] == row['name']].sort_values('v_date_dt', ascending=False)
        if not my_m.empty: st.table(my_m[['visit_date', 'notes']])
        st.link_button("📞 اتصال هاتفي", f"tel:{COMPANY_PHONE}")
    if st.button("خروج"): st.session_state.user_type = None; st.rerun()
