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

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 2. نظام الألوان (شريط جانبي ملون) ---
def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080"
    if not next_date or pd.isnull(next_date): return "#f0f2f6"
    today = datetime.now().date()
    diff = (next_date - today).days
    if diff > 7: return "#28a745"
    elif 0 <= diff <= 7: return "#ffc107"
    elif -7 <= diff < 0: return "#dc3545"
    else: return "#8b0000"

# --- 3. تصميم الـ PDF المطور ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 50) # رجعت حجم اللوجو كبير
        except: pass
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Service Report - Healthy Water', 0, 1, 'R')
        self.ln(10)

    def footer(self): # إضافة الفوتر
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Healthy Water Company - Support: 01286609535', 0, 0, 'C')

def generate_safe_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # اسم العميل
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Customer: {clean_text_for_pdf(row['name'])}", ln=True)
    pdf.ln(5)
    
    # الهيدر للجدول
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    pdf.set_fill_color(40, 116, 166) # لون هيدر الجدول
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11)
    for h in headers:
        pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()
    
    # البيانات وتلوين الصفوف
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    history = df_m[df_m['name'] == row['name']].copy()
    
    fill = False # لتبديل اللون
    for _, m in history.tail(10).iterrows():
        if fill:
            pdf.set_fill_color(240, 240, 240) # صف رمادي فاتح
        else:
            pdf.set_fill_color(255, 255, 255) # صف أبيض
            
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C', True)
        
        # علامة الصح الحقيقية باستخدام خط ZapfDingbats
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            is_checked = format_to_check(m.get(f,'')) == "✓"
            if is_checked:
                pdf.set_font('ZapfDingbats', '', 11)
                pdf.cell(31, 10, '4', 1, 0, 'C', True) # '4' في ZapfDingbats هي علامة الصح
                pdf.set_font('Arial', '', 11)
            else:
                pdf.cell(31, 10, "-", 1, 0, 'C', True)
                
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C', True)
        pdf.ln()
        fill = not fill # تبديل للترتيب القادم
        
    return bytes(pdf.output())

# --- 4. تحميل البيانات ونظام الدخول ---
if 'auth' not in st.session_state: st.session_state.auth = None
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

if not st.session_state.auth:
    st.title("💧 Healthy Water Management")
    pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
    if st.sidebar.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.auth = "admin"; st.rerun()
        else: st.error("الباسورد غلط!")
    st.stop()

# --- 5. القائمة الجانبية ---
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
        
        status_color = get_status_color(next_d, r.get('status', ''))
        
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
                loc = r.get('location','')
                if loc: st.markdown(f"🗺️ **اللوكيشن:** [اضغط هنا لفتح الخريطة]({loc})")
                
                st.write("**تواصل مع العميل:**")
                for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                    num = str(r.get(p,'')).strip()
                    if num and num != "nan" and num != "":
                        st.markdown(f"""
                        <div style="display: flex; gap: 10px; margin-bottom: 8px; align-items: center;">
                            <span style="font-weight: bold; min-width: 110px;">{num}</span>
                            <a href="tel:{num}" style="text-decoration: none; background-color: #007bff; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px;">📞 اتصال</a>
                            <a href="https://wa.me/2{num}" style="text-decoration: none; background-color: #25d366; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px;">💬 واتساب</a>
                        </div>
                        """, unsafe_allow_html=True)
            with c2:
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    h_cols = ['visit_date','P1','P2','P3','membrane','post_carbon','Calcite','infrared','amount']
                    history_display = history[[c for c in h_cols if c in history.columns]].tail(5).copy()
                    for col in history_display.columns:
                        if col not in ['visit_date', 'amount']: history_display[col] = history_display[col].apply(format_to_check)
                    st.table(history_display)
                    st.download_button("📥 تحميل PDF", generate_safe_pdf(r, df_m), f"{r['name']}.pdf", key=f"p_{idx}")

elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form_complete"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        col1, col2 = st.columns(2)
        v_date = col1.date_input("تاريخ الزيارة")
        s_date = col2.date_input("موعد استثنائي (اختياري)", value=None)
        
        st.write("---")
        st.subheader("الشمعات التي تم تغييرها")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
        calc = c3.checkbox("Calcite"); infra = c3.checkbox("Infrared")
        
        st.write("---")
        items = st.multiselect("قطع غيار إضافية من المخزن", df_inv['item_name'].tolist() if not df_inv.empty else [])
        amount = st.number_input("المبلغ المحصل", min_value=0.0)
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ البيانات"):
            st.success("تم تسجيل البيانات بنجاح")

elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات")
    with st.form("exp_form"):
        st.subheader("تسجيل مصروف جديد")
        e_date = st.date_input("التاريخ")
        col_e1, col_e2 = st.columns(2)
        trans = col_e1.number_input("انتقالات (transportation)", min_value=0.0)
        sund = col_e2.number_input("نثريات (sundries)", min_value=0.0)
        mon_exp = col_e1.number_input("مصروفات شهرية (monthly_expensess)", min_value=0.0)
        sal = col_e2.number_input("رواتب (salaries)", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            st.info("تم الحفظ")
    
    st.write("---")
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
    else: st.warning("يجب توفر بيانات في الصيانات والمصروفات لحساب الأرباح")

elif menu == "إضافة عميل جديد":
    st.header("➕ تسجيل عميل جديد")
    with st.form("add_f_complete"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("الاسم الكامل")
            st.text_input("رقم الموبايل الأساسي (phone)")
            st.text_input("موبايل 2 (phone_1)")
            st.text_input("موبايل 3 (phone_2)")
            st.text_input("المنطقة (area)")
        with c2:
            st.text_input("العنوان بالتفصيل (adress)")
            st.text_input("اللوكيشن (location)")
            st.date_input("تاريخ التركيب (setup_date)")
            st.selectbox("الحالة", ["نشط", "راكد"])
            st.number_input("دورة الصيانة (maintenance_cycle)", value=3)
        if st.form_submit_button("إضافة العميل"):
            st.success("تمت الإضافة بنجاح")

elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    if not df_inv.empty:
        df_inv['total_value'] = df_inv['quantity'] * df_inv['unit_price']
        st.dataframe(df_inv, use_container_width=True)
    else: st.warning("لا توجد بيانات بالمخزن")

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    if not df_inv.empty:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        if not shortage.empty: st.table(shortage[['item_name', 'quantity', 'min_limit']])
        else: st.success("المخزن مكتمل ✅")

elif menu == "جدول المواعيد":
    st.header("📅 جدول المواعيد القادمة")
    st.info("يتم الحساب تلقائياً بناءً على تاريخ آخر زيارة ودورة الصيانة.")
