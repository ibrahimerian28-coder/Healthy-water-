import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# روابط القراءة (تأكد من اسم الصفحة في الشيت)
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# ملاحظة: غير "Customers" لـ "Form Responses 1" لو البيانات بتنزل في صفحة الفورم الجديدة
CLIENTS_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201"

# رابط الإرسال
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظائف البيانات ---
def load_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data(CLIENTS_READ_URL)

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

# --- 4. تسجيل عميل جديد (الإرسال المطور) ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

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
                # ميكانيكا الـ ID (تجاوز لو الشيت فاضي)
                try:
                    new_id = 101 if df_c.empty else int(df_c.iloc[:,1].max()) + 1
                except:
                    new_id = 101

                # تجهيز البيانات
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
                
                # إضافة Header لإيهام جوجل إنه متصفح حقيقي
                headers = {'Referer': FORM_URL, 'User-Agent': "Mozilla/5.0"}
                
                try:
                    response = requests.post(FORM_URL, data=form_data, headers=headers)
                    # جوجل فورم بترجع 200 حتى لو الصفحة ظهرت، المهم البيانات تتبعت
                    st.success(f"تم إرسال الطلب للعميل: {name}")
                    st.info("افتح شيت الإكسيل الآن للتأكد من وصول البيانات")
                    st.balloons()
                except Exception as e:
                    st.error(f"فشل الاتصال: {e}")
            else:
                st.warning("برجاء إدخال البيانات")

# --- 5. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 العملاء")
    if df_c.empty:
        st.info("لا توجد بيانات حالياً في صفحة Form Responses 1")
    else:
        st.dataframe(df_c)
