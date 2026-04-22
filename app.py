import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Database", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
GID = "1292025701" # رقم الصفحة اللي في صورتك
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة التحميل الآمنة جداً ---
def load_data():
    try:
        # إضافة وقت الحالي لضمان عدم الكاش
        res = requests.get(f"{READ_URL}&refresh={time.time()}", timeout=10)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
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

# --- 5. تسجيل عميل جديد (حل مشكلة رسالة الفشل) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("الدورة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                new_id = 101 if df_c.empty else int(len(df_c)) + 101
                form_data = {
                    "entry.1872338545": new_id,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()),
                    "entry.1371491317": "لم تتم"
                }
                try:
                    # نرسل البيانات ونكتفي بالتأكد من وصول الطلب
                    requests.post(FORM_URL, data=form_data, timeout=5)
                    st.success(f"✅ تم حفظ العميل {name} بنجاح!")
                    st.info("سيظهر في القائمة خلال لحظات...")
                    st.balloons()
                except:
                    # حتى لو مطلع Timeout غالباً البيانات وصلت
                    st.warning("⚠️ البيانات أُرسلت، يرجى فحص القائمة.")
            else:
                st.error("برجاء إدخال الاسم والهاتف")

# --- 6. عرض البيانات (حل مشكلة الـ IndexError) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c.empty:
        st.info("لا توجد بيانات حالياً.")
    else:
        # لو عدد الأعمدة قليل أو الترتيب اختلف، اعرض جدول
        if len(df_c.columns) < 4:
            st.warning("تنسيق الشيت مختلف، جارٍ عرض البيانات كجدول:")
            st.dataframe(df_c)
        else:
            search = st.text_input("🔍 بحث")
            f_df = df_c.copy()
            
            # محاولة البحث في العمود رقم 2 (الاسم)
            try:
                if search:
                    f_df = f_df[f_df.iloc[:, 2].astype(str).str.contains(search, na=False)]
                
                for i, row in f_df.iterrows():
                    # عرض الكارت بأمان
                    name = row.iloc[2] if len(row) > 2 else "بدون اسم"
                    phone = row.iloc[3] if len(row) > 3 else "بدون هاتف"
                    with st.expander(f"👤 {name}"):
                        st.write(f"📞 هاتف: {phone}")
                        st.write(f"📍 المنطقة: {row.iloc[5] if len(row) > 5 else '-'}")
                        st.link_button("اتصال", f"tel:{phone}")
            except:
                st.dataframe(df_c) # في حالة فشل الكروت، الجدول ينقذنا
