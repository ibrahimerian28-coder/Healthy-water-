import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- دالة التنفيذ (حذف/تعديل/إضافة) ---
def execute_gsheet_action(action, sheet_name, data=None, row_index=None):
    url = "https://script.google.com/macros/s/AKfycbwyCuybxsP72RoNybypMcBQuGl8OJIDuwZBXcuw5Tx2KCgodVn751UEqkqLYsvTVn3oXg/exec"
    payload = {
        "action": action,
        "sheet": sheet_name,
        "data": data,
        "row_index": row_index
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"خطأ في التنفيذ: {e}")
        return False

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water Pro - Level الوحش", layout="wide")

def get_arabic_day(date_obj):
    days = {
        'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
        'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
    }
    return days.get(date_obj.strftime('%A'), date_obj.strftime('%A'))

@st.cache_data(ttl=5) 
def load_all_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        if 'name' in df.columns:
            df['name'] = df['name'].astype(str).str.strip()
        num_cols = ['quantity', 'unit_price', 'min_limit', 'transportation', 'sundries', 'monthly_expensess', 'salaries', 'amount', 'maintenance_cycle']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.fillna("") 
    except: return pd.DataFrame()

def format_to_check(val):
    v = str(val).lower().strip()
    return "✅" if v in ['true', '1', 'checked', 'تم', 'yes', '✓'] else "❌"

def clean_text_for_pdf(text):
    if not text: return ""
    return "".join(i for i in str(text) if ord(i) < 128)

def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080"
    if not next_date or pd.isnull(next_date): return "#f0f2f6"
    if isinstance(next_date, datetime): next_date = next_date.date()
    today = datetime.now().date()
    diff = (next_date - today).days
    if diff < 0: return "#dc3545" 
    elif 0 <= diff <= 7: return "#ffc107" 
    else: return "#28a745" 

class HealthyPDF(FPDF):
    def header(self):
        try: self.image("logo.png", 10, 8, 50)
        except: pass
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Service Report - Healthy Water', 0, 1, 'R')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Healthy Water Company - Support: 01286609535', 0, 0, 'C')

def generate_safe_pdf(row, df_m):
    pdf = HealthyPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Customer: {clean_text_for_pdf(row['name'])}", ln=True)
    pdf.ln(5)
    headers = ["Date", "P1", "P2", "P3", "Mem", "Post", "Calc", "Infra", "Cost"]
    pdf.set_fill_color(40, 116, 166); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 11)
    for h in headers: pdf.cell(31, 10, h, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", '', 11)
    history = df_m[df_m['name'] == row['name']].copy()
    fill = False
    for _, m in history.tail(10).iterrows():
        pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(31, 10, str(m.get('visit_date',''))[:10], 1, 0, 'C', True)
        for f in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared']:
            is_checked = format_to_check(m.get(f,'')) == "✅"
            if is_checked:
                pdf.set_font('ZapfDingbats', '', 11); pdf.cell(31, 10, '4', 1, 0, 'C', True); pdf.set_font('Arial', '', 11)
            else: pdf.cell(31, 10, "-", 1, 0, 'C', True)
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C', True)
        pdf.ln(); fill = not fill
    return bytes(pdf.output())

# --- 4. تحميل البيانات ومعالجة المواعيد (تم ضبط التنسيق 2026-01-25) ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

last_v_info = {}

if not df_m.empty:
    # تنظيف الأسماء لضمان المطابقة
    df_m['name'] = df_m['name'].astype(str).str.strip()
    df_c['name'] = df_c['name'].astype(str).str.strip()
    
    # دالة معالجة التواريخ المحسنة بناءً على التنسيق المذكور
    def parse_date(val):
        val = str(val).strip()
        if not val or val == "" or val == "nan": return pd.NaT
        # تجربة التنسيق الأساسي 2026-01-25 أولاً
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
            try: return pd.to_datetime(val, format=fmt)
            except: continue
        return pd.to_datetime(val, errors='coerce')

    df_m['v_date_dt'] = df_m['visit_date'].apply(parse_date)
    # الفلترة لإزالة القيم الفارغة قبل الترتيب
    valid_m = df_m.dropna(subset=['v_date_dt']).sort_values(by='v_date_dt', ascending=True)
    
    for name in valid_m['name'].unique():
        user_history = valid_m[valid_m['name'] == name]
        if not user_history.empty:
            last_row = user_history.iloc[-1].to_dict()
            s_val = str(last_row.get('special_date', "")).strip()
            last_row['spec_dt_clean'] = parse_date(s_val)
            last_v_info[name] = last_row

if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("💧 Healthy Water Management")
    pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
    if st.sidebar.button("دخول"):
        if pwd == "HgM18082019$&)": st.session_state.auth = "admin"; st.rerun()
        else: st.error("الباسورد غلط!")
    st.stop()

menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "إضافة عميل جديد"])

