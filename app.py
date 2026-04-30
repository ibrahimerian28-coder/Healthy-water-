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
        if pd.isna(val) or str(val).strip() == "":
            return 0
        return int(float(str(val).replace(',', '').strip()))
    except:
        return 0

def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(WEB_APP_URL, json=payload, timeout=15)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=1)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        df['row_index_internal'] = range(2, len(df) + 2)
        return df.fillna("")
    except:
        return pd.DataFrame()

def parse_dt(val):
    if not val or str(val).strip() == "":
        return None
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try:
            return pd.to_datetime(val, format=fmt)
        except:
            continue
    return pd.to_datetime(val, errors='coerce')

def read_gsheet(sheet_name):
    gids = {"Store_Products": "123456789"}
    return load_data(gids.get(sheet_name, "0"))
    def calculate_day_cogs(target_date):
    if df_m.empty or df_inv.empty:
        return 0
    day_maint = df_m[df_m['v_date_dt'].dt.date == target_date]
    if day_maint.empty:
        return 0
    # فلترة الصيانات التي تمت في هذا التاريخ
    day_maint = df_m[df_m['v_date_dt'].dt.date == target_date]
    if day_maint.empty:
        return 0
    
    total_cogs = 0
    # خريطة لربط اسم العمود في شيت الصيانة باسم الصنف في شيت المخزن
    parts_map = {
        'P1': 'P1', 'P2': 'P2', 'P3': 'P3', 
        'membrane': 'Membrane', 'post_carbon': 'Post Carbon', 
        'Calcite': 'Calcite', 'infrared': 'Infrared'
    }
    
    for _, row in day_maint.iterrows():
        for col, inv_name in parts_map.items():
            # إذا كانت الخانة معلمة كتم (True أو ✅)
            if str(row.get(col, '')).lower() in ['true', '1', '✅']:
                cost_row = df_inv[df_inv['item_name'] == inv_name]
                if not cost_row.empty:
                    total_cogs += to_num(cost_row['cost_price'].values[0])
        # حساب القطع الإضافية (Other)
        other_item = row.get('other', '')
        if other_item:
            cost_row = df_inv[df_inv['item_name'] == other_item]
            if not cost_row.empty:
                total_cogs += to_num(cost_row['cost_price'].values[0])
    return total_cogs

# --- 3. تحميل البيانات ---
df_c = load_data("0")  # Customers
df_m = load_data("2120582392")  # Maintenance
df_inv = load_data("1767710106")  # Inventory
df_exp = load_data("288947510")  # Expenses
df_store = load_data("1168172935")  # Store_Products

# التأكد من تحويل الأعمدة الرقمية
if not df_store.empty:
    df_store['Price'] = df_store['Price'].apply(to_num)
    df_store['Old_Price'] = df_store['Old_Price'].apply(to_num)

st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="🚰")

