import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# الرابط الأساسي للشيت
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
# رابط القراءة المباشر من صفحة Form Responses 1
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1292025701"

# --- 2. وظيفة جلب البيانات ---
def load_data():
    try:
        # إضافة توقيت للرابط لمنع الكاش نهائياً
        res = requests.get(f"{READ_URL}&t={datetime.now().timestamp()}", timeout=10)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
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

# --- 5. تسجيل عميل جديد (باستخدام Google Form كـ "ساعي بريد" فقط) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("direct_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        cycle = st.number_input("الدورة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ"):
            if name and phones:
                # رابط الإرسال المباشر (تأكد من الأكواد دي من الرابط اللي بعتهولي قبل كدة)
                post_url = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"
                payload = {
                    "entry.1872338545": "101" if df_c.empty else len(df_c)+101,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()),
                    "entry.1371491317": "لم تتم"
                }
                try:
                    # إرسال البيانات
                    requests.post(post_url, data=payload)
                    st.success("✅ البيانات وصلت لجوجل!")
                    st.info("اضغط على 'بيانات العملاء' من القائمة الجانبية الآن.")
                except:
                    st.error("فشل في الوصول للسيرفر")

# --- 6. عرض البيانات (الوضع الآمن الأخير) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    
    # زر تحديث قوي جداً
    if st.button("🔄 تحديث إجباري للبيانات"):
        st.rerun()

    if df_c.empty:
        st.warning("⚠️ التطبيق مش شايف بيانات. اتأكد إنك فاتح الشيت Share -> Anyone with link can EDIT")
    else:
        # عرض البيانات كجدول أولاً (عشان نضمن إنك شايف كل حاجة)
        st.subheader("البيانات المسجلة فعلياً في الشيت:")
        st.dataframe(df_c)
        
        # محاولة عرض الكروت
        st.divider()
        try:
            for i, row in df_c.iterrows():
                # استخدام iloc للوصول للبيانات بالأرقام عشان لو الأسامي اتغيرت
                # العمود 2 هو الاسم، العمود 3 هو التليفون
                with st.expander(f"👤 {row.iloc[2]}"):
                    st.write(f"📞 هاتف: {row.iloc[3]}")
                    st.write(f"🏠 العنوان: {row.iloc[4]}")
                    st.link_button("اتصال", f"tel:{row.iloc[3]}")
        except:
            st.info("استخدم الجدول أعلاه لعرض البيانات حالياً.")
