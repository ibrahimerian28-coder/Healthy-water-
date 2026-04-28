import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import io

# --- 1. الدوال المركزية ---
def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    url = "https://script.google.com/macros/s/AKfycbwyCuybxsP72RoNybypMcBQuGl8OJIDuwZBXcuw5Tx2KCgodVn751UEqkqLYsvTVn3oXg/exec"
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

st.set_page_config(page_title="Healthy Water Pro", layout="wide")

def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0.0
        return float(str(val).replace(',', '').strip())
    except: return 0.0

@st.cache_data(ttl=1)
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        df['row_index_internal'] = range(2, len(df) + 2)
        return df.fillna("")
    except: return pd.DataFrame()

def parse_dt(val):
    val = str(val).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

# --- 2. تحميل وتجهيز البيانات ---
df_c = load_data("0")          # Customers
df_m = load_data("2120582392") # Maintenance
df_inv = load_data("1767710106") # Inventory
df_exp = load_data("288947510")  # Expenses

if not df_inv.empty:
    df_inv['quantity'] = df_inv['quantity'].apply(to_num)
    df_inv['cost_price'] = df_inv['cost_price'].apply(to_num)

if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

if not df_exp.empty:
    df_exp['date_dt'] = df_exp['date'].apply(parse_dt)
    for col in ['transportation', 'sundries', 'monthly_expensess', 'salaries']:
        if col in df_exp.columns: df_exp[col] = df_exp[col].apply(to_num)

# --- 3. كلاس الـ PDF ---
class HealthyPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'HEALTHY WATER - MAINTENANCE REPORT', 0, 1, 'C')
        self.ln(10)

def create_pdf_report(cust_row, history_df):
    pdf = HealthyPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Customer: {cust_row['name']}", ln=True)
    pdf.cell(0, 10, f"Area: {cust_row.get('area', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    cols = ['Date', 'P1', 'P2', 'P3', 'Mem', 'Post', 'Calc', 'Inf', 'Other', 'Amt']
    for col in cols: pdf.cell(19, 10, col, 1)
    pdf.ln()
    pdf.set_font("Arial", size=9)
    for _, row in history_df.iterrows():
        pdf.cell(19, 10, str(row['visit_date']), 1)
        for p in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            val = "✅" if str(row.get(p,'')).lower() in ['true','1','yes','✅'] else "-"
            pdf.cell(19, 10, val, 1)
        pdf.cell(19, 10, str(row.get('other','-'))[:8], 1)
        pdf.cell(19, 10, str(row.get('amount','0')), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "تسجيل صيانة 🔧", "صفحة الأرباح 📈", "إضافة عميل"])

# --- صفحة بيانات العملاء ---
if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("بحث بالاسم أو المنطقة...")
    filtered = df_c[df_c['name'].astype(str).str.contains(search) | df_c['area'].astype(str).str.contains(search)] if search else df_c
    
    for idx, r in filtered.iterrows():
        with st.expander(f"👤 {r['name']} - {r.get('area','')}"):
            st.write(f"📍 **العنوان:** {r.get('adress','')} | 📞 **التليفونات:** {r.get('phone','')} / {r.get('phone_1','')} / {r.get('phone_2','')}")
            st.write(f"📅 **تاريخ التركيب:** {r.get('install_date','')} | 🔗 [موقع العميل]({r.get('location_url','#')})")
            
            c1, c2 = st.columns([1,4])
            if c1.button("🗑️ حذف العميل", key=f"del_c_{idx}"):
                if execute_gsheet_action("delete", "Customers", row_index=r['row_index_internal']):
                    st.success("تم الحذف"); st.rerun()
            
            history = df_m[df_m['name'] == r['name']].sort_values(by='v_date_dt', ascending=False)
            if not history.empty:
                display_h = history.copy()
                bool_cols = ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']
                for col in bool_cols:
                    display_h[col] = display_h[col].apply(lambda x: "✅" if str(x).lower() in ['true','1','yes','✅'] else "❌")
                
                st.dataframe(display_h[['visit_date'] + bool_cols + ['other', 'amount', 'notes']], hide_index=True)
                
                sel_v = st.selectbox("حذف زيارة:", history['visit_date'].tolist(), key=f"v_s_{idx}")
                if st.button("🗑️ تأكيد حذف الزيارة", key=f"v_d_{idx}"):
                    v_row = history[history['visit_date'] == sel_v].iloc[0]
                    if execute_gsheet_action("delete", "Maintenance", row_index=v_row['row_index_internal']):
                        st.success("تم الحذف"); st.rerun()

                pdf_bytes = create_pdf_report(r, history)
                st.download_button("📥 PDF التقرير", data=pdf_bytes, file_name=f"{r['name']}.pdf", mime="application/pdf", key=f"p_b_{idx}")

# --- صفحة جدول المواعيد ---
elif menu == "جدول المواعيد":
    st.header("📅 مواعيد العمل المتوقعة")
    today = datetime.now().date()
    sched = []
    for _, r in df_c.iterrows():
        user_m = df_m[df_m['name'] == r['name']]
        if not user_m.empty:
            last_v = user_m.sort_values('v_date_dt').iloc[-1]
            cycle = int(to_num(r.get('cycle', 3)))
            nxt = (last_v['v_date_dt'] + timedelta(days=cycle*30)).date()
            final_d = nxt if nxt >= today else today
            sched.append({'name': r['name'], 'date': final_d, 'area': r.get('area','')})
    
    if sched:
        sdf = pd.DataFrame(sched)
        for i in range(7):
            curr = today + timedelta(days=i)
            st.subheader(f"{curr} - {('اليوم' if i==0 else '')}")
            res = sdf[sdf['date'] == curr]
            for _, row in res.iterrows(): st.write(f"🔹 **{row['name']}** - {row['area']}")