if 'user_type' not in st.session_state:
    st.session_state.user_type = None

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
        except:
            pass

    def format_ar(text):
        if not text or str(text).strip() == "":
            return ""
        if not has_arabic:
            return "".join([c for c in str(text) if ord(c) < 128])
        return get_display(reshape(str(text)))

    try:
        pdf.image(LOGO_PATH, x=197, y=10, w=90)
    except:
        pass

    pdf.set_xy(10, 15)
    if has_arabic:
        pdf.set_font('ArabicFont', '', 24)
    else:
        pdf.set_font('Arial', 'B', 22)

    pdf.cell(150, 15, format_ar(f"تقرير صيانة: {cust_row['name']}"), ln=True, align='R')

    if has_arabic:
        pdf.set_font('ArabicFont', '', 14)
    else:
        pdf.set_font('Arial', '', 12)

    pdf.set_x(10)
    pdf.cell(150, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')

    pdf.set_y(60)

    cols = ['ملاحظات', 'المبلغ', 'أخرى', 'Infra', 'Calc', 'Post', 'Mem', 'P3', 'P2', 'P1', 'التاريخ']
    widths = [75, 17, 30, 15, 15, 15, 15, 15, 15, 15, 30]

    pdf.set_fill_color(173, 216, 230)

    if has_arabic:
        pdf.set_font('ArabicFont', '', 11)

    for i, col in enumerate(cols):
        pdf.cell(widths[i], 10, format_ar(col), 1, 0, 'C', True)
    pdf.ln()

    if has_arabic:
        pdf.set_font('ArabicFont', '', 10)

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
                st.session_state.user_type = "admin"
                st.rerun()

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
                        # --- واجهة العميل (Customer Interface) ---
if st.session_state.user_type == "customer":

    cust_phone = st.session_state.get('user_id')

    # --- تعريف الأجهزة ---
    if not df_c.empty:
        user_devices = df_c[df_c['phone'] == cust_phone]
    else:
        user_devices = pd.DataFrame()

    # --- القائمة الجانبية ---
    customer_menu = st.sidebar.radio(
        "القائمة الرئيسية",
        ["بياناتي وأجهزتي", "المتجر 🛒", "اطلب صيانة فوراً ⚙️"]
    )

    st.sidebar.divider()

    if st.sidebar.button("🔓 تسجيل الخروج", use_container_width=True):
        st.session_state.user_type = None
        st.session_state.authenticated = False
        st.rerun()

    # --- 1. بياناتي ---
    if customer_menu == "بياناتي وأجهزتي":
        st.header(f"👋 مرحباً بك")

        if user_devices.empty:
            st.warning("لم يتم العثور على أجهزة مسجلة لهذا الرقم.")
        else:
            st.info(f"موجود {len(user_devices)} أجهزة مسجلة برقمك")

            for index, row in user_devices.iterrows():
                with st.expander(f"📱 جهاز: {row['name']}", expanded=True):

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**الاسم:** {row['name']}")
                        st.write(f"**العنوان:** {row['adress']}")

                    with col2:
                        st.write(f"**تاريخ التركيب:** {row['install_date']}")
                        st.write(f"**حالة الجهاز:** {row['status']}")

                    st.divider()
                    st.subheader("🗓️ سجل الصيانة")

                    if not df_m.empty:
                        device_maint = df_m[df_m['name'] == row['name']]

                        if not device_maint.empty:
                            display_cols = ['visit_date', 'P1', 'P2', 'P3', 'membrane', 'amount']
                            st.dataframe(device_maint[display_cols], use_container_width=True)
                        else:
                            st.write("لا توجد صيانات مسجلة.")

    # --- 2. المتجر ---
    elif customer_menu == "المتجر 🛒":
        st.subheader("🛒 متجر Healthy Water")

        if df_store.empty:
            st.info("المتجر فارغ حالياً.")
        else:
            st.write("المنتجات المتاحة...")

    # --- 3. طلب صيانة ---
    elif customer_menu == "اطلب صيانة فوراً ⚙️":
        st.subheader("🛠️ طلب دعم فني سريع")

        with st.form("cust_urgent_form"):

            default_name = ""
            if not user_devices.empty:
                default_name = user_devices.iloc[0]['name']

            u_name = st.text_input("اسم صاحب الجهاز", value=default_name)

            u_problem = st.selectbox(
                "نوع المشكلة",
                ["طلب تغيير شمعات", "تسريب مياه", "عطل في الموتور", "تغير طعم المياه"]
            )

            u_notes = st.text_area("وصف إضافي")

            if st.form_submit_button("إرسال الطلب عبر واتساب"):
                import urllib.parse

                msg = f"طلب صيانة:\nالاسم: {u_name}\nالهاتف: {cust_phone}\nالمشكلة: {u_problem}"

                wa_url = f"https://wa.me/2{COMPANY_PHONE}?text={urllib.parse.quote(msg)}"

                st.markdown(
                    f'<a href="{wa_url}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-decoration:none;">تأكيد عبر واتساب ✅</a>',
                    unsafe_allow_html=True
                )
                # --- واجهة الأدمن ---
if st.session_state.user_type == "admin":

    menu = st.sidebar.radio(
        "القائمة الرئيسية",
        [
            "إضافة عميل جديد",
            "بيانات العملاء",
            "جدول المواعيد 📅",
            "تسجيل صيانة",
            "المخزن 📦",
            "الاحتياجات 🚨",
            "المصروفات",
            "الأرباح 📈",
            "إدارة المنتجات ⚙️"
        ]
    )

    st.sidebar.divider()

    if st.sidebar.button("🔓 تسجيل الخروج", use_container_width=True):
        st.session_state.user_type = None
        st.rerun()

    # --- إضافة عميل ---
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

            address = st.text_area("العنوان (adress)")

            area = st.selectbox("المنطقة", areas_list)
            new_area = st.text_input("أو أضف منطقة جديدة")
            final_area = new_area if new_area else area

            loc = st.text_input("رابط اللوكيشن")

            inst_date = st.date_input("تاريخ التركيب")
            cycle = st.number_input("دورة الصيانة (شهور)", value=3)

            status = st.selectbox("الحالة", ["نشط", "راكد"])

            if st.form_submit_button("حفظ العميل"):
                data = [
                    name, phone, p1, p2, p3, p4,
                    address, final_area, loc,
                    str(inst_date), cycle, status
                ]

                if execute_gsheet_action("append", "Customers", data):
                    st.success("تم الحفظ بنجاح")
                    st.rerun()

    # --- عرض العملاء ---
    elif menu == "بيانات العملاء":
        st.header("👥 إدارة العملاء")

        search = st.text_input("🔍 بحث")

        if search:
            filtered = df_c[df_c.astype(str).apply(
                lambda x: x.str.contains(search, case=False)
            ).any(axis=1)]
        else:
            filtered = df_c

        for area, group in filtered.groupby('area'):
            st.markdown(f"### 📍 {area}")

            for _, r in group.iterrows():
                with st.expander(f"👤 {r['name']} | 📞 {r['phone']}"):

                    c1, c2 = st.columns(2)

                    c1.write(f"🏠 {r.get('adress', '')}")
                    c1.write(f"📅 {r.get('install_date', '')}")

                    cust_hist = df_m[df_m['name'] == r['name']].sort_values(
                        'v_date_dt', ascending=False
                    )

                    if not cust_hist.empty:
                        last_v = cust_hist.iloc[0]['v_date_dt']
                        next_v = last_v + timedelta(days=to_num(r['cycle']) * 30)

                        st.warning(f"الزيارة القادمة: {next_v.date()}")

                        display = cust_hist.copy()

                        check_cols = ['P1', 'P2', 'P3', 'membrane']

                        for col in check_cols:
                            if col in display.columns:
                                display[col] = display[col].apply(
                                    lambda x: "✅" if str(x).lower() in ['true', '1', '✅'] else "❌"
                                )

                        st.dataframe(display[['visit_date'] + check_cols + ['amount']])

                        col_pdf, col_maint = st.columns(2)
                        with col_pdf:
    if st.button("📄 PDF", key=f"pdf_{r['row_index_internal']}"):
        pdf_data = generate_customer_pdf(r, cust_hist)
        # تأكد أن download_button تبدأ وتنتهي بأقواس صحيحة
        st.download_button(
            label="تحميل",
            data=pdf_data,
            file_name=f"{r['name']}.pdf",
            mime="application/pdf"
        )
                                # --- جدول المواعيد ---
    elif menu == "جدول المواعيد 📅":
        st.header("📅 جدول مواعيد الصيانة")

        today = datetime.now().date()
        days_to_show = []

        curr = today
        while len(days_to_show) < 7:
            if curr.weekday() != 4:  # استثناء الجمعة
                days_to_show.append(curr)
            curr += timedelta(days=1)

        for d in days_to_show:
            st.subheader(f"📆 {d.strftime('%A, %Y-%m-%d')}")

            for _, cust in df_c[df_c['status'] == "نشط"].iterrows():

                last_m_all = df_m[df_m['name'] == cust['name']].sort_values('v_date_dt')

                if not last_m_all.empty:
                    last_m = last_m_all.iloc[-1]

                    spec_date = parse_dt(last_m.get('special_date', ""))
                    next_v = spec_date.date() if spec_date else (
                        last_m['v_date_dt'] + timedelta(days=to_num(cust['cycle']) * 30)
                    ).date()

                    if next_v == d or (next_v < today and d == days_to_show[0]):

                        with st.expander(f"👤 {cust['name']} | 📞 {cust['phone']}"):

                            st.write(f"🏠 {cust.get('adress', '')}")

                            cust_hist = df_m[df_m['name'] == cust['name']].sort_values(
                                'v_date_dt', ascending=False
                            )

                            if not cust_hist.empty:
                                display = cust_hist.copy()

                                check_cols = ['P1', 'P2', 'P3', 'membrane']

                                for col in check_cols:
                                    if col in display.columns:
                                        display[col] = display[col].apply(
                                            lambda x: "✅" if str(x).lower() in ['true', '1', '✅'] else "❌"
                                        )

                                st.dataframe(display[['visit_date'] + check_cols + ['amount']])

                            if st.button("📄 PDF", key=f"pdf_sch_{cust['row_index_internal']}_{d}"):
                                pdf_data = generate_customer_pdf(cust, cust_hist)

                                st.download_button(
                                    "تحميل",
                                    data=pdf_data,
                                    file_name=f"{cust['name']}.pdf",
                                    mime="application/pdf"
                                )

                            if st.button("🔧 تسجيل صيانة", key=f"go_{cust['row_index_internal']}_{d}"):
                                st.session_state.target_customer = cust['name']
                                st.session_state.menu_choice = "تسجيل صيانة"
                                st.rerun()

    # --- تسجيل صيانة ---
    elif menu == "تسجيل صيانة":
        st.header("🔧 تسجيل زيارة صيانة")

        default_idx = 0

        if 'target_customer' in st.session_state:
            try:
                default_idx = df_c['name'].tolist().index(
                    st.session_state.target_customer
                )
            except:
                pass

        with st.form("main_m_form"):

            selected_name = st.selectbox(
                "اختر العميل",
                df_c['name'].tolist(),
                index=default_idx
            )

            v_date = st.date_input("تاريخ الزيارة", datetime.now())

            c1, c2, c3 = st.columns(3)

            p1 = c1.checkbox("P1")
            p2 = c2.checkbox("P2")
            p3 = c3.checkbox("P3")

            mem = c1.checkbox("Membrane")
            post = c2.checkbox("Post Carbon")
            calc = c3.checkbox("Calcite")
            infra = c1.checkbox("Infrared")

            other_choice = st.selectbox(
                "قطع أخرى",
                [""] + df_inv['item_name'].tolist()
            )

            amt = st.number_input("المبلغ", step=1)
            notes = st.text_area("ملاحظات")

            spec_d = st.date_input("موعد استثنائي", value=None)

            if st.form_submit_button("حفظ"):

                cid = df_c[df_c['name'] == selected_name]['phone'].values[0]

                data = [
                    selected_name,
                    str(v_date),
                    p1, p2, p3,
                    mem, post, calc, infra,
                    other_choice,
                    amt,
                    notes,
                    str(spec_d) if spec_d else "",
                    cid
                ]

                if execute_gsheet_action("append", "Maintenance", data):
                    st.success("تم التسجيل بنجاح")
                    st.rerun()
                        # --- المخزن ---
    elif menu == "المخزن 📦":
        st.header("📦 إدارة المخزن")

        total_inventory_value = 0

        for i, r in df_inv.iterrows():
            current_qty = to_num(r.get('quantity', 0))
            current_min = to_num(r.get('min_limit', 0))
            current_cost = to_num(r.get('cost_price', 0))

            item_total = current_qty * current_cost
            total_inventory_value += item_total

            with st.expander(f"{r['item_name']} | الكمية: {current_qty}"):

                with st.form(f"inv_{i}"):

                    c1, c2 = st.columns(2)

                    u_qty = c1.number_input("الكمية", value=current_qty)
                    u_min = c2.number_input("حد الأمان", value=current_min)
                    u_cost = c1.number_input("سعر التكلفة", value=current_cost)

                    st.info(f"قيمة الصنف: {u_qty * u_cost} ج")

                    if st.form_submit_button("تحديث"):

                        data = [
                            r['item_name'],
                            u_qty,
                            u_min,
                            u_cost
                        ]

                        if execute_gsheet_action(
                            "update",
                            "Inventory",
                            data,
                            row_index=r['row_index_internal']
                        ):
                            st.success("تم التحديث")
                            st.rerun()

        st.metric("إجمالي قيمة المخزن", f"{total_inventory_value} ج")

    # --- الاحتياجات ---
    elif menu == "الاحتياجات 🚨":
        st.header("🚨 أصناف ناقصة")

        needs = df_inv[
            df_inv['quantity'].apply(to_num) <= df_inv['min_limit'].apply(to_num)
        ]

        if not needs.empty:
            st.table(needs[['item_name', 'quantity', 'min_limit']])
        else:
            st.success("كل الأصناف تمام")

    # --- المصروفات ---
    elif menu == "المصروفات":
        st.header("💵 إدارة المصروفات والتكاليف")
        
        sel_date = st.date_input("اختر التاريخ لعرض البيانات", datetime.now())
        
        # عرض مصروفات اليوم المختار من الشيت
        day_exp_df = df_exp[df_exp['exp_date_dt'].dt.date == sel_date]
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📋 مصروفات اليوم المسجلة")
            if not day_exp_df.empty:
                st.dataframe(day_exp_df[['transportation', 'sundries', 'monthly_expensess', 'salaries', 'notes']], use_container_width=True)
            else:
                st.info("لا توجد مصروفات يدوية لهذا اليوم.")
        
        with c2:
            st.subheader("⚙️ تكلفة البضاعة (COGS)")
            day_cogs = calculate_day_cogs(sel_date)
            st.metric("إجمالي تكلفة الشمعات والقطع", f"{day_cogs} ج")
            st.caption("يتم حسابها تلقائياً بناءً على زيارات الصيانة في هذا اليوم وسعر التكلفة من المخزن.")

        st.divider()
        with st.form("new_exp_form"):
            st.subheader("➕ إضافة مصروف يدوي جديد")
            f1, f2 = st.columns(2)
            trans = f1.number_input("انتقالات", 0)
            neth = f2.number_input("نثريات", 0)
            monthly = f1.number_input("مصروفات شهرية", 0)
            salary = f2.number_input("رواتب", 0)
            exp_notes = st.text_area("ملاحظات إضافية")
            if st.form_submit_button("حفظ المصروف"):
                data = [str(sel_date), trans, neth, monthly, salary, exp_notes]
                if execute_gsheet_action("append", "Expenses", data):
                    st.success("تم حفظ المصروف بنجاح")
                    st.rerun()

    # --- الأرباح ---
    elif menu == "الأرباح 📈":
        st.header("📊 تقارير الأرباح والتحليل المالي")
        
        today = datetime.now().date()
        
        def get_period_stats(start, end):
            # 1. الإيرادات
            mask_m = (df_m['v_date_dt'].dt.date >= start) & (df_m['v_date_dt'].dt.date <= end)
            total_rev = df_m[mask_m]['amount_num'].sum()
            
            # 2. المصروفات اليدوية
            mask_e = (df_exp['exp_date_dt'].dt.date >= start) & (df_exp['exp_date_dt'].dt.date <= end)
            manual_exp = 0
            cols = ['transportation', 'sundries', 'monthly_expensess', 'salaries']
            if not df_exp.empty:
                for col in cols:
                    if col in df_exp.columns:
                        manual_exp += df_exp[mask_e][col].apply(to_num).sum()
            
            # 3. تكلفة البضاعة للفترة
            total_cogs = sum([calculate_day_cogs(d.date()) for d in pd.date_range(start, end)])
            
            return total_rev, (manual_exp + total_cogs), (total_rev - manual_exp - total_cogs)

        # عرض الكروت
        m1, m2, m3 = st.columns(3)
        r_d, e_d, n_d = get_period_stats(today, today)
        m1.metric("صافي ربح اليوم", f"{n_d} ج", f"إيراد: {r_d}")

        r_m, e_m, n_m = get_period_stats(today.replace(day=1), today)
        m2.metric("صافي ربح الشهر", f"{n_m} ج")

        # الرسم البياني للإيرادات
        st.subheader("📈 حركة الإيرادات آخر 10 أيام")
        last_10 = [today - timedelta(days=i) for i in range(10)]
        chart_df = pd.DataFrame({
            "التاريخ": [d.strftime('%Y-%m-%d') for d in last_10],
            "الإيراد": [df_m[df_m['v_date_dt'].dt.date == d]['amount_num'].sum() for d in last_10]
        }).sort_values("التاريخ")
        fig = px.line(chart_df, x="التاريخ", y="الإيراد", markers=True, title="نمو الإيرادات اليومي")
        st.plotly_chart(fig, use_container_width=True)

    # --- إدارة المنتجات ---
    elif menu == "إدارة المنتجات ⚙️":
        st.header("⚙️ إدارة المنتجات")

        with st.form("add_product"):

            name = st.text_input("اسم المنتج")
            price = st.number_input("السعر", min_value=0)
            old_price = st.number_input("السعر القديم", min_value=0)

            cat = st.selectbox("التصنيف", ["أجهزة", "شمعات"])

            desc = st.text_area("الوصف")
            # خانة رفع الصور (بحد أقصى 5)
            uploaded_files = st.file_uploader("ارفع صور المنتج (حتى 5 صور)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
            
            # زر الإضافة
            if st.form_submit_button("إضافة"):
                img_data = ""
                if uploaded_files:
                    # تحويل أول صورة لـ Base64 لتخزينها (كمثال للتبسيط)
                    img_data = base64.b64encode(uploaded_files[0].read()).decode()
                
                data = [name, price, old_price, cat, desc, img_data]
                if execute_gsheet_action("append", "Store_Products", data):
                    st.success("تمت إضافة المنتج بنجاح")
                    st.rerun()

            if st.form_submit_button("إضافة"):

                data = [
                    name,
                    price,
                    old_price,
                    cat,
                    desc
                ]

                if execute_gsheet_action("append", "Store_Products", data):
                    st.success("تمت الإضافة")
                    st.rerun()
