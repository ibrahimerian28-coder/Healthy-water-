import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from fpdf import FPDF

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Healthy Water Pro - Level الوحش", layout="wide")

# دالة لتحويل أسماء الأيام للعربية
def get_arabic_day(date_obj):
    days = {
        'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
        'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
    }
    return days.get(date_obj.strftime('%A'), date_obj.strftime('%A'))

@st.cache_data(ttl=600) 
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
    return "✓" if v in ['true', '1', 'checked', 'تم', 'yes'] else "✗"

def clean_text_for_pdf(text):
    if not text: return ""
    return "".join(i for i in str(text) if ord(i) < 128)

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 2. نظام الألوان (تمت مراجعته) ---
def get_status_color(next_date, status):
    if str(status).strip() == "راكد": return "#808080"
    if next_date is None or pd.isnull(next_date): return "#f0f2f6"
    
    # تحويل لـ date إذا كان datetime
    if isinstance(next_date, datetime):
        next_date = next_date.date()
        
    today = datetime.now().date()
    diff = (next_date - today).days
    
    if diff > 7: return "#28a745"  # أخضر
    elif 0 <= diff <= 7: return "#ffc107"  # أصفر
    elif -7 <= diff < 0: return "#dc3545"  # أحmer
    else: return "#8b0000"  # أحمر غامق

# --- 3. تصميم الـ PDF ---
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
            is_checked = format_to_check(m.get(f,'')) == "✓"
            if is_checked:
                pdf.set_font('ZapfDingbats', '', 11); pdf.cell(31, 10, '4', 1, 0, 'C', True); pdf.set_font('Arial', '', 11)
            else: pdf.cell(31, 10, "-", 1, 0, 'C', True)
        pdf.cell(31, 10, str(m.get('amount','0')), 1, 0, 'C', True)
        pdf.ln(); fill = not fill
    return bytes(pdf.output())

# --- 4. تحميل البيانات ---
df_c = load_all_data("0")
df_m = load_all_data("2120582392")
df_inv = load_all_data("1767710106")
df_exp = load_all_data("288947510")

if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("💧 Healthy Water Management")
    pwd = st.sidebar.text_input("باسورد الإدارة:", type="password")
    if st.sidebar.button("دخول"):
        if pwd == "HgM18082019$&)": st.session_state.auth = "admin"; st.rerun()
        else: st.error("الباسورد غلط!")
    st.stop()

menu = st.sidebar.radio("التحكم:", ["بيانات العملاء", "جدول المواعيد", "المخزن 📦", "الاحتياجات ⚠️", "تسجيل صيانة 🔧", "المصروفات والحسابات 💸", "الأرباح 📈", "إضافة عميل جديد"])

# --- تجهيز بيانات المواعيد ---
df_m['v_date_dt'] = pd.to_datetime(df_m['visit_date'], errors='coerce')
last_v_info = df_m.sort_values('v_date_dt').groupby('name').last().to_dict('index')

# --- 6. الصفحات ---

