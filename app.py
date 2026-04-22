import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# الرابط للقراءة من صفحة الفورم الجديدة
CLIENTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة تحميل البيانات المحدثة ---
def load_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.read_csv(StringIO(res.text))
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data(CLIENTS_URL)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

# --- 5. تسجيل عميل جديد ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # ميكانيكا الـ ID الآمنة
                try:
                    new_id = 101 if df_c.empty else int(df_c.iloc[:, 1].max()) + 1
                except:
                    new_id = 101

                form_data = {
                    "entry.1872338545": new_id,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1332478222": loc,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()),
                    "entry.1371491317": "لم تتم"
                }
                headers = {'Referer': FORM_URL, 'User-Agent': "Mozilla/5.0"}
                try:
                    requests.post(FORM_URL, data=form_data, headers=headers)
                    st.success(f"تم إرسال العميل {name} بنجاح!")
                    st.balloons()
                except:
                    st.error("خطأ في الإرسال")

# --- 6. عرض البيانات (حل مشكلة الـ IndexError) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    if df_c.empty or len(df_c.columns) < 3:
        st.info("لا توجد بيانات مسجلة بعد، أو الشيت لا يزال في مرحلة التهيئة.")
    else:
        search = st.text_input("🔍 بحث بالاسم")
        
        # البحث عن الأعمدة بالاسم بدلاً من الرقم لتجنب IndexError
        # جوجل فورم بتسمي الأعمدة بنفس أسئلة الفورم
        col_name = [c for c in df_c.columns if 'اسم العميل' in c][0]
        col_phone = [c for c in df_c.columns if 'الأرقام' in c][0]
        
        f_df = df_c.copy()
        if search:
            f_df = f_df[f_df[col_name].astype(str).str.contains(search, na=False)]

        for i, row in f_df.iterrows():
            with st.expander(f"👤 {row[col_name]}"):
                st.write(f"📞 هاتف: {row[col_phone]}")
                st.write(f"🏠 العنوان: {row.get('العنوان', 'غير مسجل')}")
                st.link_button("اتصال", f"tel:{row[col_phone]}")
