import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الخاص بك من Stein
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"
# اسم التبويب في الشيت
SHEET_NAME = "Form Responses 1"

# --- 2. وظيفة جلب البيانات ---
@st.cache_data(ttl=5) # تحديث البيانات كل 5 ثوانٍ
def load_data():
    try:
        res = requests.get(f"{API_URL}/{SHEET_NAME}")
        if res.status_code == 200:
            data = res.json()
            if data:
                return pd.DataFrame(data)
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
    with st.form("stein_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # تجهيز البيانات للإرسال (تأكد أن المفاتيح تطابق أول صف في الشيت)
                payload = [{
                    "id": len(df_c) + 101,
                    "اسم العميل": name,
                    "الأرقام": phone,
                    "العنوان": addr,
                    "المنطقة": area,
                    "Timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }]
                
                try:
                    res = requests.post(f"{API_URL}/{SHEET_NAME}", json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ مبروك يا هندسة! تم تسجيل {name} بنجاح.")
                        st.balloons()
                        st.cache_data.clear() # مسح الكاش لرؤية العميل فوراً
                    else:
                        st.error("فشل في الحفظ، تأكد من أسماء الأعمدة في الشيت.")
                except:
                    st.error("خطأ في الاتصال بالسيرفر.")
            else:
                st.warning("برجاء إدخال الاسم والرقم.")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

    if df_c.empty:
        st.info("لا توجد بيانات حالياً. جرب تسجيل أول عميل.")
    else:
        search = st.text_input("🔍 بحث بالاسم أو الرقم")
        
        # فلترة البيانات
        f_df = df_c.copy()
        if search:
            # بحث شامل في كل الأعمدة
            f_df = f_df[f_df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for i, row in f_df.iterrows():
            # محاولة قراءة الاسم والهاتف (بمرونة لو الأسماء تغيرت)
            display_name = row.get('اسم العميل', row.iloc[2] if len(row) > 2 else "عميل")
            display_phone = row.get('الأرقام', row.iloc[3] if len(row) > 3 else "000")
            
            with st.expander(f"👤 {display_name}"):
                st.write(f"📞 هاتف: {display_phone}")
                st.write(f"📍 المنطقة: {row.get('المنطقة', '-')}")
                st.write(f"🏠 العنوان: {row.get('العنوان', '-')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("📲 اتصال", f"tel:{display_phone}")
                with col2:
                    st.link_button("💬 واتساب", f"https://wa.me/2{display_phone}")
