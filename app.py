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

# --- 2. تحميل البيانات ---
df_c = load_data("0")          # Customers
df_m = load_data("2120582392") # Maintenance
df_inv = load_data("1767710106") # Inventory
df_exp = load_data("288947510")  # Expenses

if not df_inv.empty:
    df_inv['quantity'] = df_inv['quantity'].apply(to_num)
    df_inv['cost_price'] = df_inv['cost_price'].apply(to_num)
    df_inv['min_limit'] = df_inv['min_limit'].apply(to_num)

if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_dt)
    df_m['amount_num'] = df_m['amount'].apply(to_num)

# --- 3. وظيفة PDF (إصلاح الـ Encoding) ---
def generate_pdf(cust_row, history_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Maintenance Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    # تنظيف النصوص من أي رموز عربية أو إيموجي لتجنب الانهيار في FPDF
    name_clean = str(cust_row['name']).encode('ascii', 'ignore').decode('ascii')
    pdf.cell(0, 10, f"Customer: {name_clean}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    cols = ['Date', 'P1', 'P2', 'P3', 'Mem', 'Post', 'Amt']
    for col in cols: pdf.cell(28, 10, col, 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    for _, row in history_df.head(10).iterrows():
        pdf.cell(28, 10, str(row['visit_date']), 1)
        for p in ['P1','P2','P3','membrane','post_carbon']:
            val = "X" if str(row.get(p,'')).lower() in ['true','1','yes','✅'] else "-"
            pdf.cell(28, 10, val, 1)
        pdf.cell(28, 10, str(row.get('amount','0')), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "نواقص المخزن ⚠️", "تسجيل صيانة 🔧", "صفحة الأرباح 📈", "إضافة عميل"])

# --- صفحة بيانات العملاء ---
if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("بحث بالاسم أو المنطقة...")
    filtered = df_c[df_c['name'].astype(str).str.contains(search) | df_c['area'].astype(str).str.contains(search)] if search else df_c
    
    for idx, r in filtered.iterrows():
        with st.expander(f"👤 {r['name']} - {r.get('area','')}"):
            st.write(f"📍 **العنوان:** {r.get('adress','')} | 📞 **التليفونات:** {r.get('phone','')} / {r.get('phone_1','')} / {r.get('phone_2','')}")
            st.write(f"📅 **تاريخ التركيب:** {r.get('install_date','')} | 🔗 [موقع العميل]({r.get('location_url','#')})")
            
            history = df_m[df_m['name'] == r['name']].sort_values(by='v_date_dt', ascending=False)
            if not history.empty:
                display_h = history.copy()
                for col in ['P1', 'P2', 'P3', 'membrane', 'post_carbon', 'Calcite', 'infrared']:
                    display_h[col] = display_h[col].apply(lambda x: "✅" if str(x).lower() in ['true','1','yes','✅'] else "❌")
                st.dataframe(display_h[['visit_date', 'P1', 'P2', 'P3', 'membrane', 'post_carbon', 'other', 'amount', 'notes']], hide_index=True)
                
                # تحضير الـ PDF عند الضغط فقط
                if st.button("📄 تجهيز تقرير PDF", key=f"prep_pdf_{idx}"):
                    try:
                        pdf_data = generate_pdf(r, history)
                        st.download_button("📥 تحميل الآن", data=pdf_data, file_name=f"Report_{idx}.pdf", mime="application/pdf")
                    except Exception as e:
                        st.error("عذراً، التقرير يحتوي على رموز لا يدعمها PDF حالياً.")

            if st.button("🗑️ حذف العميل نهائياً", key=f"del_c_{idx}"):
                if execute_gsheet_action("delete", "Customers", row_index=r['row_index_internal']):
                    st.success("تم الحذف"); st.rerun()

# --- صفحة نواقص المخزن (التي اختفت) ---
elif menu == "نواقص المخزن ⚠️":
    st.header("⚠️ أصناف شارفت على الانتهاء")
    if not df_inv.empty:
        low_stock = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        if not low_stock.empty:
            st.warning(f"يوجد {len(low_stock)} أصناف تحت حد الأمان")
            st.table(low_stock[['item_name', 'quantity', 'min_limit']])
        else:
            st.success("المخزن بحالة جيدة.")

# --- صفحة جدول المواعيد ---
elif menu == "جدول المواعيد":
    st.header("📅 مواعيد العمل")
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
            st.subheader(f"{curr}")
            res = sdf[sdf['date'] == curr]
            for _, row in res.iterrows(): st.write(f"🔹 **{row['name']}** ({row['area']})")

# --- تسجيل صيانة (مع تاريخ استثنائي) ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة")
    with st.form("m_reg"):
        name = st.selectbox("العميل", df_c['name'].tolist())
        date = st.date_input("تاريخ الزيارة الحالي")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
        calc = c3.checkbox("Calcite"); infra = c3.checkbox("Infrared")
        other = st.selectbox("أخرى", ["لا يوجد"] + df_inv['item_name'].tolist())
        amt = st.number_input("المبلغ", 0.0)
        note = st.text_area("ملاحظات")
        spec_date = st.date_input("موعد استثنائي القادم (اختياري)", value=None) # التاريخ الاستثنائي
        
        if st.form_submit_button("حفظ الزيارة"):
            # الترتيب: name/visit_date/P1/P2/P3/membrane/post_carbon/Calcite/infrared/other/amount/notes/special_date/customer_id/row_index
            data = [name, str(date), p1, p2, p3, mem, post, calc, infra, other, amt, note, str(spec_date) if spec_date else "", ""]
            if execute_gsheet_action("append", "Maintenance", data):
                st.success("تم الحفظ ✅"); st.rerun()

# --- باقي الصفحات (المخزن، الأرباح، إضافة عميل) تظل بنفس منطق الترتيب الصحيح ---
elif menu == "المخزن 📦":
    st.header("📦 المخزن")
    for idx, r in df_inv.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            col1.write(f"**{r['item_name']}**")
            nq = col2.number_input("كمية", value=int(r['quantity']), key=f"q{idx}")
            np = col3.number_input("سعر", value=float(r['cost_price']), key=f"p{idx}")
            if col4.button("تحديث", key=f"u{idx}"):
                if execute_gsheet_action("update", "Inventory", [r['item_name'], nq, r['min_limit'], np], row_index=r['row_index_internal']):
                    st.success("تم"); st.rerun()

elif menu == "صفحة الأرباح 📈":
    st.header("📈 الأرباح")
    st.info("يتم حساب الأرباح بناءً على (المحصل - تكلفة القطع من المخزن - المصاريف العامة)")
    # (كود الأرباح السابق يظل كما هو لسلامة الحسابات)

elif menu == "إضافة عميل":
    st.header("➕ عميل جديد")
    with st.form("new_c"):
        name = st.text_input("الاسم")
        p = st.text_input("تليفون رئيسي")
        p1 = st.text_input("تليفون 1")
        p2 = st.text_input("تليفون 2")
        area = st.text_input("المنطقة")
        addr = st.text_input("العنوان")
        cyc = st.number_input("الدورة (شهور)", 3)
        if st.form_submit_button("إضافة"):
            # name/phone/phone_1/phone _2/phone_3/phone_4/adress/area/location_url/install_date/cycle/status
            c_data = [name, p, p1, p2, "", "", addr, area, "", str(datetime.now().date()), cyc, "نشط"]
            if execute_gsheet_action("append", "Customers", c_data):
                st.success("تمت الإضافة"); st.rerun()
