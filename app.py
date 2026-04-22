import streamlit as st
import pandas as pd
import requests

# --- الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", page_icon="💧")

# الرابط المباشر لصفحة Customers
API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982/Customers"

# --- دالة جلب البيانات ---
def get_data():
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- الواجهة ---
st.title("💧 نظام إدارة العملاء")
menu = st.sidebar.selectbox("القائمة", ["إضافة عميل جديد", "عرض كل العملاء"])

if menu == "إضافة عميل جديد":
    st.subheader("📝 تسجيل بيانات عميل")
    with st.form("add_form", clear_on_submit=True):
        # استخدمنا أسامي إنجليزية بسيطة "name" و "phone" عشان السيرفر ميزعلش
        name = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ البيانات"):
            if name and phone:
                # الـ payload ده هو اللي Stein هيفهمه فوراً
                payload = [{"name": name, "phone": phone, "area": area}]
                
                try:
                    # بنبعت الداتا "خبط لزق" للسيرفر
                    resp = requests.post(API_URL, json=payload, timeout=15)
                    
                    if resp.status_code == 200:
                        st.success(f"تم تسجيل {name} بنجاح.. السيرفر رضي عننا!")
                        st.balloons()
                    else:
                        st.error(f"السيرفر لسه مقمص: {resp.text}")
                except:
                    st.error("فيه خناقة في الشبكة، جرب تاني!")
            else:
                st.warning("لازم تكتب الاسم والرقم يا هندسة!")

else:
    st.subheader("👥 قائمة العملاء المسجلين")
    if st.button("🔄 تحديث القائمة"):
        st.cache_data.clear()
        st.rerun()
        
    df = get_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("الشيت لسه مفيش فيه داتا.. سجل أول عميل!")
