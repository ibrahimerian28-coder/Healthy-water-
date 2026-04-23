import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"

# الحركة دي بتخلينا نقرأ الشيت كله ونختار آخر صفحة اتعملت (اللي فيها الردود)
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

def get_google_data(url):
    try:
        # كسر الكاش عشان يقرأ اللحظة الحالية
        return pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# --- 2. الواجهة ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["🔍 إدارة العملاء", "➕ إضافة عميل جديد"])

if menu == "🔍 إدارة العملاء":
    st.header("👤 قاعدة بيانات العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    df = get_google_data(DATA_URL)
    
    if not df.empty:
        # البحث
        search = st.text_input("🔍 ابحث بالاسم")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        # ترتيب البيانات بحيث الأحدث يظهر فوق
        if 'Timestamp' in df.columns:
            df = df.sort_values(by='Timestamp', ascending=False)
            
        for _, row in df.iterrows():
            # بنحاول نقرأ الأعمدة بأي اسم (عربي أو إنجليزي)
            name = row.get('الاسم') or row.get('name') or "عميل جديد"
            phone = str(row.get('الهاتف') or row.get('رقم التليفون') or "").strip()
            area = row.get('المنطقة') or row.get('area') or "غير محدد"
            
            with st.expander(f"👤 {name} | 📍 {area}"):
                st.write(f"📅 تاريخ التسجيل: {row.get('Timestamp', 'غير معروف')}")
                if phone:
                    cola, colb = st.columns(2)
                    cola.markdown(f'''<a href="tel:{phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:10px;">📞 اتصل</button></a>''', unsafe_allow_html=True)
                    
                    # تنظيف رقم الواتساب
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    
                    colb.markdown(f'''<a href="https://wa.me/{clean_p}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:10px;">💬 واتساب</button></a>''', unsafe_allow_html=True)
    else:
        st.warning("البيانات لسه مظهرتش. تأكد من عمل Unlink و Re-link في الفورم.")

elif menu == "➕ إضافة عميل جديد":
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800)
