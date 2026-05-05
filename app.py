import base64
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
import io
import os
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# --- 1. الإعدادات والبيانات الأساسية ---
ADMIN_PASSWORD = "HgM18082019$&)" 
USER_PASSWORD = "456"

# 1. المعرف الخاص بملفك (تم استخراجه من اللينك الذي أرسلته)
SPREADSHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"

# 2. رابط الـ Web App الصحيح (يجب أن يكون للمكرو وليس للشيت)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwSW9s7nKgp5_fPRh9P7a5UqJ84bYfJrs7jkwTkCVRAFvHY3DZEcQfZ0PBGY4ksapT-aw/exec"

LOGO_PATH = "logo.png"
COMPANY_PHONE = "01286609535"

# --- 2. تهيئة الجلسة (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# --- 3. الدوال المساعدة المركزية ---
def format_ar(text):
    if text is None or str(text).strip().lower() in ["none", "nan", "null", ""]: 
        return "-"
    return get_display(reshape(str(text)))

def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "none": return 0
        return int(float(str(val).replace(',', '').strip()))
    except: return 0

def parse_dt(val):
    if not val or str(val).strip().lower() == "none": return None
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        # استخدام الرابط الصحيح للسكريبت
        response = requests.post(WEB_APP_URL, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=1)
def load_data(gid):
    # تعديل الرابط ليكون بصيغة التصدير CSV مع استخدام المعرف الخاص بك
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # إضافة مؤشر الصفوف للتعامل مع التعديل والحذف لاحقاً
        df['row_index_internal'] = range(2, len(df) + 2)
        return df.replace({pd.NA: "", None: "", "None": "", "none": ""})
    except: 
        return pd.DataFrame()

# --- 4. كلاس الـ PDF وتوليد التقارير (لا تغيير هنا) ---
# ... (بقية كود الـ PDF كما هو لديك)

# --- 5. تحميل كافة الجداول بالأرقام التي أرسلتها ---
# تأكد أن هذه الأرقام تطابق الـ gid في شريط العنوان لكل صفحة عندك
df_c = load_data("0")              # صفحة العملاء
df_m = load_data("2120582392")     # صفحة الصيانات
df_inv = load_data("1767710106")    # صفحة المخزن
df_exp = load_data("288947510")     # صفحة المصروفات
df_store = load_data("1129472026")  # صفحة المنتجات

# تحويل التواريخ فور التحميل لضمان عمل "جدول المواعيد"
if not df_m.empty and 'visit_date' in df_m.columns:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

if not df_exp.empty and 'date' in df_exp.columns:
    df_exp['exp_date_dt'] = df_exp['date'].apply(parse_dt)
