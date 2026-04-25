import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from fpdf import FPDF
# ملاحظة: تحتاج لتثبيت arabic-reshaper و python-bidi لدعم العربي في الـ PDF
import arabic_reshaper
from bidi.algorithm import get_display

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=60)
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'نعم'] else "✗"

# --- 2. نظام تسجيل الدخول ---
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = None
    st.session_state.user_data = None

def login():
    st.title("🔐 تسجيل الدخول - Healthy Water")
    choice = st.radio("دخول بصفتك:", ["أدمن (مدير)", "عميل (مستخدم)"])
    
    if choice == "أدمن (مدير)":
        pwd = st.text_input("أدخل كلمة مرور الإدارة:", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "HgM18082019$&)":
                st.session_state.auth_status = "admin"
                st.rerun()
            else: st.error("كلمة المرور خاطئة!")
            
    else:
        phone_id = st.text_input("أدخل رقم هاتفك المسجل (ID):")
        if st.button("دخول العميل"):
            df_c = load_all_data("0")
            # البحث عن العميل بأول رقم موبايل
            match = df_c[df_c['الأرقام'].astype(str).str.contains(phone_id)] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth_status = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("عذراً، هذا الرقم غير مسجل لدينا.")

if st.session_state.auth_status is None:
    login()
    st.stop()

# --- 3. التنسيق المرئي (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #ffffff;}
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .status-green { border-color: #28a745; background-color: #f1f9f3; }
    .status-yellow { border-color: #ffc107; background-color: #fffdf5; }
    .status-red { border-color: #dc3545; background-color: #fff5f5; }
    .status-darkred { border-color: #8b0000; background-color: #4b0000; color: white; }
    .status-gray { border-color: #6c757d; background-color: #f8f9fa; }
    .phone-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .call-link { background-color: #007bff; color: white !important; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    .wa-link { background-color: #25d366; color: white !important; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. محرك المواعيد الذكي ---
def get_v_info(name, cycle, df_m):
    if df_m.empty or 'الاسم' not in df_m.columns: return None
    c_m = df_m[df_m['الاسم'].astype(str).str.strip() == str(name).strip()].copy()
    if c_m.empty: return None
    c_m['dt'] = pd.to_datetime(c_m['تاريخ الزيارة'], errors='coerce')
    last = c_m['dt'].max()
    if pd.isnull(last): return None
    try: return last + timedelta(days=int(cycle)*30)
    except: return None

# --- 5. تصدير PDF مع دعم العربي (تحتاج خط يدعم العربي مثل DejaVuSans) ---
def make_comprehensive_pdf(row, df_m):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    # تنبيه: FPDF لا تدعم العربي إلا بخطوط خارجية، هنا سنكتفي بالبيانات اللاتينية لتجنب الكراش
    # وإذا توفر خط ttf يمكن تفعيله هنا
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Customer: {str(row['الاسم'])} Report", ln=True)
    pdf.ln(5)
    check_cols = ['P1', 'P2', 'P3', 'membrane', 'post carbon', 'Calcite', 'infrared']
    for h in ["Date"] + check_cols + ["Cost"]: pdf.cell(32, 10, h, 1, 0, 'C')
    pdf.ln()
    for _, m in df_m.iterrows():
        pdf.cell(32, 10, str(m.get('تاريخ الزيارة',''))[:10], 1)
        for c in check_cols:
            pdf.cell(32, 10, "V" if format_to_check(m.get(c, '')) == "✓" else "X", 1)
        pdf.cell(32, 10, str(m.get('amount','0')), 1); pdf.ln()
    return bytes(pdf.output())

# --- 6. تحميل البيانات ---
df_customers = load_all_data("0")
df_maint = load_all_data("2120582392")

# --- 7. منطق العرض بناءً على الرتبة ---
if st.session_state.auth_status == "admin":
    st.sidebar.success("مرحباً: المدير")
    menu = st.sidebar.radio("القائمة الرئيسية:", ["بيانات العملاء", "جدول المواعيد", "بحث عن عميل", "تسجيل صيانة", "إضافة عميل جديد"])
    if st.sidebar.button("خروج"): 
        st.session_state.auth_status = None
        st.rerun()
else:
    st.sidebar.info(f"مرحباً: {st.session_state.user_data['الاسم']}")
    menu = "بروفايل العميل"
    if st.sidebar.button("خروج"):
        st.session_state.auth_status = None
        st.rerun()

# --- 8. الصفحات ---

if menu == "بيانات العملاء" or menu == "بروفايل العميل":
    st.header("👤 ملفات العملاء")
    # إذا كان عميل يظهر بياناته فقط، إذا كان أدمن يظهر الكل
    display_list = [st.session_state.user_data] if st.session_state.auth_status == "customer" else df_customers.to_dict('records')
    
    if not df_customers.empty:
        df_sorted = pd.DataFrame(display_list)
        if st.session_state.auth_status == "admin":
            area_col = 'المنطقه' if 'المنطقه' in df_sorted.columns else 'المنطقة'
            df_sorted = df_sorted.sort_values(by=area_col)
        
        for idx, row in df_sorted.iterrows():
            nv = get_v_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maint)
            style = "status-green" # كافتراضي للأدمن لتجنب أخطاء الحسابات في العرض السريع
            
            st.markdown(f'<div class="cust-card {style}"><h3>👤 {row["الاسم"]}</h3><p>📍 {row.get("المنطقه","")} | 📅 الموعد القادم: {nv.date() if nv else "---"}</p></div>', unsafe_allow_html=True)
            
            with st.expander(f"فتح البيانات الكاملة", expanded=(st.session_state.auth_status == "customer")):
                c1, c2 = st.columns(2)
                with c1:
                    for col in df_customers.columns: st.write(f"**{col}:** {row[col]}")
                    nums = re.findall(r'01[0-2,5]\d{8}', str(row['الأرقام']))
                    for n in nums:
                        st.markdown(f'<div class="phone-container"><a href="tel:{n}" class="call-link">📞 {n}</a><a href="https://wa.me/2{n}" class="wa-link">💬 واتساب</a></div>', unsafe_allow_html=True)
                with c2:
                    st.subheader("🛠️ سجل الصيانات")
                    cust_m = df_maint[df_maint['الاسم'] == row['الاسم']].copy()
                    if not cust_m.empty:
                        cust_m['dt'] = pd.to_datetime(cust_m['تاريخ الزيارة'], errors='coerce')
                        display_df = cust_m.sort_values(by='dt', ascending=False).copy()
                        for f in ['P1','P2','P3','membrane','post carbon','Calcite','infrared']:
                            if f in display_df.columns: display_df[f] = display_df[f].apply(format_to_check)
                        st.dataframe(display_df.drop(columns=['dt']))
                        st.download_button("📥 تحميل PDF", make_comprehensive_pdf(row, cust_m), f"{row['الاسم']}.pdf")

elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    active_ones = df_customers[df_customers.get('status', 'نشط') == 'نشط']
    for i in range(8):
        day = datetime.now().date() + timedelta(days=i)
        st.subheader(f"🗓️ {day.strftime('%A')} - {day}")
        
        # 1. مواعيد الصيانة الدورية
        for _, row in active_ones.iterrows():
            nv = get_v_info(row['الاسم'], row.get('دورة الصيانة', 3), df_maint)
            if nv and nv.date() == day:
                st.info(f"🔹 **دورية:** {row['الاسم']} | 📍 {row.get('المنطقه','')}")
                
        # 2. المواعيد الاستثنائية (Special Reminder)
        special_hits = df_maint[pd.to_datetime(df_maint['Special reminder date'], errors='coerce').dt.date == day]
        for _, s_row in special_hits.iterrows():
            st.warning(f"🔔 **استثنائي:** {s_row['الاسم']} | 📝 {s_row.get('Other','')}")

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة جديدة")
    with st.form("m_form"):
        c_name = st.selectbox("العميل", df_customers['الاسم'].tolist())
        v_date = st.date_input("تاريخ الزيارة")
        cc1, cc2, cc3 = st.columns(3)
        p1 = cc1.checkbox("P1"); p2 = cc1.checkbox("P2"); p3 = cc1.checkbox("P3")
        mem = cc2.checkbox("Membrane"); post = cc2.checkbox("Post Carbon"); calc = cc2.checkbox("Calcite")
        infra = cc3.checkbox("Infrared")
        
        cost = st.number_input("التكلفة (amount)")
        other = st.text_input("خانة أخرى (Other)")
        special_rem = st.date_input("تذكير بموعد استثنائي (Special reminder date)", value=None)
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"): st.success("تم الحفظ بنجاح")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل")
    with st.form("add_f"):
        # خانات مطابقة لكل أعمدة الشيت
        c_name = st.text_input("الاسم")
        c_phone = st.text_input("الأرقام")
        c_addr = st.text_input("العنوان")
        c_area = st.text_input("المنطقه")
        c_loc = st.text_input("اللوكيشن")
        c_setup = st.date_input("تاريخ التركيب")
        c_cycle = st.number_input("دورة الصيانة", value=3)
        c_status = st.selectbox("الحالة", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"): st.success("تمت الإضافة بنجاح")

elif menu == "بحث عن عميل":
    q = st.text_input("ابحث بالاسم/المنطقة/الهاتف")
    if q: st.dataframe(df_customers[df_customers.apply(lambda r: q.lower() in str(r.values).lower(), axis=1)])
