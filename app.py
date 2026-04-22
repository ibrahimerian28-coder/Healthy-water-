import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط القراءة من التبويب اللي جوجل عملته (Form Responses 1)
CLIENTS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201"
# رابط الإرسال للفورم
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة تحميل البيانات ---
def load_data():
    try:
        res = requests.get(CLIENTS_URL, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(StringIO(res.text))
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data()

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
                try:
                    # ميكانيكا الـ ID
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
                    st.success(f"تم تسجيل {name} بنجاح! انتظر ثواني وستظهر في القائمة.")
                    st.balloons()
                except:
                    st.error("خطأ في الاتصال بجوجل")
            else:
                st.warning("برجاء ملء الاسم والرقم")

# --- 6. عرض البيانات (الكود الآمن) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if df_c.empty or len(df_c.columns) < 4:
        st.info("لا توجد بيانات حالياً. يرجى تسجيل أول عميل.")
    else:
        search = st.text_input("🔍 بحث بالاسم")
        
        # طريقة آمنة للوصول للأعمدة بالترتيب وليس بالاسم
        # العمود 0: الوقت | العمود 1: ID | العمود 2: الاسم | العمود 3: الهاتف
        f_df = df_c.copy()
        
        try:
            name_col_idx = 2
            phone_col_idx = 3
            
            if search:
                f_df = f_df[f_df.iloc[:, name_col_idx].astype(str).str.contains(search, na=False)]

            for i, row in f_df.iterrows():
                client_name = row.iloc[name_col_idx]
                client_phone = row.iloc[phone_col_idx]
                
                with st.expander(f"👤 {client_name}"):
                    st.write(f"📞 هاتف: {client_phone}")
                    st.write(f"📍 المنطقة: {row.iloc[5] if len(row) > 5 else 'غير محدد'}")
                    st.link_button("📲 اتصال", f"tel:{client_phone}")
                    st.link_button("💬 واتساب", f"https://wa.me/2{client_phone}")
        except Exception as e:
            st.warning("هناك مشكلة في ترتيب أعمدة الشيت، تأكد من تسجيل عميل واحد على الأقل عبر التطبيق.")
