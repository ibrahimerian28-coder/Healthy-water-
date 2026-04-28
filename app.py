import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px

# --- 1. الدوال المركزية لربط الإكسيل ---
def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    url = "https://script.google.com/macros/s/AKfycbwyCuybxsP72RoNybypMcBQuGl8OJIDuwZBXcuw5Tx2KCgodVn751UEqkqLYsvTVn3oXg/exec"
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except:
        return False

st.set_page_config(page_title="Healthy Water Pro", layout="wide")

def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0.0
        return float(str(val).replace(',', '').strip())
    except:
        return 0.0

@st.cache_data(ttl=2)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df.fillna("")
    except:
        return pd.DataFrame()

def parse_dt(val):
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

# --- 2. تحميل وتجهيز البيانات ---
df_c = load_data("0")
df_m = load_data("2120582392")
df_inv = load_data("1767710106")
df_exp = load_data("288947510")

# تنظيف بيانات المخزن والاحتياجات لمنع الانهيار
if not df_inv.empty:
    df_inv['quantity'] = df_inv['quantity'].apply(to_num)
    df_inv['min_limit'] = df_inv['min_limit'].apply(to_num)
    df_inv['cost_price'] = df_inv.get('cost_price', 0)
    df_inv['cost_price'] = df_inv['cost_price'].apply(to_num)

# تجهيز سجلات الصيانة
if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

# --- 3. كلاس الـ PDF ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", x=110, y=8, w=80)
        except: 
            self.set_font('Arial','B',20)
            self.cell(0,10,'HEALTHY WATER',0,1,'C')
        self.ln(20)

def generate_pdf(row, history_df):
    pdf = HealthyPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Customer Report: {row['name']}", ln=True)
    # رسم الجدول مع كافة الخانات المطلوبة
    # (هنا يتم بناء الجدول برمجياً للـ PDF بشكل مبسط)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "صفحة الأرباح 📈", "إضافة عميل"])

# --- صفحة بيانات العملاء ---
if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("بحث بالاسم أو المنطقة...")
    filtered = df_c[df_c['name'].astype(str).str.contains(search) | df_c['area'].astype(str).str.contains(search)] if search else df_c
    
    for idx, r in filtered.iterrows():
        with st.expander(f"👤 {r['name']} - {r.get('area','')}"):
            c1, c2, c3 = st.columns([1,1,4])
            if c1.button("📝 تعديل العميل", key=f"ed_c_{idx}"): st.info("ميزة التعديل قيد التحديث")
            if c2.button("🗑️ حذف العميل", key=f"del_c_{idx}"): st.warning("هل أنت متأكد؟")
            
            st.write(f"**العنوان:** {r.get('adress','')} | **دورة الصيانة:** {r.get('maintenance_cycle', 3)} شهور")
            
            history = df_m[df_m['name'] == r['name']].sort_values(by='v_date_dt', ascending=False)
            full_cols = ['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared', 'other_item', 'amount', 'notes']
            
            # عرض جدول الصيانة بكافة الأعمدة (بما فيها المفقودة سابقاً)
            available_cols = [col for col in full_cols if col in history.columns]
            st.dataframe(history[available_cols], hide_index=True)
            
            st.download_button("📥 تحميل سجل PDF", data=b"", file_name=f"{r['name']}.pdf", key=f"pdf_{idx}")

# --- صفحة جدول المواعيد (الترحيل التلقائي) ---
elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    today = datetime.now().date()
    sched = []
    
    for _, r in df_c.iterrows():
        user_m = df_m[df_m['name'] == r['name']]
        if not user_m.empty:
            last_v = user_m.sort_values('v_date_dt').iloc[-1]
            cycle = int(to_num(r.get('maintenance_cycle', 3)))
            nxt = (last_v['v_date_dt'] + timedelta(days=cycle*30)).date()
            spec = parse_dt(last_v.get('special_date','')).date() if last_v.get('special_date','') else None
            
            final_d = spec if spec else nxt
            # الترحيل التلقائي: إذا فات الموعد ولم تسجل زيارة يظهر في "اليوم"
            if final_d < today: final_d = today 
            sched.append({'name': r['name'], 'date': final_d, 'area': r['area']})
            
    if sched:
        sdf = pd.DataFrame(sched)
        for i in range(7):
            curr = today + timedelta(days=i)
            st.subheader(f"{curr} - {('اليوم' if i==0 else '')}")
            res = sdf[sdf['date'] == curr]
            if not res.empty:
                for _, row in res.iterrows(): st.write(f"🔹 **{row['name']}** ({row['area']})")
            else: st.write(":grey[لا توجد مواعيد]")

