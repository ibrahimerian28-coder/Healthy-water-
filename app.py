import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# رابط الشيت بتاعك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30/edit?usp=sharing"

# --- 2. الاتصال بـ Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet)

# تحميل البيانات
try:
    df_c = load_data("Customers")
    df_h = load_data("History")
except:
    st.error("تأكد من تسمية الصفحات في Google Sheets بـ Customers و History")
    st.stop()

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water - قاعدة البيانات الآمنة")
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات العام"])

# --- 5. تسجيل عميل جديد ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_client", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام (فاصلة بينهم)")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        if st.form_submit_button("حفظ"):
            new_id = 101 if df_c.empty or df_c['id'].isnull().all() else int(df_c['id'].max()) + 1
            new_row = pd.DataFrame([{
                'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 
                'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 
                'تاريخ الزيارة القادمة': str(datetime.now().date()), 'تاريخ آخر زيارة': 'لم تتم'
            }])
            updated_df = pd.concat([df_c, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, worksheet="Customers", data=updated_df)
            st.success(f"تم الحفظ في Google Sheets بكود {new_id}")
            st.balloons()

# --- 6. بيانات العملاء والزيارات ---
elif menu == "بيانات العملاء":
    st.header("👥 ملفات العملاء")
    search = st.text_input("🔎 ابحث بالاسم أو الرقم")
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]

    for i, row in f_df.iterrows():
        with st.expander(f"👤 {row['id']} - {row['اسم العميل']}"):
            t1, t2 = st.tabs(["📄 البيانات", "🔧 الصيانة"])
            with t1:
                st.write(f"🏠 {row['العنوان']} | 📅 ميعادك القادم: {row['تاريخ الزيارة القادمة']}")
                for p in str(row['الهواتف']).split(','):
                    p = p.strip()
                    c1, c2 = st.columns(2)
                    c1.link_button(f"📞 اتصال {p}", f"tel:{p}")
                    c2.link_button(f"💬 واتساب", f"https://wa.me/2{p}")
            
            with t2:
                with st.form(f"v_{row['id']}", clear_on_submit=True):
                    v_date = st.date_input("تاريخ الزيارة")
                    c1, c2, c3 = st.columns(3)
                    p1 = c1.checkbox("P1")
                    p2 = c1.checkbox("P2")
                    p3 = c1.checkbox("P3")
                    mem = c2.checkbox("ممبرين")
                    post = c2.checkbox("بوست")
                    calc = c3.checkbox("كالسيت")
                    infra = c3.checkbox("انفرا")
                    other = st.text_input("أخرى")
                    price = st.number_input("المبلغ", min_value=0)
                    
                    if st.form_submit_button("حفظ الزيارة"):
                        v_id = 1 if df_h.empty or df_h['id_زيارة'].isnull().all() else int(df_h['id_زيارة'].max()) + 1
                        new_v = pd.DataFrame([{
                            'id_زيارة': v_id, 'id_عميل': row['id'], 'تاريخ الزيارة': str(v_date),
                            'p1': '✅' if p1 else '', 'p2': '✅' if p2 else '', 'p3': '✅' if p3 else '',
                            'ممبرين': '✅' if mem else '', 'بوست كاربون': '✅' if post else '',
                            'كالسيت': '✅' if calc else '', 'انفر ريد': '✅' if infra else '',
                            'اخري': other, 'المبلغ': price
                        }])
                        # تحديث شيت التاريخ
                        updated_h = pd.concat([df_h, new_v], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="History", data=updated_h)
                        # تحديث ميعاد العميل في شيت العملاء
                        df_c.loc[df_c['id'] == row['id'], 'تاريخ الزيارة القادمة'] = str(v_date + timedelta(days=int(row['دورة الصيانة'])*30))
                        conn.update(spreadsheet=SHEET_URL, worksheet="Customers", data=df_c)
                        st.success("تم التحديث في جوجل شيت!")
                        st.rerun()

# --- خروج ---
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
