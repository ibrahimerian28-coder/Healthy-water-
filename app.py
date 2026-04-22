import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط من الصورة اللي بعتها
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"
# اسم الصفحة اللي هنعرض منها البيانات
SHEET_NAME = "Customers" 

# --- 2. وظيفة جلب البيانات ---
def load_data():
    try:
        # طلب البيانات من Stein
        res = requests.get(f"{API_URL}/{SHEET_NAME}", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
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

# --- 5. تسجيل عميل جديد (إرسال مباشر لـ Stein) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("direct_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # تجهيز البيانات
                new_data = [{
                    "id": len(df_c) + 101,
                    "اسم العميل": name,
                    "الأرقام": phone,
                    "العنوان": addr,
                    "المنطقة": area,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                }]
                try:
                    # إرسال البيانات لـ Stein (بتحطها في الشيت فوراً)
                    resp = requests.post(f"{API_URL}/{SHEET_NAME}", json=new_data)
                    if resp.status_code == 200:
                        st.success(f"✅ تم حفظ {name} بنجاح!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("فشل الحفظ.. تأكد من مسميات الأعمدة في الشيت")
                except:
                    st.error("مشكلة في الاتصال بالسيرفر")
            else:
                st.warning("الاسم والأرقام مطلوبة")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c.empty:
        st.info("لا توجد بيانات في صفحة Customers حالياً.")
    else:
        search = st.text_input("🔍 بحث")
        # فلترة
        f_df = df_c.copy()
        if search:
            f_df = f_df[f_df.apply(lambda r: search in str(r.values), axis=1)]

        for i, row in f_df.iterrows():
            # قراءة البيانات بأسماء الأعمدة
            c_name = row.get('اسم العميل', 'عميل جديد')
            c_phone = row.get('الأرقام', '000')
            
            with st.expander(f"👤 {c_name}"):
                st.write(f"📞 هاتف: {c_phone}")
                st.write(f"🏠 العنوان: {row.get('العنوان', '-')}")
                st.write(f"📍 المنطقة: {row.get('المنطقة', '-')}")
                st.link_button("📲 اتصال", f"tel:{c_phone}")
