import streamlit as st
import pandas as pd
import requests
from io import BytesIO # لتغيير التعامل مع الملفات
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط تصدير الشيت بالكامل كملف إكسيل (ده أقوى من الـ CSV)
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة التحميل "الخارقة" ---
def load_data():
    try:
        # تحميل الملف كإكسيل لضمان قراءة كل التبويبات
        res = requests.get(EXCEL_URL, timeout=15)
        if res.status_code == 200:
            # قراءة تبويب Form Responses 1 بالاسم
            df = pd.read_excel(BytesIO(res.content), sheet_name="Form Responses 1")
            return df
        return pd.DataFrame()
    except Exception as e:
        # لو فشل في قراءة التبويب، يقرأ أول تبويب متاح
        try:
            res = requests.get(EXCEL_URL, timeout=10)
            return pd.read_excel(BytesIO(res.content))
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
    with st.form("final_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("الدورة", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
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
                    requests.post(FORM_URL, data=payload)
                    st.success("✅ تم الإرسال! انتظر ثواني وحدث القائمة.")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("خطأ في الشبكة")

# --- 6. عرض البيانات (بدون رسائل خطأ صفراء) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

    if df_c.empty:
        st.info("📭 لا توجد بيانات حالياً. سجل عميل جديد لتظهر القائمة.")
    else:
        search = st.text_input("🔍 بحث")
        # فلترة البيانات
        f_df = df_c.copy()
        if search:
            # البحث في كل الأعمدة
            f_df = f_df[f_df.apply(lambda row: search in str(row.values), axis=1)]

        for i, row in f_df.iterrows():
            # محاولة قراءة الاسم والهاتف بذكاء
            c_name = row.get('اسم العميل', row.iloc[2] if len(row)>2 else "غير معروف")
            c_phone = row.get('الهاتف', row.iloc[3] if len(row)>3 else "بدون رقم")
            
            with st.expander(f"👤 {c_name}"):
                st.write(f"📞 هاتف: {c_phone}")
                st.write(f"🏠 العنوان: {row.get('العنوان', row.iloc[4] if len(row)>4 else '-')}")
                st.link_button("📲 اتصال", f"tel:{c_phone}")
