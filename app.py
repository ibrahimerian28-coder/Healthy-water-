import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. دالة التنفيذ المركزية لربط الإكسيل ---
def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    url = "https://script.google.com/macros/s/AKfycbwyCuybxsP72RoNybypMcBQuGl8OJIDuwZBXcuw5Tx2KCgodVn751UEqkqLYsvTVn3oXg/exec"
    payload = {"action": action, "sheet": sheet_name, "data": data, "row_index": row_index}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"خطأ في التنفيذ: {e}")
        return False

# --- 2. إعدادات الصفحة والوظائف المساعدة ---
st.set_page_config(page_title="Healthy Water Pro - Admin", layout="wide")

def get_arabic_day(date_obj):
    days = {'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'}
    return days.get(date_obj.strftime('%A'), date_obj.strftime('%A'))

@st.cache_data(ttl=2) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        if 'name' in df.columns: df['name'] = df['name'].astype(str).str.strip()
        return df.fillna("") 
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✅" if v in ['true', '1', 'checked', 'تم', 'yes', '✓'] else "❌"

def clean_text_for_pdf(text):
    if not text or text == "nan": return "-"
    return "".join(i for i in str(text) if ord(i) < 128)

def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080"
    if not next_date or pd.isnull(next_date): return "#f0f2f6"
    today = datetime.now().date()
    diff = (next_date - today).days
    if diff < 0: return "#dc3545" 
    elif 0 <= diff <= 7: return "#ffc107" 
    else: return "#28a745" 

def parse_date(val):
    val = str(val).strip()
    if not val or val in ["", "nan"]: return pd.NaT
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
        try: return pd.to_datetime(val, format=fmt)
        except: continue
    return pd.to_datetime(val, errors='coerce')

# --- 3. كلاس الـ PDF المطور (مع الشعار والفوتر) ---
class HealthyPDF(FPDF):
    def header(self):
        try:
            # شعار الشركة في المنتصف بحجم كبير
            self.image("logo.png", x=110, y=8, w=80) 
        except:
            self.set_font('Arial', 'B', 25)
            self.set_text_color(40, 116, 166)
            self.cell(0, 20, 'HEALTHY WATER', 0, 1, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.line(10, self.get_y(), 287, self.get_y())
        self.ln(2)
        self.cell(0, 10, 'Technical Support & Maintenance: 01286609535', 0, 0, 'C')
        self.set_x(-20)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')

def generate_safe_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 0, 0)
    customer_name = clean_text_for_pdf(row['name'])
    pdf.cell(0, 15, f"Service History Report: {customer_name}", ln=True, align='L')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Area: {clean_text_for_pdf(row.get('area',''))} | Installation Date: {row.get('setup_date','')}", ln=True)
    pdf.ln(5)
    
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Other Parts", "Cost", "Notes"]
    col_widths = [25, 12, 12, 12, 12, 12, 12, 12, 40, 20, 100]
    
    pdf.set_fill_color(40, 116, 166)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 10)
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 12, h, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    
    history = df_m[df_m['name'] == row['name']].copy()
    history['v_date_dt'] = history['visit_date'].apply(parse_date)
    history = history.sort_values(by='v_date_dt', ascending=False)
    
    fill = False
    for _, m in history.iterrows():
        pdf.set_fill_color(245, 247, 249) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_widths[0], 10, str(m.get('visit_date',''))[:10], 1, 0, 'C', True)
        
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            is_checked = format_to_check(m.get(f,'')) == "✅"
            val = "YES" if is_checked else "-"
            if is_checked: pdf.set_text_color(40, 167, 69)
            pdf.cell(12, 10, val, 1, 0, 'C', True)
            pdf.set_text_color(0, 0, 0)
            
        pdf.cell(col_widths[8], 10, clean_text_for_pdf(str(m.get('other_item', '-'))), 1, 0, 'C', True)
        pdf.cell(col_widths[9], 10, str(m.get('amount','0')), 1, 0, 'C', True)
        
        note_text = clean_text_for_pdf(str(m.get('notes', '-')))
        if len(note_text) > 55: note_text = note_text[:52] + "..."
        pdf.cell(col_widths[10], 10, note_text, 1, 0, 'L', True)
        pdf.ln()
        fill = not fill
        
    return bytes(pdf.output())

# --- 4. تحميل البيانات ومعالجة المواعيد ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

available_areas = sorted(list(set(df_c['area'].astype(str).unique()))) if not df_c.empty else []

