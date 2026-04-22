import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# رابط الشيت الخاص بك (تم تحديثه)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30/edit?usp=sharing"

# --- 2. الاتصال بـ Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# تعريف الأعمدة الأساسية للطوارئ
C_COLS = ['id', 'اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'الموقع', 'دورة الصيانة', 'تاريخ الزيارة القادمة', 'تاريخ آخر زيارة']
H_COLS = ['id_زيارة', 'id_عميل', 'تاريخ الزيارة', 'p1', 'p2', 'p3', 'ممبرين', 'بوست كاربون', 'كالسيت', 'انفر ريد', 'اخري', 'المبلغ']

def load_data():
    try:
        # محاولة قراءة البيانات (تأكد من عدم وجود مسافات في أسماء Sheets)
        c_df = conn.read(spreadsheet=SHEET_URL, worksheet="Customers", ttl=0)
        h_df = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl=0)
        return c_df, h_df
    except Exception as e:
        st.error(f"خطأ في الوصول للصفحات: {e}")
        return pd.DataFrame(columns=C_COLS), pd.DataFrame(columns=H_COLS)

# تحميل البيانات
df_c, df_h = load_data()

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water - قاعدة البيانات")
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات العام"])

# --- 5. تسجيل عميل جديد (تفريغ تلقائي) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_client", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام (فاصلة بينهم)")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", min_value=1, value=3)
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                new_id = 101 if df_c.empty or df_c['id'].isnull().all() else int(df_c['id'].max()) + 1
                new_row = pd.DataFrame([{
                    'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 
                    'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 
                    'تاريخ الزيارة القادمة': str(datetime.now().date()), 'تاريخ آخر زيارة': 'لم تتم'
                }])
                updated_df = pd.concat([df_c, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Customers", data=updated_df)
                st.success(f"تم الحفظ في Google Sheets بكود {new_id}")
                st.rerun()

# --- 6. بيانات العملاء ---
elif menu == "بيانات العملاء":
    st.header("👥 ملفات العملاء")
    search = st.text_input("🔎 ابحث بالاسم أو الرقم")
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]

    for i, row in f_df.iterrows():
        with st.expander(f"👤 {row['id']} - {row['اسم العميل']} ({row['المنطقه']})"):
            t1, t2, t3 = st.tabs(["📄 البيانات", "🔧 سجل الزيارات", "✏️ تعديل"])
            with t1:
                st.write(f"🏠 {row['العنوان']}")
                phone_list = str(row['الهواتف']).split(',')
                for p in phone_list:
                    p = p.strip()
                    if p:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"📞 {p}")
                        c2.link_button("اتصال", f"tel:{p}")
                        c3.link_button("واتساب", f"https://wa.me/2{p}")
                if "http" in str(row['الموقع']):
                    st.link_button("📍 فتح اللوكيشن", row['الموقع'])
            
            with t2:
                with st.form(f"v_{row['id']}", clear_on_submit=True):
                    v_date = st.date_input("تاريخ الزيارة")
                    st.write("**ترتيب الشمعات:**")
                    p1 = st.checkbox("P1")
                    p2 = st.checkbox("P2")
                    p3 = st.checkbox("P3")
                    mem = st.checkbox("ممبرين")
                    post = st.checkbox("بوست كاربون")
                    calc = st.checkbox("كالسيت")
                    infra = st.checkbox("انفرا ريد")
                    other = st.text_input("أخرى")
                    price = st.number_input("المبلغ", min_value=0)
                    if st.form_submit_button("✅ حفظ الزيارة"):
                        v_id = 1 if df_h.empty or df_h['id_زيارة'].isnull().all() else int(df_h['id_زيارة'].max()) + 1
                        new_v = pd.DataFrame([{
                            'id_زيارة': v_id, 'id_عميل': row['id'], 'تاريخ الزيارة': str(v_date),
                            'p1': '✅' if p1 else '', 'p2': '✅' if p2 else '', 'p3': '✅' if p3 else '',
                            'ممبرين': '✅' if mem else '', 'بوست كاربون': '✅' if post else '',
                            'كالسيت': '✅' if calc else '', 'انفر ريد': '✅' if infra else '',
                            'اخري': other, 'المبلغ': price
                        }])
                        conn.update(spreadsheet=SHEET_URL, worksheet="History", data=pd.concat([df_h, new_v], ignore_index=True))
                        # تحديث الموعد القادم
                        df_c.loc[df_c['id'] == row['id'], 'تاريخ الزيارة القادمة'] = str(v_date + timedelta(days=int(row['دورة الصيانة'])*30))
                        conn.update(spreadsheet=SHEET_URL, worksheet="Customers", data=df_c)
                        st.success("تم التحديث في جوجل شيت!")
                        st.rerun()

# --- خروج ---
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