# --- 5. الصفحات ---

if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    search = st.text_input("ابحث عن عميل بالاسم أو المنطقة...")
    filtered_df = df_c[df_c['name'].str.contains(search, na=False) | df_c['area'].str.contains(search, na=False)] if search else df_c

    for idx, r in filtered_df.iterrows():
        name = r['name']
        last_v = last_v_info.get(name, {})
        next_d, last_visit_date = None, None
        
        if last_v:
            if pd.notnull(last_v['v_date_dt']):
                last_visit_date = last_v['v_date_dt'].date()
            
            spec_dt = last_v.get('spec_dt_clean')
            if pd.notnull(spec_dt):
                next_d = spec_dt.date()
            elif last_visit_date:
                try:
                    cycle = int(float(str(r.get('maintenance_cycle', 3)).strip()))
                except:
                    cycle = 3
                next_d = last_visit_date + timedelta(days=cycle * 30)

        status_color = get_status_color(next_d, r.get('status', ''))
        anchor_name = name.replace(" ", "_")
        st.markdown(f'<div id="{anchor_name}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="padding:12px; border-radius:8px; margin-bottom:10px; background-color:#ffffff; border-right:15px solid {status_color}; border-left:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <h4 style="margin:0; color:#333;">👤 {name} 
                <span style="font-size:12px; color:red;">{" (استثنائي: " + str(next_d) + ")" if next_d and pd.notnull(last_v.get('spec_dt_clean')) else ""}</span></h4>
                <p style="margin:0; font-size:14px; color:#666;">📍 {r.get('area','')} | 📞 {r.get('phone','')} | الموعد القادم: <b>{next_d if next_d else 'غير محدد'}</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("فتح التفاصيل وسجل الصيانات"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                st.write(f"**آخر زيارة:** {last_visit_date if last_visit_date else 'لا يوجد سجل'}")
                st.write(f"**الموعد القادم:** :blue[{next_d if next_d else 'غير محدد'}]")
                loc = r.get('location','')
                if loc: st.markdown(f"🗺️ **اللوكيشن:** [اضغط هنا لفتح الخريطة]({loc})")
                
                st.write("**تواصل:**")
                for p in ['phone', 'phone_1', 'phone_2', 'phone_3', 'phone_4']:
                    num = str(r.get(p,'')).strip()
                    if num and num not in ["nan", "", "0.0"]:
                        st.markdown(f"""
                        <div style="margin-bottom:5px;">
                            <span style="font-weight:bold;">📞 {num}:</span> 
                            <a href="tel:{num}" style="text-decoration:none; background:#28a745; color:white; padding:2px 8px; border-radius:4px; font-size:12px;">اتصال</a>
                            <a href="https://wa.me/2{num}" style="text-decoration:none; background:#25d366; color:white; padding:2px 8px; border-radius:4px; font-size:12px;">واتساب</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.write("---")
                if st.button("🗑️ حذف العميل", key=f"del_cust_{idx}"):
                    st.error(f"⚠️ هل أنت متأكد من حذف العميل {name}؟")
                    if st.button("نعم، احذف", key=f"conf_del_cust_{idx}"):
                        execute_gsheet_action("delete", "Customers", row_index=idx+2)
                        st.cache_data.clear()
                        st.rerun()

            with c2:
                history = df_m[df_m['name'] == name].copy()
                history['v_date_dt'] = history['visit_date'].apply(parse_date)
                history = history.sort_values(by='v_date_dt', ascending=False)
                
                if not history.empty:
                    st.write("**سجل الزيارات (الأحدث أولاً):**")
                    for h_idx, h_row in history.head(10).iterrows():
                        parts = [p for p in ['P1','P2','P3','membrane','post_carbon','Calcite','infrared'] if format_to_check(h_row[p]) == "✅"]
                        shamaat_text = " | ".join(parts) if parts else "لم يتم تغيير شمعات"
                        
                        st.markdown(f"""
                        <div style="background:#f9f9f9; padding:10px; border-radius:5px; margin-bottom:10px; border-left:5px solid #007bff; font-size:13px;">
                            <b>📅 {h_row['visit_date']}</b> | <b style="color:green;">💰 {h_row['amount']} ج.م</b><br>
                            🛠️ {shamaat_text}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.download_button("📥 تحميل PDF", generate_safe_pdf(r, df_m), f"{name}.pdf", key=f"pdf_down_{idx}")

elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    today = datetime.now().date()
    sched_list = []
    for _, r in df_c.iterrows():
        lv = last_v_info.get(r['name'], {})
        nd = None
        if lv:
            sd = lv.get('spec_dt_clean')
            if pd.notnull(sd): 
                nd = sd.date()
            elif pd.notnull(lv.get('v_date_dt')):
                try:
                    cycle = int(float(str(r.get('maintenance_cycle', 3)).strip()))
                except:
                    cycle = 3
                nd = (lv['v_date_dt'] + timedelta(days=cycle*30)).date()
            
            if nd:
                sched_list.append({'name': r['name'], 'date': nd, 'area': r.get('area','')})
    
    if sched_list:
        sdf = pd.DataFrame(sched_list)
        for i in range(7):
            curr = today + timedelta(days=i)
            st.subheader(f"{get_arabic_day(curr)} ({curr})")
            day_res = sdf[sdf['date'] == curr]
            if not day_res.empty:
                for _, row in day_res.iterrows():
                    st.markdown(f"🔹 **[{row['name']}](بيانات_العملاء#{row['name'].replace(' ','_')})** | 📍 {row['area']}")
            else: st.write(":grey[لا توجد مواعيد]")

elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("complete_m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        col1, col2 = st.columns(2)
        v_date = col1.date_input("تاريخ الزيارة")
        s_date = col2.date_input("موعد استثنائي القادم (اختياري)", value=None)
        st.write("---")
        st.subheader("الشمعات التي تم تغييرها")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
        calc = c3.checkbox("Calcite"); infra = c3.checkbox("Infrared")
        st.write("---")
        other_item = st.selectbox("إضافة قطعة غيار أخرى", ["لا يوجد"] + (df_inv['item_name'].tolist() if not df_inv.empty else []))
        amount = st.number_input("المبلغ المحصل", min_value=0.0)
        notes = st.text_area("ملاحظات الزيارة")
        if st.form_submit_button("حفظ البيانات"):
            new_data = [name, str(v_date), p1, p2, p3, mem, post, calc, infra, other_item, amount, notes, str(s_date) if s_date else "", ""]
            if execute_gsheet_action("append", "Maintenance", data=new_data):
                st.success("تم الحفظ بنجاح ✅")
                st.cache_data.clear()
                st.rerun()

elif menu == "المصروفات والحسابات 💸":
    st.header("💸 سجل المصروفات")
    with st.form("exp_form_full"):
        e_date = st.date_input("التاريخ")
        col_e1, col_e2 = st.columns(2)
        trans = col_e1.number_input("انتقالات", min_value=0.0)
        sund = col_e2.number_input("نثريات", min_value=0.0)
        mon_exp = col_e1.number_input("مصروفات شهرية", min_value=0.0)
        sal = col_e2.number_input("رواتب", min_value=0.0)
        if st.form_submit_button("حفظ"):
            if execute_gsheet_action("append", "Expenses", data=[str(e_date), trans, sund, mon_exp, sal]):
                st.success("تم الحفظ")
                st.cache_data.clear()
    if not df_exp.empty:
        st.dataframe(df_exp, use_container_width=True)

elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح")
    if not df_m.empty and not df_exp.empty:
        df_m['date_only'] = df_m['v_date_dt'].dt.date
        income = df_m.groupby('date_only')['amount'].sum().reset_index().rename(columns={'date_only':'date', 'amount':'income'})
        df_exp['date_only'] = pd.to_datetime(df_exp['date'], errors='coerce').dt.date
        expense = df_exp.groupby('date_only')[['transportation','sundries','monthly_expensess','salaries']].sum().sum(axis=1).reset_index(name='expense')
        merged = pd.merge(income, expense, on='date', how='outer').fillna(0)
        merged['profit'] = merged['income'] - merged['expense']
        st.dataframe(merged.sort_values('date', ascending=False), use_container_width=True)

elif menu == "إضافة عميل جديد":
    st.header("➕ تسجيل عميل جديد")
    with st.form("add_full_cust"):
        c_name = st.text_input("الاسم الكامل")
        c_phone = st.text_input("الموبايل")
        c_area = st.text_input("المنطقة")
        c_address = st.text_input("العنوان")
        c_setup = st.date_input("تاريخ التركيب")
        c_cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        c_status = st.selectbox("الحالة", ["نشط", "راكد"])
        if st.form_submit_button("إضافة"):
            if execute_gsheet_action("append", "Customers", data=[c_name, c_phone, c_area, c_address, str(c_setup), c_cycle, c_status]):
                st.success("تم إضافة العميل")
                st.cache_data.clear()

elif menu == "المخزن 📦":
    st.header("📦 المخزن")
    st.dataframe(df_inv, use_container_width=True)

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ النواقص")
    shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
    st.table(shortage[['item_name', 'quantity', 'min_limit']])
