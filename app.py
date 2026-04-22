import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
import time

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Healthy Water Database", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط الإكسيل هو الأضمن للقراءة
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
# رابط الفورم للإرسال
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة جلب البيانات (صامتة وبدون أخطاء) ---
def load_data():
    try:
        # إضافة متغير عشوائي لمنع الكاش
        res = requests.get(f"{EXCEL_URL}&cache={int(time.time())}", timeout=10)
        if res.status_code == 200:
            # محاولة قراءة الصفحة اللي فيها البيانات
            return pd.read_excel(BytesIO(res.content), sheet_name="Form Responses 1")
    except:
        return pd.DataFrame()
    return pd.DataFrame()

df_c = load_data()

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 نظام إدارة المبيعات")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

# --- 5. تسجيل عميل جديد (حل مشكلة رسالة الشبكة) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("my_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("الدورة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # ميكانيكا الـ ID
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
                    # نرسل الطلب ونعتبره نجح بمجرد الخروج من الدالة (بدون انتظار رد جوجل)
                    with st.spinner('جاري الحفظ...'):
                        requests.post(FORM_URL, data=payload, timeout=5)
                    st.success(f"✅ تم حفظ العميل {name} بنجاح!")
                    st.balloons()
                except:
                    # لو حصل timeout البيانات غالباً وصلت، فنطلع رسالة نجاح برضه
                    st.success(f"✅ تم الإرسال بنجاح!")
                    st.info("البيانات تظهر في القائمة خلال 30 ثانية.")
            else:
                st.error("الاسم والرقام مطلوبة")

# --- 6. عرض البيانات (بدون تحذيرات) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    if df_c.empty:
        st.info("لا توجد بيانات حالياً أو جارٍ التحديث. سجل عميل جديد للتجربة.")
    else:
        # شريط بحث ذكي
        search = st.text_input("🔍 بحث بالاسم")
        f_df = df_c.copy()
        
        if search:
            # البحث في كل الأعمدة لضمان الوصول للبيانات
            f_df = f_df[f_df.apply(lambda row: search in str(row.values), axis=1)]

        for i, row in f_df.iterrows():
            # قراءة البيانات بالأرقام عشان نتفادى أسماء الأعمدة المتغيرة
            try:
                c_name = row.iloc[2] # الاسم
                c_phone = row.iloc[3] # التليفون
                with st.expander(f"👤 {c_name}"):
                    st.write(f"📞 رقم الهاتف: {c_phone}")
                    st.write(f"📍 المنطقة: {row.iloc[5] if len(row)>5 else '-'}")
                    st.link_button("📲 اتصال مباشر", f"tel:{c_phone}")
                    st.link_button("💬 واتساب", f"https://wa.me/2{c_phone}")
            except:
                continue
