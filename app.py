import base64
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

def read_gsheet(sheet_name):
    # دالة افتراضية لتحميل بيانات المتجر بناءً على الاسم
    gids = {"Store_Products": "123456789"} # يجب التأكد من الـ GID الصحيح لهذا الشيت
    return load_data(gids.get(sheet_name, "0"))

# --- 3. تحميل البيانات ---
df_c = load_data("0")          # Customers
df_m = load_data("2120582392") # Maintenance
df_inv = load_data("1767710106") # Inventory
df_exp = load_data("288947510")  # Expenses
df_store = load_data("1168172935") # Store_Products (مثال للـ GID)

# التأكد من تحويل الأعمدة الرقمية لضمان عدم حدوث أخطاء في الحسابات
if not df_store.empty:
    df_store['Price'] = df_store['Price'].apply(to_num)
    df_store['Old_Price'] = df_store['Old_Price'].apply(to_num)

st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="🚰")

if 'user_type' not in st.session_state: st.session_state.user_type = None

if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)
if not df_exp.empty:
    df_exp['exp_date_dt'] = df_exp['date'].apply(parse_dt)

# --- 4. وظيفة توليد الـ PDF ---
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

    try:
        pdf.image(LOGO_PATH, x=197, y=10, w=90) 
    except: pass

    pdf.set_xy(10, 15) 
    if has_arabic: pdf.set_font('ArabicFont', '', 24)
    else: pdf.set_font('Arial', 'B', 22)
    pdf.cell(150, 15, format_ar(f"تقرير صيانة: {cust_row['name']}"), ln=True, align='R')
    
    if has_arabic: pdf.set_font('ArabicFont', '', 14)
    else: pdf.set_font('Arial', '', 12)
    pdf.set_x(10)
    pdf.cell(150, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    
    pdf.set_y(60) 

    cols = ['ملاحظات', 'المبلغ', 'أخرى', 'Infra', 'Calc', 'Post', 'Mem', 'P3', 'P2', 'P1', 'التاريخ']
    widths = [75, 17, 30, 15, 15, 15, 15, 15, 15, 15, 30]
    
    pdf.set_fill_color(173, 216, 230) 
    if has_arabic: pdf.set_font('ArabicFont', '', 11)
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 10, format_ar(col), 1, 0, 'C', True)
    pdf.ln()

    if has_arabic: pdf.set_font('ArabicFont', '', 10)
    fill = False
    for _, r in history_df.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(widths[0], 8, format_ar(r['notes']), 1, 0, 'R', fill)
        pdf.cell(widths[1], 8, str(r['amount']), 1, 0, 'C', fill)
        other_val = str(r.get('other', ''))
        pdf.cell(widths[2], 8, format_ar(other_val), 1, 0, 'C', fill)
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
        phone_input = st.text_input("رقم الهاتف المسجل")
        if st.button("دخول العميل"):
            if phone_input.strip() == "":
                st.warning("يرجى إدخال رقم الهاتف")
            else:
                clean_phone = str(phone_input).strip()
                available_phone_cols = [col for col in df_c.columns if 'phone' in col.lower()]
                
                if not available_phone_cols:
                    st.error("خطأ: لم يتم العثور على أعمدة الهاتف في قاعدة البيانات.")
                else:
                    mask = df_c[available_phone_cols].astype(str).apply(
                        lambda x: x.str.contains(clean_phone, na=False)
                    ).any(axis=1)
                    
                    match = df_c[mask]
                    
                    if not match.empty:
                        st.session_state.user_type = "customer"
                        st.session_state.customer_data = match
                        st.success("تم تسجيل الدخول بنجاح")
                        st.rerun()
                    else:
                        st.error("عذراً، هذا الرقم غير مسجل لدينا.")

