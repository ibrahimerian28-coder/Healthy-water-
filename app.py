\import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px

# --- 1. الدوال المركزية وتأمين البيانات ---
def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    url = "https://script.google.com/macros/s/AKfycbwyCuybxsP72RoNybypMcBQuGl8OJIDuwZBXcuw5Tx2KCgodVn751UEqkqLYsvTVn3oXg/exec"
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except: return False

st.set_page_config(page_title="Healthy Water Pro", layout="wide")

def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0.0
        return float(str(val).replace(',', '').strip())
    except: return 0.0

@st.cache_data(ttl=2)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df.fillna("")
    except: return pd.DataFrame()

def parse_dt(val):
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

# --- 2. تحميل وتجهيز البيانات (المخزن، العملاء، الصيانة) ---
df_c = load_data("0")
df_m = load_data("2120582392")
df_inv = load_data("1767710106")
df_exp = load_data("288947510")

# تنظيف بيانات المخزن فوراً لمنع الـ ValueError
if not df_inv.empty:
    df_inv['quantity'] = df_inv['quantity'].apply(to_num)
    df_inv['min_limit'] = df_inv['min_limit'].apply(to_num)
    df_inv['cost_price'] = df_inv.get('cost_price', 0) # تأكد من وجود عمود سعر التكلفة
    df_inv['cost_price'] = df_inv['cost_price'].apply(to_num)

# تجهيز سجلات الصيانة
if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

# --- 3. كلاس الـ PDF ---
class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", x=110, y=8, w=80)
        except: self.set_font('Arial','B',20); self.cell(0,10,'HEALTHY WATER',0,1,'C')
        self.ln(20)

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة:", ["بيانات العملاء", "جدول المواعيد", "المخزن والاحتياجات", "تسجيل صيانة", "صفحة الأرباح 📈", "إضافة عميل"])

# --- صفحة بيانات العملاء ---
if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("بحث...")
    filtered = df_c[df_c['name'].astype(str).str.contains(search)] if search else df_c
    
    for idx, r in filtered.iterrows():
        with st.expander(f"👤 {r['name']} - {r.get('area','')}"):
            # أزرار التعديل والحذف
            c1, c2, c3 = st.columns([1,1,4])
            c1.button("📝 تعديل", key=f"edit_c_{idx}")
            c2.button("🗑️ حذف", key=f"del_c_{idx}")
            
            # جدول الصيانات بكافة الأعمدة
            history = df_m[df_m['name'] == r['name']].sort_values(by='v_date_dt', ascending=False)
            full_cols = ['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared', 'other_item', 'amount', 'notes']
            st.dataframe(history[full_cols], hide_index=True)
            st.button("📥 تحميل PDF (سريع)", key=f"pdf_{idx}")

# --- صفحة جدول المواعيد (مع الترحيل التلقائي) ---
elif menu == "جدول المواعيد":
    st.header("📅 جدول المواعيد (المُرّحلة والجديدة)")
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
            if final_d < today: final_d = today # ترحيل تلقائي لليوم
            sched.append({'name': r['name'], 'date': final_d, 'area': r['area']})
            
    sdf = pd.DataFrame(sched)
    for i in range(7):
        curr = today + timedelta(days=i)
        st.subheader(f"{curr} " + ("(اليوم)" if i==0 else ""))
        res = sdf[sdf['date'] == curr]
        for _, row in res.iterrows(): st.write(f"🔹 {row['name']} - {row['area']}")

# --- صفحة المخزن والاحتياجات ---
elif menu == "المخزن والاحتياجات":
    t1, t2 = st.tabs(["المخزن", "الاحتياجات ⚠️"])
    with t1:
        for idx, r in df_inv.iterrows():
            c1, c2, c3 = st.columns([3,2,1])
            c1.write(f"**{r['item_name']}**")
            new_q = c2.number_input("الكمية", value=int(r['quantity']), key=f"inv_{idx}")
            if c3.button("تحديث", key=f"upd_{idx}"):
                execute_gsheet_action("update", "Inventory", [r['item_name'], new_q, r['min_limit']], idx+2)
                st.rerun()
    with t2:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        st.table(shortage[['item_name', 'quantity', 'min_limit']])

