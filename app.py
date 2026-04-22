import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الخاص بك من Stein
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"

# --- 2. وظيفة جلب البيانات الذكية ---
def load_data(sheet_name):
    try:
        res = requests.get(f"{API_URL}/{sheet_name}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                return pd.DataFrame(data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# محاولة القراءة من Customers أولاً، ثم التبويب الافتراضي
df_c = load_data("Customers")
if df_c.empty:
    df_c = load_data("Sheet1") # محاولة تانية لاسم افتراضي شائع

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

# --- 5. تسجيل عميل جديد (إرسال صريح) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("final_rescue", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                # البيانات لازم تتبع نفس عناوين أول صف في الشيت
                payload = [{
                    "id": str(int(time.time())),
                    "اسم العميل": name,
                    "الأرقام": phone,
                    "العنوان": addr,
                    "المنطقة": area,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                }]
                # هنبعت لـ "Customers" ونأمل إن Stein عمل Sync
                try:
                    requests.post(f"{API_URL}/Customers", json=payload, timeout=10)
                    st.success(f"✅ مبروك! تم تسجيل {name}")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("فشل الإرسال.. تأكد من اتصال الإنترنت")
            else:
                st.warning("برجاء إدخال الاسم والرقم")

# --- 6. عرض البيانات (بدون تعقيد) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c.empty:
        st.warning("⚠️ التطبيق مش شايف بيانات في الشيت.")
        st.info("تأكد إن صفحة 'Customers' فيها على الأقل عميل واحد مسجل من داخل التطبيق.")
    else:
        st.write(f"عدد المسجلين: {len(df_c)}")
        search = st.text_input("🔍 بحث")
        
        for i, row in df_c.iterrows():
            try:
                # قراءة مرنة (لو ملقاش الاسم بالاسم ياخده بمكانه)
                c_name = row.get('اسم العميل', row.iloc[1] if len(row) > 1 else "بدون اسم")
                c_phone = row.get('الأرقام', row.iloc[2] if len(row) > 2 else "000")
                
                if search.lower() in str(c_name).lower() or search in str(c_phone):
                    with st.expander(f"👤 {c_name}"):
                        st.write(f"📞 هاتف: {c_phone}")
                        st.write(f"🏠 العنوان: {row.get('العنوان', '-')}")
                        st.link_button("📲 اتصال", f"tel:{c_phone}")
            except:
                continue
