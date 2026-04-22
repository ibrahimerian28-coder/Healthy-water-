import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الخاص بالشيت بتاعك
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"

# --- تعديل أسماء الصفحات بناءً على الصور الجديدة ---
# صفحة العملاء أصبحت الآن Form Responses 1 لأن الفورم بعت عليها
CLIENTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201"
# صفحة التاريخ لسه زي ما هي History
HISTORY_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=History"

# رابط إرسال الفورم (اللي استخدمناه المرة اللي فاتت)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة تحميل البيانات ---
def load_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.read_csv(StringIO(res.text))
            # تنظيف البيانات من أي أعمدة فارغة تماماً
            return df.dropna(how='all', axis=1).dropna(how='all', axis=0)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data(CLIENTS_URL)
df_h = load_data(HISTORY_URL)

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

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

# --- 5. تسجيل عميل جديد ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_client_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # ميكانيكا الـ ID
                new_id = 101 if df_c.empty else int(df_c.iloc[:, 1].max()) + 1
                
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
                    st.success(f"تم إرسال العميل {name} لصفحة Form Responses 1 بنجاح!")
                    st.balloons()
                except:
                    st.error("فشل في الإرسال")

# --- 6. عرض بيانات العملاء من التبويب الجديد ---
elif menu == "بيانات العملاء":
    st.header("👥 العملاء في التبويب الجديد")
    if df_c.empty:
        st.info("لا توجد بيانات في Form Responses 1")
    else:
        search = st.text_input("🔍 بحث بالاسم")
        f_df = df_c.copy()
        
        # ملاحظة: في شيت الفورم، أول عمود بيكون Timestamp، فالاسم بيكون في العمود التاني
        name_col = f_df.columns[2] # عمود اسم العميل
        phone_col = f_df.columns[3] # عمود الهواتف
        
        if search:
            f_df = f_df[f_df[name_col].astype(str).str.contains(search, na=False)]

        for i, row in f_df.iterrows():
            with st.expander(f"👤 {row[name_col]}"):
                st.write(f"📞 هاتف: {row[phone_col]}")
                st.write(f"🏠 العنوان: {row[f_df.columns[4]]}")
                st.link_button("اتصال", f"tel:{row[phone_col]}")