# --- 6. نظام تسجيل الدخول ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Healthy Water - Login", layout="centered")
    st.title("🚰 Healthy Water System")
    t1, t2 = st.tabs(["🔒 الأدمن", "👤 العميل"])
    
    with t1:
        pwd_input = st.text_input("كلمة السر", type="password")
        if st.button("دخول الأدمن"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
    
    with t2:
        phone_input = st.text_input("رقم الهاتف المسجل")
        if st.button("دخول العميل"):
            if phone_input.strip() != "":
                clean_phone = str(phone_input).strip()
                available_phone_cols = [col for col in df_c.columns if 'phone' in col.lower()]
                if available_phone_cols:
                    mask = df_c[available_phone_cols].astype(str).apply(lambda x: x.str.contains(clean_phone, na=False)).any(axis=1)
                    match = df_c[mask]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "customer"
                        st.session_state.customer_data = match
                        st.rerun()
                    else:
                        st.error("عذراً، هذا الرقم غير مسجل لدينا.")
    st.stop()

# --- 7. واجهة التطبيق الرئيسية (بعد تسجيل الدخول) ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# زر تسجيل الخروج في الشريط الجانبي
if st.sidebar.button("🚪 تسجيل خروج"):
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.rerun()

if st.session_state.user_type == "admin":
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    admin_options = ["بيانات العملاء", "إضافة عميل جديد", "جدول المواعيد 📅", "تسجيل صيانة", "المخزن 📦", "الاحتياجات 🚨", "المصروفات", "الأرباح 📈", "المتجر 🛒", "إدارة المنتجات ⚙️", "اطلب صيانة فوراً ⚙️"]
    menu = st.sidebar.radio("القائمة", admin_options)
    
    if menu == "بيانات العملاء":
        st.header("📋 سجل العملاء")
        search = st.text_input("بحث عن عميل بالاسم أو الهاتف:")
        # أضف كود عرض العملاء هنا

    elif menu == "إضافة عميل جديد":
        st.header("➕ إضافة عميل جديد")
        with st.form("new_cust_form"):
            name = st.text_input("اسم العميل")
            phone = st.text_input("رقم الهاتف")
            area = st.text_input("المنطقة")
            address = st.text_input("العنوان بالتفصيل")
            install_date = st.date_input("تاريخ التركيب", datetime.now())
            cycle = st.number_input("دورة الصيانة (بالشهور)", value=3)
            submit = st.form_submit_button("حفظ العميل")
            if submit:
                if name and phone:
                    customer_data = [name, phone, "", "", "", "", address, area, "", str(install_date), cycle, "نشط"]
                    if execute_gsheet_action("append", "Customers", data=customer_data):
                        st.success(f"تم إضافة العميل {name} بنجاح!")
                        st.cache_data.clear()
                    else:
                        st.error("فشل الاتصال بجوجل شيت")
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف")

    # يمكن إضافة باقي الـ elif لكل خيار في المنيو هنا بنفس النمط

elif st.session_state.user_type == "customer":
    st.header("👋 أهلاً بك")
    st.write("هنا تظهر بياناتك وصياناتك القادمة")
    # أضف كود واجهة العميل هنا

elif menu == "بيانات العملاء":
        st.header("👥 إدارة العملاء")
        search = st.text_input("🔍 بحث (اسم، هاتف، منطقة، ID)")
        
        filtered = df_c[df_c.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)] if search else df_c
        
        if not filtered.empty:
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
                                
                            show_cols = ['visit_date'] + [c for c in check_cols if c in display_hist.columns] + ['amount', 'notes']
                            st.dataframe(display_hist[show_cols], use_container_width=True, hide_index=True)
                                
                            if st.button("📄 تحميل تقرير PDF", key=f"pdf_{r['row_index_internal']}"):
                                pdf_data = generate_customer_pdf(r, cust_hist)
                                st.download_button(
                                    label="اضغط لبدء التحميل",
                                    data=pdf_data,
                                    file_name=f"{r['name']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_{r['row_index_internal']}"
                                )
                            
                        phones = [r.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(r.get(p, '')).strip() != ""]
                        for ph in phones:
                            st.markdown(f"<b>📞 {ph}</b> <a href='tel:{ph}'>اتصال</a> | <a href='https://wa.me/2{ph}'>واتساب</a>", unsafe_allow_html=True)

