import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

API_URL = "https://api.steinhq.com/v1/storages/69e90c9f3807a370b05f5982"

# --- 2. وظيفة جلب البيانات (مع كاشف أعطال) ---
def load_data():
    try:
        res = requests.get(f"{API_URL}/Customers", timeout=15)
        if res.status_code == 200:
            return pd.DataFrame(res.json()), "متصل"
        return pd.DataFrame(), f"خطأ من السيرفر: {res.status_code}"
    except Exception as e:
        return pd.DataFrame(), f"خطأ في الاتصال: {str(e)}"

df_c, status = load_data()

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

# --- 5. تسجيل عميل جديد (مع تأكيد الاستلام) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("debug_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phone = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phone:
                payload = [{
                    "id": str(int(time.time())),
                    "اسم العميل": name,
                    "الأرقام": phone,
                    "العنوان": addr,
                    "المنطقة": area,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                }]
                try:
                    # بنبعت الداتا وبنشوف رد السيرفر "نصاً"
                    resp = requests.post(f"{API_URL}/Customers", json=payload, timeout=20)
                    if resp.status_code == 200:
                        st.success(f"✅ تم الحفظ بنجاح!")
                        st.balloons()
                    else:
                        st.error(f"السيرفر رد بغلط: {resp.text}")
                except Exception as e:
                    st.error(f"حصلت قفلة في الطريق: {str(e)}")
            else:
                st.warning("دخل الاسم والرقم يا بطل")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    # "رادار" كشف الأعطال
    with st.expander("🔍 حالة الاتصال بالسيرفر (للمتابعة)"):
        st.write(f"حالة السيرفر: {status}")
        if not df_c.empty:
            st.write("الأعمدة اللي الشيت باعتها:")
            st.write(list(df_c.columns))

    if st.button("🔄 تحديث إجباري"):
        st.rerun()

    if df_c.empty:
        st.info("مفيش داتا ظاهرة.. لو سجلت حد، اتأكد إنك كتبت 'اسم العميل' و 'الأرقام' صح في أول صف في الشيت.")
    else:
        search = st.text_input("🔍 بحث بالاسم")
        f_df = df_c.copy()
        if search:
            f_df = f_df[f_df.apply(lambda r: search in str(r.values), axis=1)]

        for i, row in f_df.iterrows():
            # قراءة ذكية جداً
            c_name = row.get('اسم العميل', row.iloc[1] if len(row)>1 else "بدون اسم")
            c_phone = row.get('الأرقام', row.iloc[2] if len(row)>2 else "000")
            with st.expander(f"👤 {c_name}"):
                st.write(f"📞 هاتف: {c_phone}")
                st.write(f"🏠 العنوان: {row.get('العنوان', '-')}")
                st.link_button("📲 اتصال", f"tel:{c_phone}")