last_v_info = {}
if not df_m.empty:
    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_date)
    valid_m = df_m.dropna(subset=['v_date_dt']).sort_values(by='v_date_dt')
    for name in valid_m['name'].unique():
        user_h = valid_m[valid_m['name'] == name]
        last_row = user_h.iloc[-1].to_dict()
        last_row['spec_dt_clean'] = parse_date(last_row.get('special_date', ""))
        last_v_info[name] = last_row

# --- 5. نظام تسجيل الدخول ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("💧 Healthy Water Management")
    pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
    if st.sidebar.button("دخول"):
        if pwd == "HgM18082019$&)": st.session_state.auth = "admin"; st.rerun()
        else: st.error("الباسورد غلط!")
    st.stop()

menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "إضافة عميل جديد"])

# --- صفحة بيانات العملاء ---
if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("ابحث بالاسم أو المنطقة...")
    filtered = df_c[df_c['name'].str.contains(search, na=False) | df_c['area'].str.contains(search, na=False)] if search else df_c

    for idx, r in filtered.iterrows():
        name = r['name']
        last_v = last_v_info.get(name, {})
        next_main, next_spec = None, None
        
        if last_v and pd.notnull(last_v['v_date_dt']):
            try: cycle = int(float(str(r.get('maintenance_cycle', 3))))
            except: cycle = 3
            next_main = (last_v['v_date_dt'] + timedelta(days=cycle * 30)).date()
            if pd.notnull(last_v.get('spec_dt_clean')):
                next_spec = last_v['spec_dt_clean'].date()

        display_date = next_spec if next_spec else next_main
        status_color = get_status_color(display_date, r.get('status', ''))
        
        st.markdown(f"""
            <div style="padding:10px; border-radius:8px; margin-bottom:10px; background-color:#ffffff; border-right:12px solid {status_color}; border-left:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd;">
                <h4 style="margin:0;">👤 {name} {" <span style='color:red; font-size:12px;'>(موعد استثنائي)</span>" if next_spec else ""}</h4>
                <p style="margin:0; font-size:13px; color:#666;">📍 {r.get('area','')} | الموعد القادم: <b>{display_date if display_date else 'غير محدد'}</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("تفاصيل التواصل وسجل الصيانة"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                if r.get('location') and str(r['location']).startswith("http"):
                    st.markdown(f"📍 **[فتح الموقع على الخريطة]({r['location']})**")
                
                # إظهار كافة أرقام الموبايل الأربعة مع أزرار ملونة
                for p_col in ['phone', 'phone_1', 'phone_2', 'phone_3']:
                    p_val = str(r.get(p_col, '')).strip()
                    if p_val and p_val not in ["nan", "", "0"]:
                        st.markdown(f"""<div style="display:flex; gap:10px; margin-bottom:5px;"><b>📞 {p_val}</b> 
                        <a href="tel:{p_val}" style="background:#075e54; color:white; padding:2px 8px; border-radius:4px; text-decoration:none; font-size:12px;">اتصال</a>
                        <a href="https://wa.me/2{p_val}" style="background:#25d366; color:white; padding:2px 8px; border-radius:4px; text-decoration:none; font-size:12px;">واتساب</a></div>""", unsafe_allow_html=True)

            with col2:
                st.write("**🛠️ سجل آخر الصيانات:**")
                history = df_m[df_m['name'] == name].tail(10)
                if not history.empty:
                    hist_display = history.copy()
                    for col in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
                        hist_display[col] = hist_display[col].apply(format_to_check)
                    st.dataframe(hist_display[['visit_date', 'P1', 'P2', 'P3', 'membrane', 'amount']], hide_index=True)
                
                st.download_button("📥 تحميل سجل الصيانة PDF", generate_safe_pdf(r, df_m), f"{name}_Report.pdf", key=f"pdf_{idx}")

# --- صفحة جدول المواعيد ---
elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    today = datetime.now().date()
    sched_list = []
    for _, r in df_c.iterrows():
        lv = last_v_info.get(r['name'], {})
        if lv and pd.notnull(lv['v_date_dt']):
            try: cycle = int(float(str(r.get('maintenance_cycle', 3))))
            except: cycle = 3
            m_date = (lv['v_date_dt'] + timedelta(days=cycle*30)).date()
            sched_list.append({'name': r['name'], 'date': m_date, 'area': r['area'], 'type': 'دورية'})
            if pd.notnull(lv.get('spec_dt_clean')):
                sched_list.append({'name': r['name'], 'date': lv['spec_dt_clean'].date(), 'area': r['area'], 'type': 'استثنائي'})
    
    if sched_list:
        sdf = pd.DataFrame(sched_list)
        for i in range(7):
            curr = today + timedelta(days=i)
            st.subheader(f"{get_arabic_day(curr)} ({curr})")
            day_res = sdf[sdf['date'] == curr]
            if not day_res.empty:
                for _, row in day_res.iterrows():
                    color = "red" if row['type'] == 'استثنائي' else "blue"
                    st.markdown(f"🔹 **{row['name']}** ({row['area']}) - <span style='color:{color};'>{row['type']}</span>", unsafe_allow_html=True)
            else: st.write(":grey[لا توجد مواعيد]")

# --- صفحة المخزن ---
elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    for idx, r in df_inv.iterrows():
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{r['item_name']}** (الحالي: {r['quantity']})")
        new_q = c2.number_input("تعديل الكمية", value=int(r['quantity']), key=f"inv_{idx}")
        if c3.button("تحديث", key=f"btn_{idx}"):
            if execute_gsheet_action("update", "Inventory", data=[r['item_name'], new_q, r['min_limit']], row_index=idx+2):
                st.success("تم التحديث"); st.cache_data.clear(); st.rerun()

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    shortage = df_inv[df_inv['quantity'].astype(float) <= df_inv['min_limit'].astype(float)]
    st.table(shortage[['item_name', 'quantity', 'min_limit']])

# --- صفحة إضافة عميل جديد ---
elif menu == "إضافة عميل جديد":
    st.header("➕ إضافة عميل جديد")
    with st.form("add_form"):
        name = st.text_input("اسم العميل")
        col_p1, col_p2 = st.columns(2)
        p1 = col_p1.text_input("موبايل 1")
        p2 = col_p2.text_input("موبايل 2")
        p3 = col_p1.text_input("موبايل 3")
        p4 = col_p2.text_input("موبايل 4")
        
        area_type = st.selectbox("المنطقة", ["-- اختر --"] + available_areas + ["إضافة منطقة جديدة"])
        new_area = st.text_input("اسم المنطقة الجديدة") if area_type == "إضافة منطقة جديدة" else ""
        
        addr = st.text_input("العنوان بالتفصيل")
        loc = st.text_input("رابط اللوكيشن (Google Maps)")
        setup = st.date_input("تاريخ التركيب")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        status = st.selectbox("حالة العميل", ["نشط", "راكد"])
        
        if st.form_submit_button("حفظ العميل الجديد"):
            f_area = new_area if area_type == "إضافة منطقة جديدة" else area_type
            row = [name, p1, p2, p3, p4, f_area, addr, loc, str(setup), cycle, status]
            if execute_gsheet_action("append", "Customers", data=row):
                st.success("تمت الإضافة بنجاح ✅"); st.cache_data.clear(); st.rerun()

# --- صفحة تسجيل صيانة ---
elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        c_name = st.selectbox("اسم العميل", df_c['name'].tolist() if not df_c.empty else [])
        v_date = st.date_input("تاريخ الزيارة")
        s_date = st.date_input("موعد استثنائي (اختياري)", value=None)
        st.write("---")
        c1, c2, c3 = st.columns(3)
        sh1 = c1.checkbox("P1"); sh2 = c1.checkbox("P2"); sh3 = c1.checkbox("P3")
        sh4 = c2.checkbox("Membrane"); sh5 = c2.checkbox("Post Carbon")
        sh6 = c3.checkbox("Calcite"); sh7 = c3.checkbox("Infrared")
        other = st.text_input("قطع أخرى")
        price = st.number_input("المبلغ", 0.0)
        note = st.text_area("ملاحظات")
        
        if st.form_submit_button("حفظ الزيارة"):
            data = [c_name, str(v_date), sh1, sh2, sh3, sh4, sh5, sh6, sh7, other, price, note, str(s_date) if s_date else ""]
            if execute_gsheet_action("append", "Maintenance", data=data):
                st.success("تم الحفظ ✅"); st.cache_data.clear(); st.rerun()

# --- المصروفات ---
elif menu == "المصروفات والحسابات 💸":
    st.header("💸 المصروفات")
    with st.form("exp"):
        d = st.date_input("التاريخ")
        t = st.number_input("انتقالات", 0.0); s = st.number_input("نثريات", 0.0)
        m = st.number_input("مصروف شهري", 0.0); sa = st.number_input("رواتب", 0.0)
        if st.form_submit_button("حفظ"):
            if execute_gsheet_action("append", "Expenses", data=[str(d), t, s, m, sa]):
                st.success("تم الحفظ"); st.cache_data.clear(); st.rerun()
