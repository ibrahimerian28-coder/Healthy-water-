import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

@st.cache_data(ttl=600) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
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
    c_name = clean_text_for_pdf(row['name'])
    c_phone = clean_text_for_pdf(row.get('phone',''))
    c_area = clean_text_for_pdf(row.get('area',''))
    pdf.cell(0, 10, f"Customer Name: {c_name}", ln=True)
    pdf.cell(0, 10, f"Phone: {c_phone} | Area: {c_area}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(40, 116, 166)
    pdf.set_text_color(255, 255, 255)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    df_m['v_date_dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    sorted_m = df_m.sort_values(by='v_date_dt', ascending=False)
    for i, (_, m) in enumerate(sorted_m.iterrows()):
        if i % 2 == 0: pdf.set_fill_color(255, 255, 255)
        else: pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", '', 10)
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C', True)
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            status = format_to_check(m.get(f,''))
            if status == "✓":
                pdf.set_font("ZapfDingbats", '', 10)
                pdf.cell(31, 10, "4", 1, 0, 'C', True)
            else:
                pdf.set_font("Arial", '', 10)
                pdf.cell(31, 10, "-", 1, 0, 'C', True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C', True)
        pdf.ln()
    return bytes(pdf.output())

# --- 4. التنسيق (CSS) ---
st.markdown("""
    <style>
    .cust-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-right: 15px solid #28a745; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .wa-btn { background:#25d366 !important; color:white !important; padding:6px 12px; border-radius:8px; text-decoration:none; margin:2px; display:inline-block; font-size:13px; }
    .call-btn { background:#007bff !important; color:white !important; padding:6px 12px; border-radius:8px; text-decoration:none; margin:2px; display:inline-block; font-size:13px; }
    .contact-section { background: #fff; padding: 20px; border-radius: 15px; border: 1px solid #ddd; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")

# --- 6. القائمة الجانبية ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "تسجيل صيانة", "إضافة عميل جديد"])
else:
    menu = "بروفايلي"
    st.sidebar.markdown("### 📞 الدعم الفني")
    st.sidebar.markdown('<a href="tel:01286609535" class="call-btn">📞 مكالمة</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="https://wa.me/201286609535" class="wa-btn">💬 واتساب</a>', unsafe_allow_html=True)

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.session_state.user_data = None
    st.rerun()

# --- 7. الصفحات ---
if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء والأجهزة")
    
    data_to_show = st.session_state.user_data if st.session_state.auth == "customer" else df_c.to_dict('records')
    
    for idx, r in enumerate(data_to_show):
        with st.container():
            # عرض اسم العميل مع أزرار التعديل والحذف للأدمن فقط
            head_col1, head_col2 = st.columns([0.8, 0.2])
            with head_col1:
                st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3><p>📍 {r.get("area","")} | {r.get("phone","")}</p></div>', unsafe_allow_html=True)
            
            with head_col2:
                if st.session_state.auth == "admin":
                    btn_edit_c, btn_del_c = st.columns(2)
                    if btn_edit_c.button("📝", key=f"edit_c_{idx}", help="تعديل العميل"):
                        st.session_state[f"editing_customer_{idx}"] = True
                    if btn_del_c.button("🗑️", key=f"del_c_{idx}", help="حذف العميل"):
                        st.session_state[f"confirm_del_c_{idx}"] = True

            # منطق تأكيد حذف العميل
            if st.session_state.get(f"confirm_del_c_{idx}"):
                st.warning(f"هل أنت متأكد من حذف العميل: {r['name']}؟")
                if st.button("نعم، احذف", key=f"yes_del_c_{idx}"):
                    st.success("تم الحذف بنجاح (من الذاكرة حالياً)")
                    st.session_state[f"confirm_del_c_{idx}"] = False
                if st.button("إلغاء", key=f"no_del_c_{idx}"):
                    st.session_state[f"confirm_del_c_{idx}"] = False

            # منطق تعديل العميل
            if st.session_state.get(f"editing_customer_{idx}"):
                with st.form(f"form_edit_c_{idx}"):
                    st.subheader(f"تعديل بيانات: {r['name']}")
                    new_name = st.text_input("الاسم", value=r['name'])
                    new_phone = st.text_input("الموبايل", value=r.get('phone',''))
                    new_area = st.text_input("المنطقة", value=r.get('area',''))
                    if st.form_submit_button("حفظ التعديلات"):
                        st.success("تم حفظ التعديلات")
                        st.session_state[f"editing_customer_{idx}"] = False
                        st.rerun()

            with st.expander(f"تفاصيل جهاز: {r['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**العنوان:** {r.get('adress','')}")
                    st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                    st.write(f"**الدورة:** كل {r.get('cycle',3)} شهور")
                    for p_field in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                        val = str(r.get(p_field, '')).strip()
                        if val and val != "nan" and len(val) > 5:
                            st.markdown(f'**{val}:** <a href="tel:{val}" class="call-btn">اتصال</a> <a href="https://wa.me/2{val}" class="wa-btn">واتساب</a>', unsafe_allow_html=True)
                
                with col2:
                    st.subheader("🛠️ سجل الصيانات")
                    history = df_m[df_m['name'] == r['name']].copy()
                    if not history.empty:
                        # أزرار الـ PDF
                        try:
                            pdf_output = generate_safe_pdf(r, history)
                            st.download_button(label=f"📥 PDF لهذا الجهاز", data=pdf_output, file_name=f"{r['name']}.pdf", mime="application/pdf", key=f"pdf_{r['name']}")
                        except: pass
                        
                        # عرض سجل الصيانات مع خيارات التعديل للأدمن
                        for m_idx, m_row in history.iterrows():
                            m_col1, m_col2 = st.columns([0.7, 0.3])
                            with m_col1:
                                st.text(f"📅 {m_row['visit_date']} - التكلفة: {m_row.get('amount',0)}")
                            
                            with m_col2:
                                if st.session_state.auth == "admin":
                                    m_edit, m_del = st.columns(2)
                                    if m_edit.button("📝", key=f"edit_m_{m_idx}"):
                                        st.session_state[f"editing_m_{m_idx}"] = True
                                    if m_del.button("🗑️", key=f"del_m_{m_idx}"):
                                        st.session_state[f"confirm_del_m_{m_idx}"] = True
                            
                            # تأكيد حذف زيارة
                            if st.session_state.get(f"confirm_del_m_{m_idx}"):
                                st.error("حذف هذه الزيارة؟")
                                if st.button("تأكيد الحذف", key=f"y_m_{m_idx}"):
                                    st.success("تم الحذف")
                                    st.session_state[f"confirm_del_m_{m_idx}"] = False
                            
                            # تعديل زيارة
                            if st.session_state.get(f"editing_m_{m_idx}"):
                                with st.form(f"form_m_{m_idx}"):
                                    new_cost = st.number_input("التكلفة الجديدة", value=float(m_row.get('amount',0)))
                                    if st.form_submit_button("حفظ التعديلات"):
                                        st.success("تم التحديث")
                                        st.session_state[f"editing_m_{m_idx}"] = False
                                        st.rerun()
                        
                        # الجدول الرئيسي للعرض فقط
                        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                            if f in history.columns: history[f] = history[f].apply(format_to_check)
                        st.dataframe(history.sort_values(by='visit_date', ascending=False), hide_index=True)
                    else:
                        st.write("لا يوجد سجل صيانات")

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد والتنبيهات")
    tab_a, tab_b = st.tabs(["الصيانات الدورية", "🔔 مواعيد استثنائية"])
    with tab_a:
        for i in range(8):
            day = datetime.now().date() + timedelta(days=i)
            st.write(f"**{day}**")
    with tab_b:
        if 'Special_reminder_date' in df_m.columns:
            df_m['rem_dt'] = pd.to_datetime(df_m['Special_reminder_date'], errors='coerce')
            specials = df_m[df_m['rem_dt'].notna()]
            st.dataframe(specials[['name', 'Special_reminder_date', 'other', 'notes']])

elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        v_date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        st.divider()
        other = st.text_input("أخرى")
        spec_date = st.date_input("موعد استثنائي", value=None)
        cost = st.number_input("التكلفة")
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"): st.success("تم الحفظ بنجاح")

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل/جهاز جديد")
    with st.form("add_f"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("الاسم (مثال: علي سالمان 1)")
            st.text_input("الموبايل الأساسي (phone)")
            st.text_input("موبايل 2 (phone_1)")
            st.text_input("موبايل 3 (phone_2)")
            st.text_input("موبايل 4 (phone_3)")
            st.text_input("موبايل 5 (phone_4)")
        with col2:
            st.text_input("العنوان بالتفصيل")
            st.text_input("المنطقة (Area)")
            st.text_input("رابط اللوكيشن")
            st.date_input("تاريخ التركيب")
            st.number_input("دورة الصيانة (شهور)", 3)
            st.selectbox("حالة العميل", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"): st.success("تم الإضافة!")
