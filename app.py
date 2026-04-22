import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط السحري للربط المباشر (تعديل الرابط ليقبل التصدير)
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
CLIENTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Customers"
HISTORY_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=History"

# --- 2. دالة جلب البيانات ---
def load_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# تحميل البيانات في بداية التطبيق
df_c = load_data(CLIENTS_URL)
df_h = load_data(HISTORY_URL)

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
        
        st.info("💡 ملاحظة: بعد الحفظ، سيتم توجيهك لصفحة البيانات للتأكيد.")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # ميكانيكا الحفظ المؤقت (لأنه لا يمكن الكتابة مباشرة عبر HTTP GET)
                st.warning("⚠️ لتمكين الحفظ المباشر، يرجى استخدام Google Forms أو Apps Script. حالياً يمكنك نسخ البيانات للشيت.")
                st.code(f"{name}, {phones}, {addr}, {area}, {cycle}")
            else:
                st.error("برجاء إدخال البيانات")

# --- 6. بيانات العملاء ---
elif menu == "بيانات العملاء":
    st.header("👥 ملفات العملاء")
    if df_c.empty:
        st.info("لا توجد بيانات حالياً في شيت Customers أو الرابط غير صحيح.")
    else:
        search = st.text_input("🔎 ابحث بالاسم أو الرقم")
        f_df = df_c.copy()
        if search:
            f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]

        for i, row in f_df.iterrows():
            with st.expander(f"👤 {row['id']} - {row['اسم العميل']} ({row['المنطقه']})"):
                st.write(f"🏠 العنوان: {row['العنوان']}")
                st.write(f"📅 الموعد القادم: {row['تاريخ الزيارة القادمة']}")
                
                # أزرار الاتصال
                p_list = str(row['الهواتف']).split(',')
                for p in p_list:
                    p = p.strip()
                    c1, c2 = st.columns(2)
                    c1.link_button(f"📞 اتصال {p}", f"tel:{p}")
                    c2.link_button(f"💬 واتساب", f"https://wa.me/2{p}")