# --- صفحة المخزن ---
elif menu == "المخزن 📦":
    st.header("📦 المخزن والأسعار")
    with st.expander("➕ إضافة صنف جديد"):
        with st.form("add_inv"):
            n = st.text_input("اسم الصنف")
            q = st.number_input("الكمية", 0)
            m = st.number_input("حد الأدنى", 5)
            c = st.number_input("السعر", 0.0)
            if st.form_submit_button("حفظ"):
                if execute_gsheet_action("append", "Inventory", [n, q, m, c]):
                    st.success("تم"); st.rerun()

    for idx, r in df_inv.iterrows():
        c1, c2, c3, c4 = st.columns([2,1,1,1])
        c1.write(f"**{r['item_name']}**")
        new_q = c2.number_input("كمية", value=int(r['quantity']), key=f"iq_{idx}")
        new_p = c3.number_input("سعر", value=float(r['cost_price']), key=f"ip_{idx}")
        if c4.button("تحديث", key=f"ib_{idx}"):
            if execute_gsheet_action("update", "Inventory", [r['item_name'], new_q, r['min_limit'], new_p], row_index=r['row_index_internal']):
                st.success("تم"); st.rerun()

# --- تسجيل صيانة ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 زيارة صيانة")
    main_p = ['p1', 'p2', 'p3', 'membrane', 'post carbon', 'calcite', 'infrared']
    other_opts = [n for n in df_inv['item_name'].tolist() if n.lower() not in main_p]
    
    with st.form("m_reg"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        date = st.date_input("التاريخ")
        col1, col2, col3 = st.columns(3)
        p1 = col1.checkbox("P1"); p2 = col1.checkbox("P2"); p3 = col1.checkbox("P3")
        mem = col2.checkbox("Membrane"); post = col2.checkbox("Post Carbon")
        calc = col3.checkbox("Calcite"); infra = col3.checkbox("Infrared")
        other = st.selectbox("أخرى", ["لا يوجد"] + other_opts)
        amt = st.number_input("المبلغ", 0.0)
        note = st.text_area("ملاحظات")
        if st.form_submit_button("حفظ"):
            # ترتيب الأعمدة: name/visit_date/P1/P2/P3/membrane/post_carbon/Calcite/infrared/other/amount/notes/special_date/customer_id
            data = [name, str(date), p1, p2, p3, mem, post, calc, infra, other, amt, note, "", ""]
            if execute_gsheet_action("append", "Maintenance", data):
                st.success("تم الحفظ"); st.rerun()

# --- صفحة الأرباح ---
elif menu == "صفحة الأرباح 📈":
    st.header("📈 تقرير الأرباح الشامل")
    f_date1 = st.date_input("من", datetime.now() - timedelta(days=30))
    f_date2 = st.date_input("إلى", datetime.now())

    def get_cost(row):
        total = 0.0
        p_map = {'P1':'p1','P2':'p2','P3':'p3','membrane':'membrane','post_carbon':'post carbon','Calcite':'calcite','infrared':'infrared'}
        for col, inv_n in p_map.items():
            if str(row.get(col,'')).lower() in ['true','1','yes','✅']:
                try: total += to_num(df_inv[df_inv['item_name'].str.lower() == inv_n.lower()]['cost_price'].values[0])
                except: pass
        if str(row.get('other','')) != "لا يوجد":
            try: total += to_num(df_inv[df_inv['item_name'] == row['other']]['cost_price'].values[0])
            except: pass
        return total

    if not df_m.empty:
        df_m['visit_cost'] = df_m.apply(get_cost, axis=1)
        df_m['gross_profit'] = df_m['amount_num'] - df_m['visit_cost']
        
        mask = (df_m['v_date_dt'].dt.date >= f_date1) & (df_m['v_date_dt'].dt.date <= f_date2)
        filtered_m = df_m[mask]
        
        # حساب المصاريف من شيت Expenses
        total_exp = 0.0
        if not df_exp.empty:
            mask_e = (df_exp['date_dt'].dt.date >= f_date1) & (df_exp['date_dt'].dt.date <= f_date2)
            total_exp = df_exp[mask_e][['transportation','sundries','monthly_expensess','salaries']].sum().sum()

        net = filtered_m['gross_profit'].sum() - total_exp
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي التحصيل", f"{filtered_m['amount_num'].sum():,.1f}")
        c2.metric("إجمالي المصاريف", f"{total_exp:,.1f}")
        c3.metric("صافي الربح النهائي", f"{net:,.1f}")
        
        st.plotly_chart(px.bar(filtered_m, x='v_date_dt', y='gross_profit', title="الربح اليومي (قبل المصاريف العامة)"))

# --- إضافة عميل ---
elif menu == "إضافة عميل":
    st.header("➕ إضافة عميل")
    with st.form("new_cust"):
        name = st.text_input("الاسم")
        c1, c2, c3 = st.columns(3)
        ph = c1.text_input("تليفون")
        ph1 = c1.text_input("تليفون 1")
        ph2 = c2.text_input("تليفون 2")
        ph3 = c2.text_input("تليفون 3")
        ph4 = c3.text_input("تليفون 4")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        url = st.text_input("اللوكيشن URL")
        inst = st.date_input("تاريخ التركيب")
        cyc = st.number_input("دورة الصيانة", 3)
        if st.form_submit_button("حفظ"):
            # الترتيب: name/phone/phone_1/phone _2/phone_3/phone_4/adress/area/location_url/install_date/cycle/status
            c_data = [name, ph, ph1, ph2, ph3, ph4, addr, area, url, str(inst), cyc, "نشط"]
            if execute_gsheet_action("append", "Customers", c_data):
                st.success("تم الحفظ"); st.rerun()
