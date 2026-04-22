import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water", layout="wide")

LOGO_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/logo.png"
BG_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/background.png"

# --- 2. إدارة البيانات ---
def load_db(file, cols):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_db(df, file): df.to_csv(file, index=False)

C_COLS = ['id', 'اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'الموقع', 'دورة الصيانة', 'تاريخ الزيارة القادمة', 'تاريخ آخر زيارة']
S_COLS = ['العنصر', 'الكميه', 'سعر الوحده', 'القيمه الاجماليه']

df_c = load_db("customers_final.csv", C_COLS)
df_s = load_db("stock_final.csv", S_COLS)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None

if st.session_state.role is None:
    st.image(LOGO_URL, width=150)
    st.title("💧 Healthy Water")
    pwd = st.text_input("باسورد المدير", type="password")
    if st.button("دخول الإدارة"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
        else: st.error("خطأ!")
    st.stop()

# --- 4. القائمة الجانبية ---
st.sidebar.image(LOGO_URL, width=80)
menu = st.sidebar.radio("القائمة الرئيسية", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات", "المخزن", "الحسابات والمصروفات"])

# --- 5. صفحة تسجيل عميل جديد (تم الإصلاح) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 تسجيل عميل جديد")
    with st.form("add_customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("👤 اسم العميل")
        phones = col2.text_input("📞 الهواتف (فاصلة بين الأرقام)")
        
        addr = st.text_area("🏠 العنوان")
        
        col3, col4 = st.columns(2)
        area = col3.text_input("📍 المنطقة")
        loc = col4.text_input("🔗 رابط اللوكيشن")
        
        col5, col6 = st.columns(2)
        cycle = col5.number_input("📅 دورة الصيانة (شهور)", min_value=1, value=3)
        last_v = col6.date_input("🗓️ تاريخ آخر زيارة", value=datetime.now().date())
        
        if st.form_submit_button("✅ حفظ العميل"):
            if name and phones:
                # ميكانيكا الـ ID يبدأ من 101
                new_id = 101 if df_c.empty else int(df_c['id'].max()) + 1
                next_v = last_v + timedelta(days=int(cycle) * 30)
                
                new_row = {
                    'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 
                    'العنوان': addr, 'المنطقه': area, 'الموقع': loc, 
                    'دورة الصيانة': cycle, 'تاريخ الزيارة القادمة': next_v, 
                    'تاريخ آخر زيارة': last_v
                }
                
                df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
                save_db(df_c, "customers_final.csv")
                st.success(f"تم تسجيل العميل بنجاح بكود: {new_id}")
                st.balloons()
            else:
                st.error("يرجى ملء الاسم ورقم الهاتف")

# --- 6. صفحة بيانات العملاء ---
elif menu == "بيانات العملاء":
    st.header("👥 قاعدة بيانات العملاء")
    search = st.text_input("🔎 بحث بالاسم أو الرقم")
    
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]
    
    def color_date(val):
        try:
            diff = (pd.to_datetime(val).date() - datetime.now().date()).days
            if diff < 0: return 'background-color: #ffcccc'
            if diff <= 7: return 'background-color: #ffffcc'
            return 'background-color: #ccffcc'
        except: return ''

    st.dataframe(f_df.style.map(color_date, subset=['تاريخ الزيارة القادمة']), use_container_width=True)

# --- 7. صفحة المخزن ---
elif menu == "المخزن":
    st.header("📦 إدارة المخزن")
    if df_s.empty:
        items = ['p1', 'p2', 'p3', 'ممبرين', 'بوست كاربون', 'كالسيت', 'انفر ريد']
        df_s = pd.DataFrame({'العنصر': items, 'الكميه': [0]*7, 'سعر الوحده': [0.0]*7, 'القيمه الاجماليه': [0.0]*7})
    
    edited_df = st.data_editor(df_s, num_rows="dynamic", use_container_width=True)
    if st.button("💾 حفظ التعديلات"):
        edited_df['القيمه الاجماليه'] = edited_df['الكميه'] * edited_df['سعر الوحده']
        save_db(edited_df, "stock_final.csv")
        st.success("تم التحديث")

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