# --- 6. واجهة الأدمن ---
elif st.session_state.user_type == "admin":
    st.sidebar.image(LOGO_PATH, use_column_width=True)
    if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "بيانات العملاء"
    
    admin_options = ["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈", "المتجر 🛒", "إدارة المنتجات ⚙️", "اطلب صيانة فوراً ⚙️"]
    if st.session_state.menu_choice not in admin_options:
        st.session_state.menu_choice = "بيانات العملاء"

    menu = st.sidebar.radio(
        "القائمة", 
        admin_options,
        index=admin_options.index(st.session_state.menu_choice)
    ) 
    
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
                        
                        st.write("🛠️ **سجل الصيانات:**")
                        display_hist = cust_hist.copy()
                        check_cols = ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']
                        for col in check_cols:
                            if col in display_hist.columns:
                                display_hist[col] = display_hist[col].apply(lambda x: "✅" if str(x).lower() in ['true', '1', '✅'] else "❌")
                        
                        show_cols = ['visit_date'] + check_cols + ['amount', 'notes']
                        st.dataframe(display_hist[show_cols], use_container_width=True, hide_index=True)
                        
                        if st.button("📄 تحميل تقرير PDF", key=f"pdf_{r['row_index_internal']}"):
                            pdf_data = generate_customer_pdf(r, cust_hist)
                            st.download_button(label="اضغط لبدء التحميل", data=pdf_data, file_name=f"{r['name']}.pdf", mime="application/pdf")
                    
                    phones = [r.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(r.get(p, '')).strip() != ""]
                    for ph in phones:
                        st.markdown(f"<b>📞 {ph}</b> <a href='tel:{ph}'>اتصال</a> | <a href='https://wa.me/2{ph}'>واتساب</a>", unsafe_allow_html=True)

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
                        with st.expander(f"👤 {cust['name']} | 📍 {cust['area']} | 📞 {cust['phone']}"):
                            c1, c2 = st.columns(2)
                            c1.write(f"🏠 **العنوان:** {cust.get('adress', 'غير مسجل')}")
                            c1.write(f"📅 **تاريخ التركيب:** {cust.get('install_date', 'غير مسجل')}")
                            
                            cust_hist = df_m[df_m['name'] == cust['name']].sort_values('v_date_dt', ascending=False)
                            if not cust_hist.empty:
                                st.write("🛠️ **سجل الصيانات:**")
                                display_hist = cust_hist.copy()
                                check_cols = ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']
                                
                                for col in check_cols:
                                    if col in display_hist.columns:
                                        display_hist[col] = display_hist[col].apply(lambda x: "✅" if str(x).lower() in ['true', '1', '✅'] else "❌")
                                
                                show_cols = ['visit_date'] + check_cols + ['amount', 'notes']
                                st.dataframe(display_hist[show_cols], use_container_width=True, hide_index=True)
                                
                                if st.button("📄 تحميل PDF", key=f"pdf_sch_{cust['row_index_internal']}_{d}"):
                                    pdf_data = generate_customer_pdf(cust, cust_hist)
                                    st.download_button(label="بدء التحميل", data=pdf_data, file_name=f"{cust['name']}.pdf", mime="application/pdf")
                            
                            phones = [cust.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(cust.get(p, '')).strip() != ""]
                            for ph in phones:
                                st.markdown(f"<b>📞 {ph}</b> <a href='tel:{ph}'>اتصال</a> | <a href='https://wa.me/2{ph}'>واتساب</a>", unsafe_allow_html=True)
                            
                            if st.button("🔧 تسجيل صيانة الآن", key=f"go_reg_{cust['row_index_internal']}_{d}"):
                                st.session_state.target_customer = cust['name']
                                st.session_state.menu_choice = "تسجيل صيانة"
                                st.rerun()

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
        total_inventory_value = 0 
        
        for i, r in df_inv.iterrows():
            current_qty = to_num(r.get('quantity', 0))
            current_min = to_num(r.get('min_limit', 0))
            current_cost = to_num(r.get('cost_price', 0))
            
            item_total_value = current_qty * current_cost
            total_inventory_value += item_total_value
            
            with st.expander(f"⚙️ {r['item_name']} - الرصيد الحالي: {current_qty}"):
                with st.form(f"inv_edit_{i}"):
                    c1, c2 = st.columns(2)
                    u_qty = c1.number_input("الكمية المتوفرة", value=current_qty, key=f"qty_{i}")
                    u_min = c2.number_input("حد الأمان (min_limit)", value=current_min, key=f"min_{i}")
                    u_cost = c1.number_input("سعر التكلفة (cost_price)", value=current_cost, key=f"cost_{i}")
                    
                    st.info(f"💰 إجمالي قيمة هذا الصنف في المخزن: {u_qty * u_cost} ج.م")
                    
                    if st.form_submit_button("تحديث بيانات الصنف"):
                        updated_data = [
                            r['item_name'], # العمود A
                            u_qty,          # العمود B
                            u_min,          # العمود C
                            u_cost          # العمود D
                        ]
                        
                        if execute_gsheet_action("update", "Inventory", updated_data, row_index=r['row_index_internal']):
                            st.success(f"تم تحديث {r['item_name']} بنجاح!")
                            st.rerun()
                        else:
                            st.error("خطأ: تعذر الوصول للسيرفر لتحديث البيانات.")

        st.divider()
        st.metric(label="إجمالي رأس المال (قيمة المخزون الكلية)", value=f"{total_inventory_value} ج.م")
        st.sidebar.metric("إجمالي رأس المال", f"{total_inventory_value} ج.م")

    elif menu == "الاحتياجات 🚨":
        st.header("🚨 أصناف تحت حد الأمان")
        needs = df_inv[df_inv['quantity'].apply(to_num) <= df_inv['min_limit'].apply(to_num)]
        if not needs.empty: st.table(needs[['item_name', 'quantity', 'min_limit']])
        else: st.success("كل الأصناف متوفرة فوق حد الأمان.")

    elif menu == "المصروفات":
        st.header("💵 إدارة المصروفات")
        selected_date = st.date_input("تاريخ المصروفات", datetime.now())
        
        todays_m = df_m[df_m['v_date_dt'].dt.date == selected_date]
        auto_parts_cost = 0
        for _, m_row in todays_m.iterrows():
            for part in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                if str(m_row.get(part, '')).lower() in ['true', '1', '✅']:
                    price = to_num(df_inv[df_inv['item_name'].str.lower() == part.lower()]['cost_price'].values[0]) if not df_inv[df_inv['item_name'].str.lower() == part.lower()].empty else 0
                    auto_parts_cost += price
        
        st.info(f"ℹ️ تكلفة قطع الغيار المستهلكة في صيانات اليوم: {auto_parts_cost} ج.م (تُحسب تلقائياً في الأرباح)")

        with st.form("exp_form_extended"):
            st.subheader("تسجيل مصروفات إضافية")
            c1, c2 = st.columns(2)
            trans = c1.number_input("انتقالات (transportation)", min_value=0, step=5)
            neth = c2.number_input("نثريات (sundries)", min_value=0, step=5)
            monthly = c1.number_input("مصروفات شهرية (monthly_expensess)", min_value=0, step=10)
            salary = c2.number_input("رواتب (salaries)", min_value=0, step=50)
            notes = st.text_area("ملاحظات (notes)")
            
            total_manual = trans + neth + monthly + salary
            st.markdown(f"**إجمالي المصروفات اليدوية: {total_manual} ج.م**")
            
            if st.form_submit_button("حفظ المصروفات في الشيت"):
                exp_data = [
                    str(selected_date), # date
                    trans,              # transportation
                    neth,               # sundries
                    monthly,            # monthly_expensess
                    salary,             # salaries
                    notes               # notes
                ]
                
                if execute_gsheet_action("append", "Expenses", exp_data):
                    st.success("✅ تم حفظ المصروفات بنجاح")
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بالسيرفر، حاول مرة أخرى")

        if not df_exp.empty:
            st.divider()
            st.subheader("📅 آخر المصروفات المسجلة")
            recent_exp = df_exp.tail(10).iloc[::-1]
            st.dataframe(recent_exp, use_container_width=True, hide_index=True)

    elif menu == "الأرباح 📈":
        st.header("📈 تقارير صافي الأرباح")

        def get_daily_net(target_date):
            if isinstance(target_date, str):
                target_date = pd.to_datetime(target_date).date()
            
            day_rev = 0
            if not df_m.empty and 'v_date_dt' in df_m.columns:
                day_m = df_m[df_m['v_date_dt'].dt.date == target_date]
                day_rev = day_m['amount_num'].sum()
            
            day_exp_total = 0
            if not df_exp.empty and 'exp_date_dt' in df_exp.columns:
                day_ex = df_exp[df_exp['exp_date_dt'].dt.date == target_date]
                for col in ['transportation', 'sundries', 'monthly_expensess', 'salaries']:
                    if col in day_ex.columns:
                        day_exp_total += day_ex[col].apply(to_num).sum()
            
            return day_rev - day_exp_total

        st.subheader("🗓️ صافي الربح اليومي")
        sel_day = st.date_input("اختر التاريخ", datetime.now())
        daily_net = get_daily_net(sel_day)
        st.metric(f"صافي ربح يوم {sel_day}", f"{daily_net} ج.م")

        st.divider()

        st.subheader("📅 صافي الربح الأسبوعي (آخر 7 أيام)")
        end_date = datetime.now().date()
        week_days = [end_date - timedelta(days=i) for i in range(7)]
        weekly_net = sum([get_daily_net(d) for d in week_days])
        st.metric("إجمالي ربح الـ 7 أيام الماضية", f"{weekly_net} ج.م")

        st.divider()

        st.subheader("📊 صافي الربح الشهري")
        c1, c2 = st.columns(2)
        sel_year_m = c1.selectbox("السنة", range(2024, 2030), index=2)
        sel_month = c2.selectbox("الشهر", range(1, 13), index=datetime.now().month - 1)
        
        import calendar
        num_days = calendar.monthrange(sel_year_m, sel_month)[1]
        month_days = [datetime(sel_year_m, sel_month, d).date() for d in range(1, num_days + 1)]
        monthly_net = sum([get_daily_net(d) for d in month_days])
        st.metric(f"إجمالي أرباح شهر {sel_month} - {sel_year_m}", f"{monthly_net} ج.م")

        st.divider()

        st.subheader("🏢 إجمالي صافي الربح السنوي")
        sel_year_y = st.selectbox("اختر السنة المرجعية", range(2024, 2030), index=2)
        
        yearly_net = 0
        for m in range(1, 13):
            m_days = calendar.monthrange(sel_year_y, m)[1]
            yearly_net += sum([get_daily_net(datetime(sel_year_y, m, d).date()) for d in range(1, m_days + 1)])
        
        st.metric(f"صافي أرباح سنة {sel_year_y} كاملة", f"{yearly_net} ج.م")

        st.divider()

        st.subheader("📈 قسم الرسوم البيانية")
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["مقارنة أيام الشهر", "مقارنة شهور السنة", "مقارنة السنوات"])

        with chart_tab1:
            m_data = []
            for d in month_days:
                m_data.append({"التاريخ": str(d), "الربح": get_daily_net(d)})
            df_m_chart = pd.DataFrame(m_data)
            st.plotly_chart(px.line(df_m_chart, x="التاريخ", y="الربح", title=f"تذبذب الأرباح خلال شهر {sel_month}"))

        with chart_tab2:
            y_data = []
            for m in range(1, 13):
                m_days = calendar.monthrange(sel_year_y, m)[1]
                m_sum = sum([get_daily_net(datetime(sel_year_y, m, d).date()) for d in range(1, m_days + 1)])
                y_data.append({"الشهر": calendar.month_name[m], "الربح": m_sum})
            df_y_chart = pd.DataFrame(y_data)
            st.plotly_chart(px.bar(df_y_chart, x="الشهر", y="الربح", title=f"أداء الشهور خلال سنة {sel_year_y}"))

        with chart_tab3:
            years_to_compare = [2024, 2025, 2026]
            all_years_data = []
            for y in years_to_compare:
                y_sum = 0
                for m in range(1, 13):
                    m_days = calendar.monthrange(y, m)[1]
                    y_sum += sum([get_daily_net(datetime(y, m, d).date()) for d in range(1, m_days + 1)])
                all_years_data.append({"السنة": str(y), "إجمالي الربح": y_sum})
            df_all_y = pd.DataFrame(all_years_data)
            st.plotly_chart(px.bar(df_all_y, x="السنة", y="إجمالي الربح", title="مقارنة الأرباح السنوية"))
            
    # --- 7. إدارة المنتجات ⚙️ ---
    elif menu == "إدارة المنتجات ⚙️":
        st.header("⚙️ إدارة منتجات المتجر")
        with st.form("add_product_form", clear_on_submit=True):
            st.subheader("إضافة منتج جديد")
            p_title = st.text_input("اسم المنتج")
            p_price = st.number_input("السعر الحالي", min_value=0)
            p_old_price = st.number_input("السعر القديم", min_value=0)
            p_cat = st.selectbox("التصنيف", ["أجهزة", "شمعات"])
            
            # رفع الصور من الجهاز (بحد أقصى 5 صور)
            uploaded_files = st.file_uploader("ارفع صور المنتج (1-5 صور)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            
            # وصف المنتج (بدون حد أقصى للحروف)
            p_desc = st.text_area("وصف المنتج التفصيلي", height=200)
            
            if st.form_submit_button("حفظ المنتج"):
                if not uploaded_files:
                    st.error("يرجى رفع صورة واحدة على الأقل")
                else:
                    # تحويل الصور لروابط نصية Base64 لتخزينها في الشيت
                    img_links = []
                    for file in uploaded_files[:5]: # التأكد من عدم تجاوز 5 صور
                        encoded = base64.b64encode(file.read()).decode()
                        img_links.append(f"data:image/png;base64,{encoded}")
                    
                    # دمج روابط الصور في نص واحد مفصول بفاصلة
                    all_imgs_str = "||".join(img_links)
                    
                    new_prod = [str(datetime.now().timestamp()), p_title, p_price, p_old_price, p_cat, all_imgs_str, p_desc]
                    if execute_gsheet_action("append", "Store_Products", new_prod):
                        st.success("تم إضافة المنتج بنجاح مع الصور!"); st.rerun()

    # --- 8. المتجر 🛒 (النظام المتكامل: سلة + دفع + إجمالي) ---
    elif menu == "المتجر 🛒":
        st.header("🛒 متجر Healthy Water")
        
        # 1. تهيئة سلة التسوق في الذاكرة (Session State)
        if 'cart' not in st.session_state:
            st.session_state.cart = []

        # 2. أيقونة السلة في الأعلى
        cart_count = sum(item['quantity'] for item in st.session_state.cart)
        col_header, col_cart = st.columns([0.8, 0.2])
        with col_cart:
            if st.button(f"🛒 السلة ({cart_count})"):
                st.session_state.view_cart = True
        
        # 3. تحميل البيانات
        STORE_GID = "1168172935" # تأكد من مطابقة هذا الرقم لصفحة Store_Products
        df_store = load_data(STORE_GID)
        
        if df_store is None or df_store.empty:
            st.error("لم يتم العثور على بيانات في المتجر.")
        else:
            df_store.columns = df_store.columns.str.strip()
            
            # عرض الأقسام (Tabs)
            t1, t2 = st.tabs(["💧 الأجهزة", "🛡️ الشمعات"])
            
            def show_products(filtered_df):
                cols = st.columns(2)
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    with cols[i % 2]:
                        imgs = str(row['Images']).split("||")
                        st.image(imgs[0], use_column_width=True)
                        st.subheader(row['Title'])
                        st.write(f"**السعر:** {row['Price']} ج.م")
                        
                        # أزرار الإضافة للسلة
                        if st.button("➕ أضف للسلة", key=f"add_{row['row_index_internal']}"):
                            # التحقق إذا كان المنتج موجود مسبقاً لزيادة الكمية
                            found = False
                            for item in st.session_state.cart:
                                if item['Title'] == row['Title']:
                                    item['quantity'] += 1
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    'Title': row['Title'],
                                    'Price': row['Price'],
                                    'quantity': 1
                                })
                            st.toast(f"تم إضافة {row['Title']} للسلة")
                            st.rerun()

            with t1:
                show_products(df_store[df_store['Category'].str.contains('أجهزة', na=False)])
            with t2:
                show_products(df_store[df_store['Category'].str.contains('شمعات', na=False)])

        # --- نافذة سلة التسوق (عرض المشتريات) ---
        if st.session_state.get('view_cart', False):
            with st.sidebar:
                st.header("🛒 مشترياتك")
                if not st.session_state.cart:
                    st.write("السلة فارغة حالياً")
                else:
                    total_price = 0
                    for index, item in enumerate(st.session_state.cart):
                        subtotal = int(item['Price']) * item['quantity']
                        total_price += subtotal
                        st.write(f"**{item['Title']}**")
                        st.write(f"{item['quantity']} × {item['Price']} = {subtotal} ج.م")
                        if st.button("❌ حذف", key=f"del_{index}"):
                            st.session_state.cart.pop(index)
                            st.rerun()
                        st.divider()
                    
                    # عرض الإجمالي في خانة مميزة
                    st.success(f"**الإجمالي: {total_price} ج.م**")
                    
                    # خيارات الدفع وإتمام الطلب
                    st.subheader("💳 تفاصيل الدفع والطلب")
                    pay_method = st.radio("طريقة الدفع المفضلة:", ["عند الاستلام", "فودافون كاش / انستا باي"])
                    
                    cust_name = st.text_input("الاسم لزوم التوصيل")
                    cust_address = st.text_input("عنوان التوصيل بالتفصيل")
                    
                    if st.button("✅ تأكيد الطلب عبر واتساب"):
                        if not cust_name or not cust_address:
                            st.error("يرجى إدخال الاسم والعنوان")
                        else:
                            # بناء نص الرسالة المنظم
                            order_details = ""
                            for item in st.session_state.cart:
                                order_details += f"- {item['Title']} (عدد {item['quantity']})\n"
                            
                            final_msg = (
                                f"طلب شراء جديد من المتجر 🛒\n"
                                f"--------------------------\n"
                                f"👤 العميل: {cust_name}\n"
                                f"📍 العنوان: {cust_address}\n"
                                f"💰 الإجمالي: {total_price} ج.م\n"
                                f"💳 طريقة الدفع: {pay_method}\n"
                                f"📦 المنتجات:\n{order_details}"
                            )
                            
                            import urllib.parse
                            wa_url = f"https://wa.me/2{COMPANY_PHONE}?text={urllib.parse.quote(final_msg)}"
                            st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none; background-color:#25D366; color:white; padding:12px; border-radius:8px; display:block; text-align:center;">إرسال الطلب الآن 📲</a>', unsafe_allow_html=True)
                
                if st.button("إغلاق السلة"):
                    st.session_state.view_cart = False
                    st.rerun()
    # --- 9. اطلب صيانة فوراً ⚙️ ---
    elif menu == "اطلب صيانة فوراً ⚙️":
        st.header("⚙️ طلب صيانة فورية")
        with st.form("urgent_m_form"):
            u_name = st.text_input("الاسم بالكامل")
            u_phone = st.text_input("رقم الهاتف")
            u_address = st.text_input("العنوان")
            u_problem = st.selectbox("نوع المشكلة", ["طلب تغيير شمعات", "تسريب مياه", "عطل في الموتور", "تغير طعم المياه"])
            u_notes = st.text_area("تفاصيل إضافية")
            
            if st.form_submit_button("إرسال الطلب عبر واتساب"):
                order_msg = f"طلب صيانة جديد:\nالاسم: {u_name}\nالهاتف: {u_phone}\nالمشكلة: {u_problem}\nالعنوان: {u_address}"
                import urllib.parse
                wa_url = f"https://wa.me/2{COMPANY_PHONE}?text={urllib.parse.quote(order_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none; background-color:#25D366; color:white; padding:10px; border-radius:5px;">✅ اضغط هنا لتأكيد الطلب عبر واتساب</a>', unsafe_allow_html=True)
