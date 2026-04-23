import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت اللي إنت بعته (تم تعديله ليصبح قابل للقراءة كـ CSV)
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.title("🌊 منظومة Healthy Water لإدارة الفلاتر")
st.markdown("---")

# --- 2. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة الرئيسية", ["📋 عرض جدول العملاء", "➕ إضافة عميل جديد", "🛠️ سجل الصيانات"])

# --- 3. عرض الجدول (الربط المباشر) ---
if menu == "📋 عرض جدول العملاء":
    st.header("📊 قاعدة بيانات العملاء (من جوجل شيتس)")
    try:
        # قراءة البيانات مباشرة من الرابط
        df = pd.read_csv(CSV_URL)
        
        if not df.empty:
            search = st.text_input("🔍 ابحث بالاسم أو المنطقة")
            if search:
                df = df[df.apply(lambda row: search in str(row.values), axis=1)]
            
            st.dataframe(df, use_container_width=True)
            
            # ميزة الاتصال السريع من الجدول
            st.info("💡 نصيحة: لو بتستخدم الموبايل، الجدول هيتعرض بشكل مرن.")
        else:
            st.warning("الشيت باين عليه فاضي.. سجل أول عميل يا وحش!")
    except Exception as e:
        st.error("مش قادر يقرأ الشيت.. تأكد إنك عامل Share لـ 'Anyone with the link' ويكون 'Viewer' على الأقل.")

# --- 4. إضافة عميل جديد ---
elif menu == "➕ إضافة عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    st.write("بما إننا لغينا Stein، أفضل طريقة تضمن إن بياناتك تروح الشيت 100% من الموبايل هي استخدام Google Form المربوط بالشيت.")
    
    with st.form("add_form"):
        name = st.text_input("اسم العميل")
        area = st.text_input("المنطقة")
        phone = st.text_input("رقم الهاتف")
        address = st.text_area("العنوان")
        
        submit = st.form_submit_button("✅ تجهيز البيانات للرفع")
        
        if submit:
            if name and phone:
                st.success("تم تجهيز كارت العميل!")
                # عرض البيانات بشكل يسهل نسخه
                st.code(f"الاسم: {name}\nالمنطقة: {area}\nالهاتف: {phone}\nالعنوان: {address}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}")
                st.balloons()
                st.info("انسخ البيانات دي وحطها في الشيت، أو استنى أعملك Google Form يرمي في الشيت ده أوتوماتيك!")

# --- 5. سجل الصيانات ---
elif menu == "🛠️ سجل الصيانات":
    st.header("⚙️ متابعة فترات الصيانة")
    st.info("الجزء ده هيعرض لك مواعيد تغيير الشمعات بناءً على تاريخ التركيب اللي في الشيت.")