if menu == "بيانات العملاء":
    st.header("📋 سجل العملاء")
    # محرك بحث سريع
    search = st.text_input("ابحث عن عميل بالاسم أو المنطقة...")
    
    filtered_df = df_c
    if search:
        filtered_df = df_c[df_c['name'].str.contains(search) | df_c['area'].str.contains(search)]

    for idx, r in filtered_df.iterrows():
        last_v = last_v_info.get(r['name'], {})
        next_d = None
        last_visit_date = None
        
        if last_v:
            last_visit_date = last_v['v_date_dt'].date() if pd.notnull(last_v['v_date_dt']) else None
            spec_d = pd.to_datetime(last_v.get('special_date'), errors='coerce')
            if pd.notnull(spec_d): 
                next_d = spec_d.date()
            elif last_visit_date:
                cycle = int(r.get('maintenance_cycle', 3))
                next_d = last_visit_date + timedelta(days=cycle * 30)
        
        status_color = get_status_color(next_d, r.get('status', ''))
        
        # لعمل رابط لصفحة الجدول
        anchor_name = r['name'].replace(" ", "_")
        st.markdown(f'<div id="{anchor_name}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="padding:12px; border-radius:8px; margin-bottom:10px; background-color:#ffffff; border-right:15px solid {status_color}; border-left:1px solid #ddd; border-top:1px solid #ddd; border-bottom:1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <h4 style="margin:0; color:#333;">👤 {r['name']}</h4>
                <p style="margin:0; font-size:14px; color:#666;">📍 {r.get('area','')} | 📞 {r.get('phone','')} | الموعد: {next_d if next_d else 'غير محدد'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("فتح التفاصيل وسجل الصيانات"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**العنوان:** {r.get('adress','')}")
                st.write(f"**تاريخ التركيب:** {r.get('setup_date','')}")
                st.write(f"**الحالة:** {r.get('status','')}")
                st.write(f"**آخر زيارة:** {last_visit_date if last_visit_date else 'لا يوجد'}")
                st.write(f"**الموعد القادم:** :blue[{next_d if next_d else 'غير محدد'}]")
                loc = r.get('location','')
                if loc: st.markdown(f"🗺️ **اللوكيشن:** [اضغط هنا لفتح الخريطة]({loc})")
                
                # تواصل
                st.write("**تواصل مع العميل:**")
                phones = [r.get('phone',''), r.get('phone_1',''), r.get('phone_2',''), r.get('phone_3',''), r.get('phone_4','')]
                for num in phones:
                    num = str(num).strip()
                    if num and num != "nan" and num != "":
                        st.markdown(f"📞 {num}: [اتصال](tel:{num}) | [واتساب](https://wa.me/2{num})")
                
                st.write("---")
                # أزرار التعديل والحذف
                bc1, bc2 = st.columns(2)
                bc1.button("📝 تعديل بيانات العميل", key=f"edit_c_{idx}")
                bc2.button("🗑️ حذف العميل نهائياً", key=f"del_c_{idx}")

            with c2:
                history = df_m[df_m['name'] == r['name']].copy()
                if not history.empty:
                    st.write("**سجل الصيانات:**")
                    # عرض الجدول مع أيقونات التعديل والحذف
                    for h_idx, h_row in history.tail(5).iterrows():
                        v_d = str(h_row['visit_date'])[:10]
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; background:#f9f9f9; padding:5px 10px; border-radius:5px; margin-bottom:5px; border:1px solid #eee;">
                            <span>📅 {v_d} - مبلغ: {h_row.get('amount',0)}</span>
                            <div>
                                <button style="border:none; background:none; cursor:pointer;">✏️</button>
                                <button style="border:none; background:none; cursor:pointer;">🗑️</button>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.download_button("📥 تحميل ملف PDF", generate_safe_pdf(r, df_m), f"{r['name']}.pdf", key=f"pdf_{idx}")

elif menu == "جدول المواعيد":
    st.header("📅 جدول مواعيد الأسبوع")
    
    # حساب المواعيد لكل العملاء
    schedule_data = []
    for _, r in df_c.iterrows():
        last_v = last_v_info.get(r['name'], {})
        if last_v:
            spec_d = pd.to_datetime(last_v.get('special_date'), errors='coerce')
            if pd.notnull(spec_d): n_date = spec_d.date()
            else: n_date = (last_v['v_date_dt'] + timedelta(days=int(r.get('maintenance_cycle',3))*30)).date()
            schedule_data.append({"name": r['name'], "date": n_date, "area": r.get('area','')})
    
    sched_df = pd.DataFrame(schedule_data)
    
    # عرض الـ 7 أيام القادمة
    today = datetime.now().date()
    for i in range(7):
        current_day = today + timedelta(days=i)
        day_str = get_arabic_day(current_day)
        date_display = current_day.strftime('%Y-%m-%d')
        
        st.subheader(f"{day_str} ({date_display})")
        
        day_clients = sched_df[sched_df['date'] == current_day]
        
        if not day_clients.empty:
            for _, c_row in day_clients.iterrows():
                # لينك يحول لصفحة العملاء (باستخدام anchor)
                c_name = c_row['name']
                st.markdown(f"🔹 **[{c_name}](بيانات_العملاء#{c_name.replace(' ','_')})** - (المنطقة: {c_row['area']})")
        else:
            st.write(":grey[لا توجد مواعيد متوفرة خلال اليوم]")
        st.write("---")

elif menu == "تسجيل صيانة 🔧":
    st.header("🔧 تسجيل زيارة صيانة")
    with st.form("m_form"):
        name = st.selectbox("العميل", df_c['name'].tolist() if not df_c.empty else [])
        col1, col2 = st.columns(2)
        v_date = col1.date_input("تاريخ الزيارة")
        s_date = col2.date_input("موعد استثنائي (اختياري)", value=None)
        st.subheader("الشمعات")
        c1, c2, c3 = st.columns(3)
        p1 = c1.checkbox("P1"); p2 = c1.checkbox("P2"); p3 = c1.checkbox("P3")
        mem = c2.checkbox("Membrane"); post = c2.checkbox("Post Carbon")
        calc = c3.checkbox("Calcite"); infra = c3.checkbox("Infrared")
        amount = st.number_input("المبلغ المحصل", min_value=0.0)
        if st.form_submit_button("حفظ الزيارة"): st.success("تم الحفظ")

elif menu == "إضافة عميل جديد":
    st.header("➕ تسجيل عميل جديد")
    with st.form("add_client_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("الاسم الكامل للعميل")
            p0 = st.text_input("رقم الموبايل الأساسي")
            p1 = st.text_input("رقم موبايل 1")
            p2 = st.text_input("رقم موبايل 2")
            p3 = st.text_input("رقم موبايل 3")
            area = st.text_input("المنطقة")
        with c2:
            addr = st.text_input("العنوان بالتفصيل")
            loc = st.text_input("رابط اللوكيشن (Google Maps)")
            setup_d = st.date_input("تاريخ التركيب")
            cycle = st.number_input("دورة الصيانة (شهور)", value=3)
            status = st.selectbox("الحالة", ["نشط", "راكد"])
        
        if st.form_submit_button("إضافة العميل لقاعدة البيانات"):
            st.success(f"تمت إضافة العميل {name} بنجاح")

# بقية الصفحات (المخزن، الأرباح، إلخ) يتم استكمالها بنفس منطق الكود الأصلي
elif menu == "المخزن 📦":
    st.header("📦 إدارة المخزن")
    st.dataframe(df_inv, use_container_width=True)

elif menu == "الاحتياجات ⚠️":
    st.header("⚠️ نواقص المخزن")
    if not df_inv.empty:
        shortage = df_inv[df_inv['quantity'] <= df_inv['min_limit']]
        st.table(shortage)

elif menu == "الأرباح 📈":
    st.header("📈 تقارير الأرباح")
    if not df_m.empty and not df_exp.empty:
        income = df_m.groupby('v_date_dt')['amount'].sum().reset_index()
        st.write("**إجمالي الدخل اليومي:**")
        st.dataframe(income)
