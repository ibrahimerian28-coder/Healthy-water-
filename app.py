import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الأساسي للشيت (للقراءة)
url = "https://docs.google.com/spreadsheets/d/1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30/edit?usp=sharing"
# رابط الفورم (للإرسال)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة جلب البيانات باستخدام الموصل الرسمي ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # قراءة التبويب المحدد بالاسم
        return conn.read(spreadsheet=url, worksheet="1292025701")
    except:
        # لو فشل، يقرأ الشيت الأساسي
        return conn.read(spreadsheet=url)

df_c = get_data()

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
    with st.form("final_rescue_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                payload = {
                    "entry.1872338545": str(datetime.now().timestamp()),
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1371491317": "لم تتم"
                }
                requests.post(FORM_URL, data=payload)
                st.success("✅ البيانات أرسلت! جاري التحديث...")
                st.cache_data.clear() # مسح الذاكرة المؤقتة فوراً
                st.rerun()

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

    if df_c is None or df_c.empty:
        st.info("لا توجد بيانات حالياً.")
    else:
        # عرض البيانات بجدول للتأكد
        with st.expander("📝 عرض الجدول المباشر"):
            st.write(df_c)

        search = st.text_input("🔍 بحث")
        for i, row in df_c.iterrows():
            try:
                # محاولة قراءة الأعمدة بالترتيب
                c_name = str(row.iloc[2])
                c_phone = str(row.iloc[3])
                if search.lower() in c_name.lower() or search in c_phone:
                    with st.expander(f"👤 {c_name}"):
                        st.write(f"📞 هاتف: {c_phone}")
                        st.link_button("📲 اتصال", f"tel:{c_phone}")
            except:
                continue
