import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Database", layout="wide")

# الرابط اللي هتاخده من موقع SheetDB
API_URL = "https://sheetdb.io/api/v1/25ojnsldblcqy"

# --- 2. وظيفة تحميل البيانات ---
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
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

# --- 5. تسجيل عميل جديد (حفظ حقيقي ومباشر) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ في الإكسيل"):
            if name and phones:
                # حساب الـ ID
                new_id = 101 if df_c.empty else int(df_c.iloc[:,0].astype(int).max()) + 1
                
                # تجهيز البيانات (لازم الأسماء تطابق أول صف في الشيت)
                new_data = {
                    "data": [{
                        "id": new_id,
                        "اسم العميل": name,
                        "الهواتف": phones,
                        "العنوان": addr,
                        "المنطقه": area,
                        "دورة الصيانة": cycle,
                        "تاريخ الزيارة القادمة": str(datetime.now().date()),
                        "تاريخ آخر زيارة": "لم تتم"
                    }]
                }
                
                # الإرسال لـ SheetDB
                res = requests.post(API_URL, json=new_data)
                if res.status_code == 201:
                    st.success(f"مبروك يا هندسة! العميل {name} اتسجل في الشيت")
                    st.balloons()
                else:
                    st.error("فشل الحفظ، تأكد من رابط API")
            else:
                st.warning("دخل الاسم والرقم")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 العملاء في الشيت")
    if df_c.empty:
        st.info("الشيت فاضي أو الرابط مش مظبوط")
    else:
        # عرض البيانات بشكل منظم
        for i, row in df_c.iterrows():
            with st.expander(f"👤 {row['اسم العميل']}"):
                st.write(f"📞 هاتف: {row['الهواتف']}")
                st.write(f"🏠 العنوان: {row['العنوان']}")
                st.link_button("اتصال", f"tel:{row['الهواتف']}")
