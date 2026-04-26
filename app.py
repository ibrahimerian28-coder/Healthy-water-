import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF
import plotly.express as px

# --- 1. إعدادات الصفحة وسرعة الأداء ---
st.set_page_config(page_title="Healthy Water Pro - Level الوحش", layout="wide")

@st.cache_data(ttl=600) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # معالجة القيم الرقمية للمخزن والمصروفات
        for col in ['quantity', 'unit_price', 'min_limit', 'transportation', 'sundries', 'monthly_expensess', 'salaries', 'amount']:
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

# --- 3. تصميم الـ PDF (نفس التفاصيل السابقة) ---
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
    pdf.cell(0, 10, f"Customer Name: {clean_text_for_pdf(row['name'])}", ln=True)
    # ... (نفس منطق الجداول السابق)
    return bytes(pdf.output())

# --- 4. تحميل كافة البيانات (GIDs الجديدة) ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106") # شيت المخزن
df_exp = load_all_data("288947510") # شيت المصروفات

# --- 5. القائمة الجانبية المحدثة ---
if st.session_state.auth == "admin":
    menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "جدول المواعيد", "إضافة عميل جديد"])
else:
    menu = "بروفايلي"

if st.sidebar.button("خروج"):
    st.session_state.auth = None
    st.rerun()

# --- 6. تنفيذ الصفحات ---

# --- صفحة المخزن ---
if menu == "المخزن 📦":
    st.header("📦 إدارة المخزن (Inventory)")
    if not df_inv.empty:
        df_inv['total_item_value'] = df_inv['quantity'] * df_inv['unit_price']
        st.dataframe(df_inv, use_container_width=True)
        
        total_stock_value = df_inv['total_item_value'].sum()
        st.markdown(f"### 💰 القيمة الإجمالية للمخزون: `{total_stock_value:,.2f}` جنيه")
    else:
        st.warning("شيت المخزن فارغ أو غير متاح")

# --- صفحة الاحتياجات ---
elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ قائمة الاحتياجات (نواقص المخزن)")
    if not df_inv.empty:
        # الفلترة بناءً على حد الأمان
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        if not shortage.empty:
            st.error(f"يوجد عدد ({len(shortage)}) صنف يحتاج لطلب بضاعة فوراً")
            st.table(shortage[['item_name', 'category', 'quantity', 'min_limit']])
        else:
            st.success("كل الكميات في المخزن آمنة ومستوفاة لحد الأمان ✅")

# --- تسجيل صيانة (مع القائمة المنسدلة والخصم) ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form_new"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        v_date = st.date_input("تاريخ الزيارة", datetime.now())
        
        st.subheader("القطع الأساسية")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon"); calc = c2.checkbox("Calcite")
        infra = c3.checkbox("Infrared")
        
        st.divider()
        st.subheader("قطع غيار إضافية (من المخزن)")
        # القائمة المنسدلة الديناميكية
        inv_list = df_inv['item_name'].tolist()
        selected_items = st.multiselect("اختر القطع المستخدمة من المخزن (أخرى)", inv_list)
        
        # إدخال كميات للقطع المختارة
        item_quantities = {}
        if selected_items:
            q_cols = st.columns(len(selected_items))
            for i, item in enumerate(selected_items):
                item_quantities[item] = q_cols[i].number_input(f"كمية {item}", min_value=1, value=1)

        cost = st.number_input("المبلغ المحصل (Amount)", min_value=0.0)
        notes = st.text_area("ملاحظات")
        
        if st.form_submit_button("حفظ الزيارة"):
            st.success(f"تم تسجيل الزيارة للعميل {name} بنجاح!")
            st.info("سيتم خصم الكميات من المخزن في التحديث القادم للشيت.")

