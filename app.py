import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت الأساسي
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"

# ⚠️ ملاحظة: جرب gid=0 ولو البيانات مظهرتش، افتح الشيت وشوف رقم gid بتاع صفحة "Form Responses 2" كام
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

def get_google_data(url):
    try:
        return pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# --- 2. الواجهة ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["🔍 إدارة العملاء", "➕ إضافة عميل جديد"])

if menu == "🔍 إدارة العملاء":
    st.header("👤 قاعدة بيانات العملاء")
    st.info("اضغط على 'تحديث' بعد تسجيل عميل جديد بـ 5 ثوانٍ")
    
    if st.button("🔄 تحديث القائمة"):
        st.rerun()

    df = get_google_data(DATA_URL)
    
    if not df.empty:
        search = st.text_input("🔍 ابحث بالاسم")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        for _, row in df.iterrows():
            name = row.get('الاسم') or row.get('name') or "عميل"
            phone = str(row.get('الهاتف') or row.get('رقم التليفون') or "").strip()
            
            with st.expander(f"👤 {name}"):
                if phone:
                    cola, colb = st.columns(2)
                    cola.markdown(f'''<a href="tel:{phone}"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:10px;">📞 اتصل</button></a>''', unsafe_allow_html=True)
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    colb.markdown(f'''<a href="https://wa.me/{clean_p}"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:10px;">💬 واتساب</button></a>''', unsafe_allow_html=True)
    else:
        st.warning("البيانات لم تظهر بعد. تأكد من ربط الفورم بالشيت (Unlink/Relink).")

elif menu == "➕ إضافة عميل جديد":
    st.header("➕ تسجيل بيانات العميل")
    st.warning("⚠️ تنبيه: لازم تضغط على زرار 'إرسال' أو 'Submit' اللي داخل النموذج بالأسفل لحفظ البيانات.")
    
    # عرض الـ Google Form
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800, scrolling=True)
    
    if st.button("✅ أتممت التسجيل.. ارجع للجدول"):
        st.info("جاري التحويل...")
        # هنا مكن نخليه يرجع لصفحة الإدارة أوتوماتيك
        st.balloons()
