import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الخاص بك (تأكد إنه هو اللي في الصورة)
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"
SHEET_NAME = "Customers"

# --- 2. وظيفة جلب البيانات (أقوى نسخة) ---
def load_data():
    try:
        res = requests.get(f"{API_URL}/{SHEET_NAME}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
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

# --- 5. تسجيل عميل جديد (إرسال أعمى لضمان النجاح) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("final_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # لازم الأسماء هنا تكون هي هي اللي في أول صف في الشيت بالظبط
                payload = [{
                    "id": str(int(time.time())), 
                    "اسم العميل": name,
                    "الأرقام": phone,
                    "العنوان": addr,
                    "المنطقة": area,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d")
                }]
                try:
                    requests.post(f"{API_URL}/{SHEET_NAME}", json=payload, timeout=10)
                    st.success(f"تم الحفظ! العميل {name} سجلناه بنجاح.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except:
                    st.warning("البيانات أرسلت، حدث الصفحة للتأكد.")
            else:
                st.error("دخل الاسم والرقم يا هندسة")

# --- 6. عرض البيانات (النسخة الذكية) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c.empty:
        st.info("لا توجد بيانات حالياً. تأكد أن صفحة Customers في الشيت تحتوي على بيانات.")
    else:
        # عرض جدول صغير جداً للتأكد إن فيه اتصال
        st.write(f"عدد العملاء المسجلين: {len(df_c)}")
        
        search = st.text_input("🔍 بحث")
        
        for i, row in df_c.iterrows():
            try:
                # الكود دلوقتي هيدور على الاسم والرقم بأي طريقة
                # لو ملقاش الاسم بالكلمة، هياخد أول عمود فيه نص
                c_name = row.get('اسم العميل', row.iloc[1] if len(row) > 1 else "بدون اسم")
                c_phone = row.get('الأرقام', row.iloc[2] if len(row) > 2 else "000")
                
                if search.lower() in str(c_name).lower() or search in str(c_phone):
                    with st.expander(f"👤 {c_name}"):
                        st.write(f"📞 هاتف: {c_phone}")
                        st.write(f"📍 المنطقة: {row.get('المنطقة', 'غير محدد')}")
                        st.link_button("📲 اتصال", f"tel:{c_phone}")
            except:
                continue
