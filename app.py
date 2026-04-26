import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة ---
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

# --- 2. نظام الألوان (شريط جانبي فقط) ---
def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080" # رمادي
    if not next_date or pd.isnull(next_date): return "#f9f9f9"
    today = datetime.now().date()
    diff = (next_date - today).days
    if diff > 7: return "#28a745" # أخضر
    elif 0 <= diff <= 7: return "#ffc107" # أصفر
    elif -7 <= diff < 0: return "#dc3545" # أحمر
    else: return "#8b0000" # أحمر غامق

# --- 3. تصميم الـ PDF (حل مشكلة الـ Unicode) ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 33) 
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
            # حل مشكلة الصورة: نستخدم حرف Y و N في الـ PDF بدل علامة الصح لتجنب الـ Error
            status = "Y" if format_to_check(m.get(f,'')) == "✓" else "-"
            pdf.cell(31, 10, status, 1, 0, 'C')
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C')
        pdf.ln()
    return bytes(pdf.output())

# --- 4. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

# --- 5. نظام الدخول والقائمة ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("💧 Healthy Water")
    pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
    if st.sidebar.button("دخول"):
        if pwd == "HgM18082019$&)": 
            st.session_state.auth = "admin"
            st.rerun()
    st.stop()

menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "إضافة عميل جديد"])

# --- 6. الصفحات ---

if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    df_m['v_date_dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    last_v_map = df_m.sort_values('v_date_dt').groupby('name').last().to_dict('index')

    for idx, r in df_c.iterrows():
        last_v = last_v_map.get(r['name'], {})
        next_d = None
        if last_v:
            if pd.notnull(last_v.get('special_date')) and last_v.get('special_date') != "": 
                next_d = pd.to_datetime(last_v['special_date']).date()
            else: next_d = (last_v['v_date_dt'] + timedelta(days=int(r.get('maintenance_cycle',3))*30)).date()
        
        side_color = get_status_color(next_d, r.get('status', ''))
        
        # تعديل الكارت: شريط جانبي فقط ملون (ملاحظة ثانياً)
        st.markdown(f"""
            <div style="padding:10px; border-radius:5px; margin-bottom:10px; background-color:#ffffff; border-right:12px solid {side_color}; border-left:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <h4 style="margin:0; color:#333;">👤 {r['name']}</h4>
                <p style="margin:0; font-size:13px; color:#666;">📍 {r.get('area','')} | 📞 {r.get('phone','')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("التفاصيل والصيانات"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                    num = str(r.get(p,'')).strip()
                    if num and num != "nan" and num != "":
                        st.markdown(f"📞 {num}: [اتصال](tel:{num}) | [واتساب](https://wa.me/2{num})")
            with c2:
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    disp_h = history[['visit_date','P1','P2','P3','membrane','amount']].tail(5).copy()
                    for col in ['P1','P2','P3','membrane']: disp_h[col] = disp_h[col].apply(format_to_check)
                    st.table(disp_h)
                    st.download_button("📥 تحميل PDF", generate_safe_pdf(r, df_m), f"{r['name']}.pdf", key=f"pdf_{idx}")

elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    if not df_inv.empty:
        df_inv['total_item_value'] = df_inv['quantity'] * df_inv['unit_price']
        st.dataframe(df_inv, use_container_width=True)
        st.metric("إجمالي قيمة المخزن", f"{df_inv['total_item_value'].sum():,.2f} ج.م")
    else: st.warning("لا توجد بيانات في شيت المخزن")

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    if not df_inv.empty:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        st.table(shortage[['item_name', 'quantity', 'min_limit']]) if not shortage.empty else st.success("المخزن مكتمل ✅")

elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات")
    if not df_exp.empty:
        df_exp['total_exp'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
        st.dataframe(df_exp, use_container_width=True)
    else: st.info("سجل المصروفات فارغ")

elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح")
    if not df_m.empty and not df_exp.empty:
        df_m['visit_date'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
        df_exp['date'] = pd.to_datetime(df_exp['date'], errors='coerce')
        inc = df_m.groupby('visit_date')['amount'].sum().reset_index().rename(columns={'visit_date':'date', 'amount':'income'})
        exp = df_exp.groupby('date')[['transportation','sundries','monthly_expensess','salaries']].sum().sum(axis=1).reset_index(name='expense')
        fin = pd.merge(inc, exp, on='date', how='outer').fillna(0)
        fin['profit'] = fin['income'] - fin['expense']
        st.dataframe(fin.sort_values('date', ascending=False))
        if HAS_PLOTLY: st.plotly_chart(px.line(fin, x='date', y='profit', title="صافي الربح"))

elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        col_d1, col_d2 = st.columns(2)
        v_date = col_d1.date_input("تاريخ اليوم", datetime.now())
        sp_date = col_d2.date_input("موعد استثنائي القادم (اختياري)", value=None)
        st.multiselect("القطع المستخدمة", df_inv['item_name'].tolist())
        st.number_input("المبلغ المحصل", min_value=0.0)
        if st.form_submit_button("حفظ"): st.success("تم!")

elif menu == "إضافة عميل جديد":
    st.header("➕ عميل جديد")
    with st.form("add_c"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("الاسم الكامل")
            st.text_input("الموبايل (phone)")
            st.text_input("موبايل 2 (phone_1)")
            st.text_input("موبايل 3 (phone_2)")
            st.text_input("المنطقة (area)")
        with c2:
            st.text_input("العنوان (adress)")
            st.text_input("اللوكيشن (location)")
            st.date_input("تاريخ التركيب")
            st.selectbox("الحالة", ["نشط", "راكد"])
            st.number_input("الدورة (شهور)", 3)
        st.form_submit_button("إضافة")

elif menu == "جدول المواعيد":
    st.header("📅 المواعيد القادمة")
    st.info("سيتم عرض المواعيد هنا بناءً على حسابات الدورة والزيارات الاستثنائية.")