# --- صفحة المخزن ---
elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    for idx, r in df_inv.iterrows():
        c1, c2, c3 = st.columns([3,2,1])
        c1.write(f"**{r['item_name']}** (سعر التكلفة: {r['cost_price']})")
        new_q = c2.number_input(f"الكمية لـ {r['item_name']}", value=int(r['quantity']), key=f"inv_{idx}")
        if c3.button("تحديث", key=f"upd_{idx}"):
            if execute_gsheet_action("update", "Inventory", [r['item_name'], new_q, r['min_limit'], r['cost_price']], idx+2):
                st.success("تم التحديث"); st.rerun()

# --- صفحة الاحتياجات ---
elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    try:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        st.table(shortage[['item_name', 'quantity', 'min_limit']])
    except Exception as e:
        st.error(f"خطأ في معالجة البيانات: {e}")

# --- صفحة تسجيل صيانة ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    main_parts = ['p1', 'p2', 'p3', 'membrane', 'post carbon', 'calcite', 'infrared']
    other_options = [n for n in df_inv['item_name'].tolist() if n.lower() not in main_parts]
    
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        date = st.date_input("تاريخ الزيارة")
        c1, c2, c3 = st.columns(3)
        s1 = c1.checkbox("P1"); s2 = c1.checkbox("P2"); s3 = c1.checkbox("P3")
        s4 = c2.checkbox("Membrane"); s5 = c2.checkbox("Post Carbon")
        s6 = c3.checkbox("Calcite"); s7 = c3.checkbox("Infrared")
        other = st.selectbox("قطع غيار أخرى (من المخزن)", ["لا يوجد"] + other_options)
        amt = st.number_input("المبلغ المحصل (Amount)", 0.0)
        note = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ الزيارة"):
            data = [name, str(date), s1, s2, s3, s4, s5, s6, s7, other, amt, note, ""]
            if execute_gsheet_action("append", "Maintenance", data):
                st.success("تم الحفظ بنجاح ✅"); st.cache_data.clear(); st.rerun()

# --- صفحة الأرباح (الكاملة والمعدلة) ---
elif menu == "صفحة الأرباح 📈":
    st.header("📈 تقرير الأرباح الصافية")

    def calc_visit_cost(row):
        visit_total_cost = 0.0
        parts_map = {
            'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 
            'membrane': 'membrane', 'post_carbon': 'post carbon', 
            'Calcite': 'calcite', 'infrared': 'infrared'
        }
        for col, inv_name in parts_map.items():
            if str(row.get(col, '')).lower() in ['true', '1', 'yes', '✅']:
                try:
                    price = to_num(df_inv[df_inv['item_name'].str.lower() == inv_name.lower()]['cost_price'].values[0])
                    visit_total_cost += price
                except: pass
        
        other_p = str(row.get('other_item', '')).strip()
        if other_p != "" and other_p != "لا يوجد":
            try:
                other_price = to_num(df_inv[df_inv['item_name'] == other_p]['cost_price'].values[0])
                visit_total_cost += other_price
            except: pass
        return visit_total_cost

    if not df_m.empty:
        df_m['visit_cost'] = df_m.apply(calc_visit_cost, axis=1)
        df_m['net_profit'] = df_m['amount_num'] - df_m['visit_cost']
        
        daily_profit = df_m.groupby(df_m['v_date_dt'].dt.date)['net_profit'].sum()
        today = datetime.now().date()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("صافي أرباح اليوم", f"{daily_profit.get(today, 0.0):,.1f} EGP")
        
        week_profit = df_m[df_m['v_date_dt'].dt.date >= (today - timedelta(days=7))]['net_profit'].sum()
        c_m2.metric("صافي أرباح الأسبوع", f"{week_profit:,.1f} EGP")
        
        month_profit = df_m[df_m['v_date_dt'].dt.month == today.month]['net_profit'].sum()
        c_m3.metric("صافي أرباح الشهر", f"{month_profit:,.1f} EGP")
        
        st.write("---")
        fig = px.line(daily_profit.reset_index(), x='v_date_dt', y='net_profit', 
                     title="مؤشر الأرباح اليومي (صافي)", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات صيانه لحساب الأرباح")

# --- إضافة عميل جديد ---
elif menu == "إضافة عميل":
    st.header("➕ إضافة عميل جديد")
    with st.form("new_c"):
        name = st.text_input("اسم العميل")
        area = st.text_input("المنطقة")
        address = st.text_input("العنوان")
        phone = st.text_input("الموبايل")
        cycle = st.number_input("دورة الصيانة (شهور)", 3)
        if st.form_submit_button("إضافة"):
            new_data = [name, phone, "", "", "", area, address, "", str(datetime.now().date()), cycle, "نشط"]
            if execute_gsheet_action("append", "Customers", new_data):
                st.success("تمت الإضافة"); st.rerun()
