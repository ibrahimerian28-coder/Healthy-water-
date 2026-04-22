import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الهوية البصرية ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# روابط الصور (تأكد من صحتها في مستودعك)
LOGO_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/logo.png"
BG_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/background.png"

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{BG_URL}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .main-box {{
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        color: black;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قواعد البيانات ---
def load_db(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_db(df, file):
    df.to_csv(file, index=False)

# الأعمدة المطلوبة
C_COLS = ['id', 'اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'الموقع', 'دورة الصيانة', 'تاريخ الزيارة القادمة', 'تاريخ آخر زيارة']
df_c = load_db("customers_final.csv", C_COLS)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.image(LOGO_URL, width=150)
    st.title("💧 Healthy Water")
    t1, t2 = st.tabs(["🔑 الإدارة", "👤 العملاء"])
    
    with t1:
        pwd = st.text_input("باسورد المدير", type="password")
        if st.button("دخول الإدارة"):
            if pwd == "HgM18082019$&)":
                st.session_state.role = "admin"
                st.rerun()
            else: st.error("خطأ!")
            
    with t2:
        c_id = st.text_input("كود العميل (ID)")
        c_ph = st.text_input("رقم الهاتف")
        if st.button("دخول العميل"):
            user = df_c[(df_c['id'].astype(str) == str(c_id)) & (df_c['الهواتف'].str.contains(str(c_ph), na=False))]
            if not user.empty:
                st.session_state.role = "client"
                st.session_state.user_info = user.iloc[0]
                st.rerun()
            else: st.error("بيانات غير صحيحة")
    st.stop()

# --- 4. لوحة الإدارة ---
st.sidebar.image(LOGO_URL, width=100)
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات", "المخزن", "الحسابات والأرباح", "المتجر"])

if menu == "تسجيل عميل جديد":
    st.header("📝 تسجيل عميل جديد (يبدأ من 101)")
    with st.form("add_new"):
        name = st.text_input("👤 اسم العميل")
        phones = st.text_input("📞 الهواتف (فاصلة بين الأرقام)")
        addr = st.text_area("🏠 العنوان")
        area = st.text_input("📍 المنطقة")
        loc = st.text_input("🔗 لوكيشن جوجل مابس")
        cycle = st.number_input("📅 الدورة (شهور)", min_value=1, value=3)
        last_v = st.date_input("🗓️ تاريخ آخر زيارة", value=datetime.now().date())
        
        if st.form_submit_button("✅ حفظ"):
            new_id = 101 if df_c.empty else int(df_c['id'].max()) + 1
            next_v = last_v + timedelta(days=cycle * 30)
            new_row = {'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 
                       'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 
                       'تاريخ الزيارة القادمة': next_v, 'تاريخ آخر زيارة': last_v}
            df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
            save_db(df_c, "customers_final.csv")
            st.success(f"تم الحفظ! كود العميل: {new_id}")
            st.balloons()

elif menu == "بيانات العملاء":
    st.header("👥 قاعدة البيانات والبحث")
    search = st.text_input("🔎 ابحث بالاسم أو الرقم")
    
    # فلترة وعرض البيانات بالألوان
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]
    
    def color_date(val):
        try:
            diff = (pd.to_datetime(val).date() - datetime.now().date()).days
            if diff < 0: return 'background-color: #ffcccc' # أحمر (متأخر)
            if diff <= 7: return 'background-color: #ffffcc' # أصفر (قريب)
            return 'background-color: #ccffcc' # أخضر (بدري)
        except: return ''

    st.dataframe(f_df.style.applymap(color_date, subset=['تاريخ الزيارة القادمة']), use_container_width=True)

if st.sidebar.button("خروج"):
    st.session_state.role = None
    st.rerun()