elif menu == "جدول المواعيد 📅":
    st.header("📅 جدول مواعيد الصيانة")
    today = datetime.now().date()
    days_to_show = []
    curr = today
                
    while len(days_to_show) < 7:
        if curr.weekday() != 4: # استثناء يوم الجمعة
            days_to_show.append(curr)
        curr += timedelta(days=1)
                    
    for d in days_to_show:
        st.subheader(f"📆 {d.strftime('%A, %Y-%m-%d')}")
            
        # فلترة العملاء النشطين وتوقع مواعيدهم
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
                                        
                            show_cols = ['visit_date'] + [c for c in check_cols if c in display_hist.columns] + ['amount', 'notes']
                            st.dataframe(display_hist[show_cols], use_container_width=True, hide_index=True)
                                        
                            if st.button("📄 تحميل PDF", key=f"pdf_sch_{cust['row_index_internal']}_{d}"):
                                pdf_data = generate_customer_pdf(cust, cust_hist)
                                st.download_button(label="بدء التحميل", data=pdf_data, file_name=f"{cust['name']}.pdf", mime="application/pdf", key=f"btn_dl_{cust['row_index_internal']}_{d}")
                                    
                        phones = [cust.get(p) for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4'] if str(cust.get(p, '')).strip() != ""]
                        for ph in phones:
                            st.markdown(f"<b>📞 {ph}</b> <a href='tel:{ph}'>اتصال</a> | <a href='https://wa.me/2{ph}'>واتساب</a>", unsafe_allow_html=True)
                                    
                        if st.button("🔧 تسجيل صيانة الآن", key=f"go_reg_{cust['row_index_internal']}_{d}"):
                            st.session_state.target_customer = cust['name']
                            st.session_state.menu_choice = "تسجيل صيانة"
                            st.rerun()



elif menu == "تسجيل صيانة":
        st.header("🔧 تسجيل زيارة صيانة")

        # التأكد من وجود مفتاح للتحكم في إعادة ضبط النموذج
        if "form_reset_key" not in st.session_state:
            st.session_state.form_reset_key = 0

        default_idx = 0
        if 'target_customer' in st.session_state:
            try:
                default_idx = df_c['name'].tolist().index(st.session_state.target_customer)
            except:
                pass
                
        with st.form("main_m_form", clear_on_submit=False):
            selected_name = st.selectbox("اختر العميل", df_c['name'].tolist(), index=default_idx)
                
            # إضافة الـ key لكل مدخل ليتم تصفيره عند تحديث الـ form_reset_key
            v_date = st.date_input("تاريخ الزيارة", datetime.now(), key=f"date_{st.session_state.form_reset_key}")
            c1, c2, c3 = st.columns(3)
            p1 = c1.checkbox("P1", key=f"p1_{st.session_state.form_reset_key}")
            p2 = c2.checkbox("P2", key=f"p2_{st.session_state.form_reset_key}")
            p3 = c3.checkbox("P3", key=f"p3_{st.session_state.form_reset_key}")
            mem = c1.checkbox("Membrane", key=f"mem_{st.session_state.form_reset_key}")
            post = c2.checkbox("Post Carbon", key=f"post_{st.session_state.form_reset_key}")
            calc = c3.checkbox("Calcite", key=f"calc_{st.session_state.form_reset_key}")
            infra = c1.checkbox("Infrared", key=f"infra_{st.session_state.form_reset_key}")
                
            other_choice = st.selectbox("قطع غيار أخرى (Other)", [""] + df_inv['item_name'].tolist(), key=f"other_{st.session_state.form_reset_key}")
            amt = st.number_input("المبلغ المحصل (Amount)", step=1, key=f"amt_{st.session_state.form_reset_key}")
            nts = st.text_area("ملاحظات", key=f"nts_{st.session_state.form_reset_key}")
            spec_d = st.date_input("موعد زيارة استثنائي (اختياري)", value=None, key=f"spec_{st.session_state.form_reset_key}")
                
            if st.form_submit_button("حفظ الزيارة"):
                cust_info = df_c[df_c['name'] == selected_name]
                customer_id = str(cust_info['phone'].values[0]) if not cust_info.empty else ""
                    
                data_to_send = [selected_name, str(v_date), p1, p2, p3, mem, post, calc, infra, other_choice, amt, nts, str(spec_d) if spec_d else "", customer_id]
                    
                if execute_gsheet_action("append", "Maintenance", data_to_send):
                    st.success(f"✅ تم تسجيل صيانة {selected_name} بنجاح!")
                    # تغيير مفتاح الـ key يؤدي لتصفير جميع الخانات المرتبطة به
                    st.session_state.form_reset_key += 1
                    st.cache_data.clear() 
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بالسيرفر، تأكد من رابط الـ Web App")

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
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("خطأ: تعذر الوصول للسيرفر لتحديث البيانات.")

        st.divider()
        st.metric(label="إجمالي رأس المال (قيمة المخزون الكلية)", value=f"{total_inventory_value} ج.م")
        st.sidebar.metric("إجمالي رأس المال", f"{total_inventory_value} ج.م")

elif menu == "الاحتياجات 🚨":
    st.header("🚨 أصناف تحت حد الأمان")
    needs = df_inv[df_inv['quantity'].apply(to_num) <= df_inv['min_limit'].apply(to_num)]
    if not needs.empty:
        st.table(needs[['item_name', 'quantity', 'min_limit']])
    else:
        st.success("كل الأصناف متوفرة فوق حد الأمان.")

elif menu == "المصروفات":
    st.header("💵 إدارة المصروفات")
    selected_date = st.date_input("تاريخ المصروفات", datetime.now())
            
    todays_m = df_m[df_m['v_date_dt'].dt.date == selected_date] if not df_m.empty else pd.DataFrame()
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
                st.cache_data.clear()
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
                if not day_m.empty:
                    day_rev = day_m['amount_num'].sum()
                
            day_exp_total = 0
            if not df_exp.empty and 'exp_date_dt' in df_exp.columns:
                day_ex = df_exp[df_exp['exp_date_dt'].dt.date == target_date]
                if not day_ex.empty:
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
        sel_year_m = c1.selectbox("السنة", range(2024, 2030), index=2) # افتراض 2026 كافتراضي
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
        import plotly.express as px
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["مقارنة أيام الشهر", "مقارنة شهور السنة", "مقارنة السنوات"])

        with chart_tab1:
            m_data = []
            for d in month_days:
                m_data.append({"التاريخ": str(d), "الربح": get_daily_net(d)})
            df_m_chart = pd.DataFrame(m_data)
            st.plotly_chart(px.line(df_m_chart, x="التاريخ", y="الربح", title=f"تذبذب الأرباح خلال شهر {sel_month}"), use_container_width=True)

        with chart_tab2:
            y_data = []
            for m in range(1, 13):
                m_days = calendar.monthrange(sel_year_y, m)[1]
                m_sum = sum([get_daily_net(datetime(sel_year_y, m, d).date()) for d in range(1, m_days + 1)])
                y_data.append({"الشهر": calendar.month_name[m], "الربح": m_sum})
            df_y_chart = pd.DataFrame(y_data)
            st.plotly_chart(px.bar(df_y_chart, x="الشهر", y="الربح", title=f"أداء الشهور خلال سنة {sel_year_y}"), use_container_width=True)

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
            st.plotly_chart(px.bar(df_all_y, x="السنة", y="إجمالي الربح", title="مقارنة الأرباح السنوية"), use_container_width=True)
            

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
                
        # وصف المنتج
        p_desc = st.text_area("وصف المنتج التفصيلي", height=200)
                
        if st.form_submit_button("حفظ المنتج"):
            if not uploaded_files:
                st.error("يرجى رفع صورة واحدة على الأقل")
            elif not p_title:
                st.warning("يرجى إدخال اسم المنتج")
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
                    st.success("تم إضافة المنتج بنجاح مع الصور!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("فشل الاتصال بجوجل شيت")

# --- 8. المتجر 🛒 (النظام المتكامل: سلة + دفع + إجمالي) ---
elif menu == "المتجر 🛒":
    st.header("🛒 متجر Healthy Water")
            
    # 1. تهيئة سلة التسوق في الذاكرة (Session State)
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'view_cart' not in st.session_state:
        st.session_state.view_cart = False

    # 2. أيقونة السلة في الأعلى
    cart_count = sum(item['quantity'] for item in st.session_state.cart)
    col_header, col_cart = st.columns([0.8, 0.2])
    with col_cart:
        if st.button(f"🛒 السلة ({cart_count})"):
            st.session_state.view_cart = not st.session_state.view_cart
            
    # 3. عرض محتويات السلة إذا كانت مفتوحة
    if st.session_state.view_cart:
        st.subheader("🛍️ محتويات السلة")
        if not st.session_state.cart:
            st.info("السلة فارغة حالياً")
        else:
            total_cart = 0
            for i, item in enumerate(st.session_state.cart):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(item['Title'])
                c2.write(f"{item['Price']} ج.م")
                c3.write(f"الكمية: {item['quantity']}")
                if c4.button("❌", key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
                total_cart += item['Price'] * item['quantity']
                
            st.divider()
            st.markdown(f"### الإجمالي: {total_cart} ج.م")
            if st.button("إتمام الطلب ✅"):
                st.success("تم استلام طلبك، سنتواصل معك قريباً!")
                st.session_state.cart = []
                st.session_state.view_cart = False
                st.rerun()
        st.divider()

    # 4. تحميل وعرض المنتجات
    STORE_GID = "1168172935" 
    df_store_data = load_data(STORE_GID)
            
    if df_store_data.empty:
        st.warning("لا توجد منتجات معروضة حالياً.")
    else:
        # عرض الأقسام (Tabs)
        t1, t2 = st.tabs(["💧 الأجهزة", "🛡️ الشمعات"])
                
        def show_products(filtered_df):
            if filtered_df.empty:
                st.write("لا توجد منتجات في هذا القسم.")
                return
                
            # عرض المنتجات في شبكة (Grid) من عمودين
            cols = st.columns(2)
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                with cols[i % 2]:
                    with st.container(border=True):
                        # معالجة الصور
                        imgs = str(row.get('Images', '')).split("||")
                        if imgs and "base64" in imgs[0]:
                            st.image(imgs[0], use_container_width=True)
                        else:
                            st.info("لا توجد صورة")
                                
                        st.subheader(row.get('Title', 'منتج بدون اسم'))
                        price = to_num(row.get('Price', 0))
                        st.write(f"**السعر:** {price} ج.م")
                            
                        # أزرار الإضافة للسلة
                        if st.button("➕ أضف للسلة", key=f"add_{row.get('row_index_internal', i)}"):
                            found = False
                            for item in st.session_state.cart:
                                if item['Title'] == row['Title']:
                                    item['quantity'] += 1
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    'Title': row['Title'],
                                    'Price': price,
                                    'quantity': 1
                                })
                            st.toast(f"تم إضافة {row['Title']} للسلة")
                            st.rerun()

        with t1:
            # فلترة المنتجات حسب تصنيف "أجهزة"
            category_col = 'Category' if 'Category' in df_store_data.columns else df_store_data.columns[4]
            show_products(df_store_data[df_store_data[category_col].astype(str).str.contains('أجهزة', na=False)])
            
        with t2:
            # فلترة المنتجات حسب تصنيف "شمعات"
            category_col = 'Category' if 'Category' in df_store_data.columns else df_store_data.columns[4]
            show_products(df_store_data[df_store_data[category_col].astype(str).str.contains('شمعات', na=False)])
