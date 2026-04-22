import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import time

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# الرابط المباشر لصفحة Form Responses 1 باستخدام الـ GID الصحيح
GID = "1292025701"
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظيفة التحميل مع كسر التخزين (Cache) ---
def load_data():
    try:
        # إضافة توقيت حالي للرابط لإجبار جوجل على إرسال أحدث نسخة
        timestamp = int(time.time())
        final_url = f"{READ_URL}&cache={timestamp}"
        res = requests.get(final_url, timeout=10)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# تحميل البيانات في كل مرة يفتح فيها التطبيق
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
        cycle = st.number_input("الدورة", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # ميكانيكا الـ ID بناءً على عدد الصفوف الحالي
                new_id = 101 if df_c.empty else int(len(df_c)) + 101
                
                form_data = {
                    "entry.1872338545": new_id,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()),
                    "entry.1371491317": "لم تتم"
                }
                headers = {'User-Agent': "Mozilla/5.0"}
                try:
                    res = requests.post(FORM_URL, data=form_data, headers=headers)
                    st.success("✅ تم الحفظ بنجاح! جاري تحديث البيانات...")
                    time.sleep(2) # انتظار ثانية لضمان تحديث جوجل
                    st.rerun()
                except:
                    st.error("❌ فشل الاتصال بجوجل")

# --- 6. عرض البيانات ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

    if df_c.empty:
        st.info("لم نتمكن من العثور على بيانات. تأكد من تسجيل عميل واحد على الأقل.")
    else:
        # عرض البيانات في كروت
        search = st.text_input("🔍 بحث")
        f_df = df_c.copy()
        
        # العمود 2 هو الاسم (العد يبدأ من 0: Timestamp, 1: id, 2: Name)
        try:
            if search:
                f_df = f_df[f_df.iloc[:, 2].astype(str).str.contains(search, na=False)]

            for i, row in f_df.iterrows():
                with st.expander(f"👤 {row.iloc[2]}"):
                    st.write(f"📞 هاتف: {row.iloc[3]}")
                    st.write(f"📍 المنطقة: {row.iloc[5]}")
                    st.link_button("📞 اتصال", f"tel:{row.iloc[3]}")
                    st.link_button("💬 واتساب", f"https://wa.me/2{row.iloc[3]}")
        except Exception as e:
            st.warning("البيانات ظهرت في الشيت ولكن هناك اختلاف بسيط في الترتيب.")
            st.dataframe(df_c)
