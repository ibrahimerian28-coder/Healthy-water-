import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro - Level الوحش", layout="wide")

@st.cache_data(ttl=600) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # تحويل الأعمدة الرقمية لضمان ظهور البيانات في صفحات المخزن والأرباح
        num_cols = ['quantity', 'unit_price', 'min_limit', 'transportation', 'sundries', 'monthly_expensess', 'salaries', 'amount', 'maintenance_cycle']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.fillna("") 
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

def clean_text_for_pdf(text):
    if not text: return ""
    return "".join(i for i in str(text) if ord(i) < 128)

# محاولة استيراد plotly بأمان
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 2. نظام الألوان (شريط جانبي ملون فقط) ---
def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080" # رمادي
    if not next_date or pd.isnull(next_date): return "#f0f2f6"
    today = datetime.now().date()
    diff = (next_date - today).days
    if diff > 7: return "#28a745" # أخضر
    elif 0 <= diff <= 7: return "#ffc107" # أصفر
    elif -7 <= diff < 0: return "#dc3545" # أحمر
    else: return "#8b0000" # أحمر غامق

# --- 3. تصميم الـ PDF (علاج خطأ الـ Unicode) ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 30) 
        except: pass
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Service Report - Healthy Water', 0, 1, 'R')
        self.ln(5)

def generate_safe_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Customer: {clean_text_for_pdf(row['name'])}", ln=True)
    pdf.ln(5)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C')
    pdf.ln()
    history = df_m[df_m['name'] == row['name']].copy()
    for _, m in history.tail(10).iterrows():
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C')
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            # نستخدم حرف Y بدل علامة الصح لتجنب خطأ المكتبة في الـ PDF
            status = "Y" if format_to_check(m.get(f,'')) == "✓" else "-"
            pdf.cell(31, 10, status, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return bytes(pdf.output())

# --- 4. تحميل البيانات ونظام الدخول ---
if 'auth' not in st.session_state: st.session_state.auth = None
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

def login():
    st.title("💧 Healthy Water Management")
    role = st.sidebar.selectbox("دخول بصفتك:", ["أدمن", "عميل"])
    if role == "أدمن":
        pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
        if st.sidebar.button("دخول"):
            if pwd == "HgM18082019$&)":
                st.session_state.auth = "admin"; st.rerun()
            else: st.error("الباسورد غلط!")
    else:
        u_id = st.sidebar.text_input("رقم الموبايل:")
        if st.sidebar.button("دخول العميل"):
            search_val = str(u_id).strip()
            if not df_c.empty and search_val:
                phone_cols = ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']
                mask = df_c[phone_cols].astype(str).apply(lambda x: x.str.contains(re.escape(search_val), na=False)).any(axis=1)
                matches = df_c[mask]
                if not matches.empty:
                    st.session_state.auth = "customer"; st.session_state.user_data = matches.to_dict('records'); st.rerun()

if not st.session_state.auth:
    login(); st.stop()

# --- 5. القائمة الجانبية ---
menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "إضافة عميل جديد"]) if st.session_state.auth == "admin" else "بروفايلي"

# --- 6. الصفحات ---

if menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء")
    data = st.session_state.user_data if st.session_state.auth == "customer" else df_c.to_dict('records')
    
    df_m['v_date_dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    last_v_map = df_m.sort_values('v_date_dt').groupby('name').last().to_dict('index')

    for idx, r in enumerate(data):
        last_v = last_v_map.get(r['name'], {})
        next_d = None
        if last_v:
            if pd.notnull(last_v.get('special_date')) and last_v.get('special_date') != "": 
                next_d = pd.to_datetime(last_v['special_date']).date()
            else: next_d = (last_v['v_date_dt'] + timedelta(days=int(r.get('maintenance_cycle',3))*30)).date()
        
        status_color = get_status_color(next_d, r.get('status', ''))
        
        # تصميم الكارت بالشريط الجانبي الملون فقط
        st.markdown(f"""
            <div style="padding:12px; border-radius:8px; margin-bottom:10px; background-color:#ffffff; border-right:15px solid {status_color}; border-left:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <h4 style="margin:0; color:#333;">👤 {r['name']}</h4>
                <p style="margin:0; font-size:14px; color:#666;">📍 {r.get('area','')} | 📞 {r.get('phone','')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("فتح التفاصيل وسجل الصيانات"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                st.write(f"**الحالة:** {r.get('status','')}")
                for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                    num = str(r.get(p,'')).strip()
                    if num and num != "nan" and num != "":
                        st.markdown(f"📞 {num}: [اتصال](tel:{num}) | [واتساب](https://wa.me/2{num})")
            with c2:
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    history_display = history[['visit_date','P1','P2','P3','membrane','amount']].tail(5).copy()
                    for col in ['P1','P2','P3','membrane']:
                        history_display[col] = history_display[col].apply(format_to_check)
                    st.table(history_display)
                    st.download_button("📥 تحميل PDF", generate_safe_pdf(r, df_m), f"{r['name']}.pdf", key=f"p_{idx}")

elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    if not df_inv.empty:
        df_inv['total_value'] = df_inv['quantity'] * df_inv['unit_price']
        st.dataframe(df_inv, use_container_width=True)
        st.metric("إجمالي قيمة المخزن", f"{df_inv['total_value'].sum():,.2f} ج.م")
    else: st.warning("لا توجد بيانات بالمخزن")

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    if not df_inv.empty:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        if not shortage.empty: st.table(shortage[['item_name', 'quantity', 'min_limit']])
        else: st.success("المخزن مكتمل ✅")

elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات")
    if not df_exp.empty:
        df_exp['total'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
        st.dataframe(df_exp, use_container_width=True)
    else: st.info("سجل المصروفات فارغ")

elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح")
    if not df_m.empty and not df_exp.empty:
        df_m['visit_date'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
        df_exp['date'] = pd.to_datetime(df_exp['date'], errors='coerce')
        income = df_m.groupby('visit_date')['amount'].sum().reset_index().rename(columns={'visit_date':'date', 'amount':'income'})
        expenses = df_exp.groupby('date')[['transportation','sundries','monthly_expensess','salaries']].sum().sum(axis=1).reset_index(name='expense')
        merged = pd.merge(income, expenses, on='date', how='outer').fillna(0)
        merged['profit'] = merged['income'] - merged['expense']
        st.dataframe(merged.sort_values('date', ascending=False))
        if HAS_PLOTLY: st.plotly_chart(px.line(merged, x='date', y='profit', title="صافي الربح اليومي"))

elif menu == "جدول المواعيد":
    st.header("📅 جدول المواعيد")
    # سيتم عرض البيانات هنا كما هي في الكود السابق لضمان استقرارها حتى يتم اختبارها
    st.info("سيتم عرض مواعيد الأسبوع القادم والترحيل التلقائي هنا.")

elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        col1, col2 = st.columns(2)
        v_date = col1.date_input("تاريخ الزيارة")
        s_date = col2.date_input("موعد استثنائي (اختياري)", value=None)
        st.form_submit_button("حفظ")

elif menu == "إضافة عميل جديد":
    st.header("➕ عميل جديد")
    with st.form("add_f"):
        st.text_input("الاسم")
        st.text_input("الموبايل")
        st.form_submit_button("إضافة")