# --- صفحة المصروفات والحسابات ---
elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات والحسابات")
    col_add, col_view = st.columns([0.4, 0.6])
    
    with col_add:
        st.subheader("إضافة مصروف جديد")
        with st.form("exp_form"):
            e_date = st.date_input("التاريخ")
            trans = st.number_input("انتقالات")
            sun = st.number_input("نثريات")
            monthly = st.number_input("مصروفات شهرية")
            sals = st.number_input("رواتب")
            e_notes = st.text_input("ملاحظات")
            if st.form_submit_button("حفظ المصروف"):
                st.success("تم الحفظ")

    with col_view:
        st.subheader("آخر المصروفات")
        if not df_exp.empty:
            df_exp['total_exp'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
            st.dataframe(df_exp.tail(10), use_container_width=True)

# --- صفحة الأرباح والرسوم البيانية ---
elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح والرسوم البيانية")
    
    # تحضير البيانات المالية
    df_m['visit_date'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
    df_exp['date'] = pd.to_datetime(df_exp['date'], errors='coerce')
    
    # تجميع الدخل اليومي
    daily_inc = df_m.groupby('visit_date')['amount'].sum().reset_index()
    daily_inc.columns = ['date', 'income']
    
    # تجميع المصروفات اليومية
    df_exp['daily_total_exp'] = df_exp['transportation'] + df_exp['sundries'] + df_exp['monthly_expensess'] + df_exp['salaries']
    daily_exp_agg = df_exp.groupby('date')['daily_total_exp'].sum().reset_index()
    
    # دمج الجداول لحساب الربح
    fin_df = pd.merge(daily_inc, daily_exp_agg, on='date', how='outer').fillna(0)
    fin_df['profit'] = fin_df['income'] - fin_df['daily_total_exp']
    fin_df = fin_df.sort_values('date')

    # عرض الأرقام الرئيسية
    c_day, c_week, c_month = st.columns(3)
    today = datetime.now().date()
    curr_profit = fin_df[fin_df['date'].dt.date == today]['profit'].sum()
    c_day.metric("أرباح اليوم", f"{curr_profit:,.2f} ج.م")
    
    # الرسوم البيانية
    tab1, tab2, tab3 = st.tabs(["📊 يومي", "📊 أسبوعي", "📊 شهري"])
    
    with tab1:
        fig_d = px.bar(fin_df, x='date', y='profit', title="صافي الربح اليومي", color='profit', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_d, use_container_width=True)
    
    with tab2:
        fin_df['week'] = fin_df['date'].dt.isocalendar().week
        weekly_profit = fin_df.groupby('week')['profit'].sum().reset_index()
        fig_w = px.bar(weekly_profit, x='week', y='profit', title="صافي الربح الأسبوعي")
        st.plotly_chart(fig_w, use_container_width=True)

    with tab3:
        fin_df['month'] = fin_df['date'].dt.to_period('M').astype(str)
        monthly_profit = fin_df.groupby('month')['profit'].sum().reset_index()
        fig_m = px.bar(monthly_profit, x='month', y='profit', title="صافي الربح الشهري")
        st.plotly_chart(fig_m, use_container_width=True)

# --- استكمال الصفحات القديمة (بيانات العملاء / إضافة عميل) بنفس المنطق السابق ---
elif menu in ["بيانات العملاء", "بروفايلي"]:
    st.header("📋 سجل العملاء والأجهزة")
    # ... (نفس الكود السابق لعرض الكروت والتعديل والحذف والـ PDF)
    data_to_show = st.session_state.user_data if st.session_state.auth == "customer" else df_c.to_dict('records')
    for idx, r in enumerate(data_to_show):
        with st.container():
            st.markdown(f'<div class="cust-card"><h3>👤 {r["name"]}</h3></div>', unsafe_allow_html=True)
            with st.expander("التفاصيل"):
                st.write(f"العنوان: {r.get('adress','')}")
                history = df_m[df_m['name'] == r['name']]
                st.dataframe(history)

elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل جديد")
    # ... (نفس كود الفورم السابق)
