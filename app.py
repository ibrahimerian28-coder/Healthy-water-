import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide")

# روابط القراءة (من الشيت مباشرة)
SHEET_ID = "1f3wgOq_s0Aies7JasDzKFz8R38U39hTa5IUoJTZYL30"
CLIENTS_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Customers"

# رابط الإرسال (مستخرج من رابط الفورم بتاعك)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeQa4UJW8n9-8lCipPgrUGBbTSmfxNizON86zDfWgw6pmOmYw/formResponse"

# --- 2. وظائف البيانات ---
def load_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return pd.read_csv(StringIO(res.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_c = load_data(CLIENTS_READ_URL)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water - لوحة التحكم")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد"])

# --- 5. تسجيل عميل جديد (الإرسال للفورم) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_client_form", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        
        if st.form_submit_button("✅ حفظ في قاعدة البيانات"):
            if name and phones:
                # ميكانيكا الـ ID
                new_id = 101 if df_c.empty else int(df_c.iloc[:,0].max()) + 1
                
                # تجهيز البيانات للإرسال (الأكواد مستخرجة من رابطك)
                form_data = {
                    "entry.1872338545": new_id,
                    "entry.1466263036": name,
                    "entry.334977578": phones,
                    "entry.1604703615": addr,
                    "entry.51378520": area,
                    "entry.1332478222": loc,
                    "entry.1671668465": cycle,
                    "entry.416270816": str(datetime.now().date()), # تاريخ القادم (مبدئياً)
                    "entry.1371491317": "لم تتم" # تاريخ آخر زيارة
                }
                
                try:
                    response = requests.post(FORM_URL, data=form_data)
                    if response.status_code == 200:
                        st.success(f"تم تسجيل العميل {name} بنجاح!")
                        st.balloons()
                    else:
                        st.error("حدث خطأ في الاتصال بالفورم")
                except:
                    st.error("فشل إرسال البيانات")
            else:
                st.warning("برجاء إدخال الاسم والهاتف")

# --- 6. عرض البيانات (الكروت) ---
elif menu == "بيانات العملاء":
    st.header("👥 العملاء المسجلين")
    if df_c.empty:
        st.info("لا توجد بيانات حالياً. جرب تسجيل عميل أولاً.")
    else:
        search = st.text_input("🔍 بحث")
        f_df = df_c.copy()
        # هنا نفترض ترتيب الأعمدة في الشيت بناءً على الفورم
        # لو الأسماء مختلفة في الشيت، هنحتاج نعدل أسماء الأعمدة هنا
        for i, row in f_df.iterrows():
            with st.expander(f"👤 {row.iloc[1]}"): # العمود التاني هو الاسم
                st.write(f"📍 المنطقة: {row.iloc[4]}")
                st.write(f"🏠 العنوان: {row.iloc[3]}")
                st.write(f"📞 الهواتف: {row.iloc[2]}")
                # زر الاتصال لأول رقم
                main_p = str(row.iloc[2]).split(',')[0].strip()
                st.link_button(f"اتصال {main_p}", f"tel:{main_p}")
