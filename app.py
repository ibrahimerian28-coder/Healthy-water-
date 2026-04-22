import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import random # لاستخدامه في تحديث البيانات الإجباري

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة تحميل البيانات المحدثة (إجبار التحديث) ---
def load_data():
    # إضافة رقم عشوائي للرابط لمنع المتصفح من عرض نسخة قديمة (Cache)
    cache_buster = random.randint(1, 100000)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Form%20Responses%201&cache={cache_buster}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.read_csv(StringIO(res.text))
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# تحميل البيانات
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
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                try:
                    # ميكانيكا الـ ID الآمنة
                    new_id = 101 if df_c.empty else int(df_c.iloc[:, 1].max()) + 1
                except:
                    new_id = 101

                form_data = {
                    "entry.1872338545": new_id,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1332478222": loc,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()),
                    "entry.1371491317": "لم تتم"
                }
                headers = {'Referer': FORM_URL, 'User-Agent': "Mozilla/5.0"}
                try:
                    requests.post(FORM_URL, data=form_data, headers=headers)
                    st.success(f"تم الإرسال بنجاح! جاري تحديث القائمة...")
                    # مسح الكاش وإعادة التحميل فوراً
                    st.rerun()
                except:
                    st.error("خطأ في الاتصال")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    # زر يدوي لتحديث البيانات لو معلقت
    if st.button("🔄 تحديث يدوي للبيانات"):
        st.rerun()

    if df_c.empty or len(df_c.columns) < 3:
        st.info("لا توجد بيانات حالياً. تأكد من وجود بيانات في صفحة 'Form Responses 1' في الشيت.")
    else:
        search = st.text_input("🔍 بحث بالاسم")
        f_df = df_c.copy()
        
        # العمود 2 هو الاسم والعمود 3 هو الهاتف (بناءً على نظام جوجل فورم)
        try:
            if search:
                f_df = f_df[f_df.iloc[:, 2].astype(str).str.contains(search, na=False)]

            for i, row in f_df.iterrows():
                with st.expander(f"👤 {row.iloc[2]}"):
                    st.write(f"📞 هاتف: {row.iloc[3]}")
                    st.write(f"📍 المنطقة: {row.iloc[5] if len(row)>5 else 'غير محدد'}")
                    st.link_button("📲 اتصال", f"tel:{row.iloc[3]}")
        except:
            st.warning("البيانات موجودة في الشيت ولكن بترتيب مختلف.")
            st.dataframe(df_c) # عرض الجدول كما هو لو حصلت مشكلة في الكروت
