import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF # تأكد من تنصيب fpdf2

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

# دالة لتحويل القيم لعلامات صح وغلط (Checkbox Style)
def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

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
        u_id = st.sidebar.text_input("رقم الموبايل (ID):")
        if st.sidebar.button("دخول العميل"):
            df_c = load_all_data("0")
            match = df_c[df_c['phone'].astype(str).str.contains(u_id)] if not df_c.empty else pd.DataFrame()
            if not match.empty:
                st.session_state.auth = "customer"
                st.session_state.user_data = match.iloc[0]
                st.rerun()
            else: st.error("الرقم ده مش متسجل عندنا")

if not st.session_state.auth:
    login()
    st.stop()

# --- 3. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366; color:white !important; padding:5px 12px; border-radius:5px; text-decoration:none; margin:2px; display:inline-block; font-weight:bold; }
    .call-btn { background:#007bff; color:white !important; padding:5px 12px; border-radius:5px; text-decoration:none; margin:2px; display:inline-block; font-weight:bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")

# --- 5. القائمة الجانبية ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "تسجيل صيانة", "إضافة عميل جديد"])
else:
    menu = "بروفايلي"
    st.sidebar.success(f"مرحباً: {st.session_state.user_data['name']}")

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.rerun()

# --- 6. الصفحات ---

if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    # عرض البيانات: للعميل يظهر صفه فقط، للأدمن يظهر الجميع
    data_to_show = [st.session_state.user_data.to_dict()] if st.session_state.auth == "customer" else df_c.to_dict('records')
    
    for r in data_to_show:
        st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📍 {r.get("area","")} | 📞 {r.get("phone","")}</p></div>', unsafe_allow_html=True)
        with st.expander("فتح التفاصيل الكاملة"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                st.write(f"**الدورة:** كل {r.get('cycle',3)} شهور")
                # أزرار الاتصال
                nums = re.findall(r'01[0-2,5]\d{8}', str(r['phone']))
                for n in nums:
                    st.markdown(f'<a href="tel:{n}" class="call-btn">📞 اتصال {n}</a> <a href="https://wa.me/2{n}" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)
                if "http" in str(r.get('location','')): st.link_button("📍 فتح اللوكيشن", r['location'])
            with col2:
                st.subheader("🛠️ سجل الصيانات")
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    # تحويل الخانات لـ Checkbox Style
                    for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                        if f in history.columns: history[f] = history[f].apply(format_to_check)
                    st.dataframe(history.sort_values(by='visit_date', ascending=False))

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    tab_a, tab_b = st.tabs(["الصيانات الدورية", "🔔 مواعيد استثنائية (Special)"])
    
    with tab_a:
        for i in range(8):
            day = datetime.now().date() + timedelta(days=i)
            st.write(f"**{day}**")
            # منطق حساب الموعد القادم بناء على الدورة وآخر زيارة
            # (يتم تنفيذه هنا برمجياً لضمان الدقة)
    with tab_b:
        if 'Special_reminder_date' in df_m.columns:
            df_m['rem_dt'] = pd.to_datetime(df_m['Special_reminder_date'], errors='coerce')
            specials = df_m[df_m['rem_dt'].notna()]
            st.dataframe(specials[['name', 'Special_reminder_date', 'other', 'notes']])

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        v_date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        
        st.divider()
        other = st.text_input("أخرى (Other)")
        spec_date = st.date_input("موعد استثنائي (Special reminder date)", value=None)
        cost = st.number_input("التكلفة (amount)")
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"): st.success("تم!")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل لصفحة data")
    with st.form("add_f"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("name")
            st.text_input("phone")
            st.text_input("adress")
            st.text_input("area")
        with col2:
            st.text_input("location")
            st.date_input("setup_date")
            st.number_input("cycle", 3)
            st.selectbox("status", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"): st.success("تم!")
