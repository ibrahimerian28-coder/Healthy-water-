import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط إكسيل مباشر وصريح
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة التحميل (محصنة ضد الفشل) ---
def load_data():
    try:
        # كسر الكاش برقم عشوائي
        res = requests.get(f"{EXCEL_URL}&v={time.time()}", timeout=15)
        if res.status_code == 200:
            # قراءة كل الصفحات وتدوير على الصفحة اللي فيها بيانات
            all_sheets = pd.read_excel(BytesIO(res.content), sheet_name=None)
            # لو صفحة الفورم موجودة ناخدها، لو لأ ناخد أول صفحة وخلاص
            if "Form Responses 1" in all_sheets:
                return all_sheets["Form Responses 1"]
            return list(all_sheets.values())[0]
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
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                payload = {
                    "entry.1872338545": int(time.time()), # ID فريد بالوقت
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1371491317": "لم تتم"
                }
                try:
                    requests.post(FORM_URL, data=payload, timeout=5)
                    st.success(f"تم تسجيل {name}.. روح لصفحة البيانات دلوقتي")
                    st.balloons()
                except:
                    st.warning("تم الإرسال.. جاري التحديث")
            else:
                st.error("كمل البيانات يا هندسة")

# --- 6. عرض البيانات (بدون تعقيدات) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث الشيت"):
        st.rerun()

    if df_c.empty:
        st.info("الشيت لسه بيحمل أو فاضي.. لو سجلت حد استنى دقيقة وجرب 'تحديث'.")
    else:
        # عرض البيانات بشكل كروت بسيط جداً
        search = st.text_input("🔍 بحث")
        
        for i, row in df_c.iterrows():
            try:
                # بنحاول نجيب الاسم من العمود التالت (موقع الاسم في الفورم)
                c_name = str(row.iloc[2])
                c_phone = str(row.iloc[3])
                
                if search.lower() in c_name.lower() or search in c_phone:
                    with st.expander(f"👤 {c_name}"):
                        st.write(f"📞 هاتف: {c_phone}")
                        st.write(f"📍 المنطقة: {row.iloc[5] if len(row)>5 else '-'}")
                        st.link_button("📲 اتصال", f"tel:{c_phone}")
            except:
                continue
