import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

# --- 1. الإعدادات والروابط ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت بتاعك (Direct CSV Link)
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
# ده رابط الصفحة الأولى (Data)
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
# ده رابط الصفحة الثانية (Maintenance) لو موجودة - لو مش موجودة الكود هيتعامل عادي
MAINT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1853673750" # تأكد من الـ gid من رابط الصفحة في المتصفح

def get_google_data(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.info("01286609535")
menu = st.sidebar.radio("القائمة الرئيسية", 
    ["🔍 إدارة العملاء وتواصل", "➕ إضافة عميل جديد", "🛠️ تسجيل صيانة", "📅 جدول الأسبوع"])

# --- 3. إدارة العملاء وتواصل سريع ---
if menu == "🔍 إدارة العملاء وتواصل":
    st.header("👤 قاعدة بيانات العملاء")
    df = get_google_data(DATA_URL)
    
    if not df.empty:
        search = st.text_input("🔍 ابحث بالاسم أو المنطقة")
        if search:
            df = df[df['name'].str.contains(search, na=False, case=False) | df['area'].str.contains(search, na=False, case=False)]
        
        for _, row in df.iterrows():
            with st.expander(f"👤 {row['name']} | 📍 {row['area']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"🏠 **العنوان:** {row['address']}")
                    st.write(f"📅 **التركيب:** {row['install_date']}")
                with c2:
                    # أزرار التواصل الذكية
                    phone = str(row['phones_json']).strip()
                    # تنظيف الرقم للواتساب (شيل أي مسافات أو علامات)
                    clean_phone = phone.replace(" ", "").replace("+", "")
                    if len(clean_phone) == 11 and clean_phone.startswith("01"):
                        clean_phone = "2" + clean_phone # إضافة كود مصر للواتساب
                    
                    cola, colb = st.columns(2)
                    cola.markdown(f'''<a href="tel:{phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:10px;">📞 اتصل</button></a>''', unsafe_allow_html=True)
                    colb.markdown(f'''<a href="https://wa.me/{clean_phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:10px;">💬 واتساب</button></a>''', unsafe_allow_html=True)
    else:
        st.warning("مش قادر يقرأ البيانات.. تأكد من وجود داتا في الشيت.")

# --- 4. إضافة عميل جديد ---
elif menu == "➕ إضافة عميل جديد":
    st.header("📝 تسجيل كارت عميل")
    st.info("بما إننا شغالين ربط مباشر (للقراءة)، التسجيل حالياً بيعرض لك الداتا عشان تحطها في الشيت وتسمع هنا فوراً.")
    with st.form("new_cust"):
        name = st.text_input("اسم العميل")
        area = st.text_input("المنطقة")
        address = st.text_input("العنوان")
        phone = st.text_input("رقم التليفون")
        install_date = st.date_input("تاريخ التركيب", datetime.now())
        
        if st.form_submit_button("✅ تجهيز البيانات"):
            if name and phone:
                cust_id = str(uuid.uuid4())[:8]
                st.success(f"تم التجهيز! الكود: {cust_id}")
                st.code(f"{cust_id}\t{name}\t{phone}\t{address}\t{area}\t{install_date}")
                st.balloons()
            else:
                st.error("كمل البيانات يا هندسة")

# --- 5. تسجيل صيانة ---
elif menu == "🛠️ تسجيل صيانة":
    st.header("🛠️ سجل زيارة صيانة")
    df_c = get_google_data(DATA_URL)
    if not df_c.empty:
        target = st.selectbox("اختر العميل", df_c['name'].unique())
        with st.form("maint_form"):
            st.write("🔧 الشمعات اللي اتغيرت:")
            c1, c2, c3 = st.columns(3)
            p1 = c1.checkbox("P1")
            p2 = c2.checkbox("P2")
            p3 = c3.checkbox("P3")
            memb = c1.checkbox("ممبرين")
            post = c2.checkbox("بوست")
            
            amount = st.number_input("المبلغ", 0)
            next_visit = st.date_input("الزيارة الجاية", datetime.now() + timedelta(days=90))
            
            if st.form_submit_button("💾 حفظ"):
                st.write(f"سجل في الشيت: {target} - مبلغ {amount} - الجاية {next_visit}")
