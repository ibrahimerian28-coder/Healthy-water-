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
                st.rer

