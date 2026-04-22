import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الأساسي للتصدير (بدون تحديد gid في الرابط لضمان الوصول)
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط "الخام" اللي بيجيب الشيت كأنه ملف إكسيل
RAW_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1292025701"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة التحميل (محسنة جداً) ---
def load_data():
    try:
        # كسر الكاش بإضافة توقيت عشوائي
        response = requests.get(f"{RAW_URL}&t={int(time.time())}", timeout=10)
        if response.status_code == 200:
            new_df = pd.read_csv(StringIO(response.text))
            return new_df
        return pd.DataFrame()
    except Exception as e:
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
    with st.form("add_client_final", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("الدورة (شهور)", value=3, step=1)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # حساب الـ ID
                new_id = 101 if df_c.empty else len(df_c) + 101
                
                payload = {
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
                    requests.post(FORM_URL, data=payload, timeout=10)
                    st.success(f"تم إرسال {name} بنجاح!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("فشل في الوصول لجوجل، لكن قد تكون البيانات وصلت.")
            else:
                st.warning("الاسم والموبايل مطلوبين")

# --- 6. عرض البيانات (حل نهائي للرسالة الصفراء) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c is None or df_c.empty:
        st.error("⚠️ التطبيق لا يزال غير قادر على قراءة البيانات.")
        st.info("تأكد من وجود صف واحد على الأقل في تبويب Form Responses 1.")
    else:
        # عرض جدول صغير للتأكد
        with st.expander("📊 عرض الجدول الخام"):
            st.write(df_c)

        search = st.text_input("🔍 بحث بالاسم")
        f_df = df_c.copy()
        
        # محاولة البحث (العمود رقم 2 هو الاسم عادةً)
        try:
            if search:
                # بنبحث في كل الجدول عن الكلمة عشان نتفادى غلط ترتيب الأعمدة
                f_df = f_df[f_df.apply(lambda row: search in str(row.values), axis=1)]

            for i, row in f_df.iterrows():
                # عرض البيانات بالترتيب المكتشف
                c_name = row.iloc[2] if len(row) > 2 else "غير معروف"
                c_phone = row.iloc[3] if len(row) > 3 else "بدون رقم"
                
                with st.expander(f"👤 {c_name}"):
                    st.write(f"📞 هاتف: {c_phone}")
                    st.write(f"📍 منطقة: {row.iloc[5] if len(row) > 5 else '-'}")
                    st.link_button("📲 اتصال", f"tel:{c_phone}")
        except Exception as e:
            st.warning("حدث خطأ في عرض الكروت، يرجى مراجعة الجدول الخام.")