# --- صفحة تسجيل صيانة (القائمة المنسدلة) ---
elif menu == "تسجيل صيانة":
    st.header("🔧 تسجيل زيارة")
    main_parts = ['p1', 'p2', 'p3', 'membrane', 'post carbon', 'calcite', 'infrared']
    other_options = [n for n in df_inv['item_name'].tolist() if n.lower() not in main_parts]
    
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        date = st.date_input("التاريخ")
        c1, c2, c3 = st.columns(3)
        s1 = c1.checkbox("P1"); s2 = c1.checkbox("P2"); s3 = c1.checkbox("P3")
        s4 = c2.checkbox("Membrane"); s5 = c2.checkbox("Post Carbon")
        s6 = c3.checkbox("Calcite"); s7 = c3.checkbox("Infrared")
        other = st.selectbox("قطع غيار أخرى", ["لا يوجد"] + other_options)
        amt = st.number_input("المبلغ المحصل", 0.0)
        note = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"):
            data = [name, str(date), s1, s2, s3, s4, s5, s6, s7, other, amt, note, ""]
            execute_gsheet_action("append", "Maintenance", data)
            st.success("تم الحفظ"); st.rerun()

# --- داخل صفحة الأرباح ---
def calc_visit_cost(row):
    cost = 0.0
    # خريطة تربط أسماء الخانات في سجل الصيانة بأسماء القطع في المخزن
    # تأكد أن الأسماء في المخزن (item_name) مطابقة تماماً لما هو مكتوب هنا
    parts_map = {
        'P1': 'p1', 
        'P2': 'p2', 
        'P3': 'p3', 
        'membrane': 'membrane', 
        'post_carbon': 'post carbon', 
        'Calcite': 'calcite', 
        'infrared': 'infrared'
    }
    
    for col, inv_name in parts_map.items():
        # لو الخانة متعلم عليها (True/Yes/✅)
        if str(row.get(col, '')).lower() in ['true', '1', 'yes', '✅']:
            # هيدور على سعر التكلفة للقطعة دي في شيت المخزن
            try:
                item_cost = to_num(df_inv[df_inv['item_name'].str.lower() == inv_name.lower()]['cost_price'].values[0])
                cost += item_cost
            except:
                pass # لو القطعة مش موجودة في المخزن بيكمل عادي
                
    # حساب تكلفة "قطع غيار أخرى" لو موجودة
    other_p = str(row.get('other_item', '')).strip()
    if other_p != "" and other_p != "لا يوجد":
        try:
            other_cost = to_num(df_inv[df_inv['item_name'] == other_p]['cost_price'].values[0])
            cost += other_cost
        except:
            pass
            
    return cost

    if not df_m.empty:
        df_m['visit_cost'] = df_m.apply(calc_visit_cost, axis=1)
        df_m['net_profit'] = df_m['amount_num'] - df_m['visit_cost']
        
        # تجميع يومي
        daily_profit = df_m.groupby(df_m['v_date_dt'].dt.date)['net_profit'].sum()
        
        today = datetime.now().date()
        st.metric("صافي أرباح اليوم", f"{daily_profit.get(today, 0.0)} EGP")
        
        # رسم بياني للتقدم
        fig = px.line(daily_profit.reset_index(), x='v_date_dt', y='net_profit', title="منحنى الأرباح الصافية")
        st.plotly_chart(fig, use_container_config=True)
        
        col1, col2 = st.columns(2)
        col1.subheader("أرباح الأسبوع")
        col1.write(f"{df_m[df_m['v_date_dt'].dt.date > (today - timedelta(days=7))]['net_profit'].sum()} EGP")
        col2.subheader("أرباح الشهر")
        col2.write(f"{df_m[df_m['v_date_dt'].dt.month == today.month]['net_profit'].sum()} EGP")
