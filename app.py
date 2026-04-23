import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت الأساسي
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"

# رابط الفورم
GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

def get_google_data():
    # بنجرب أكتر من GID مشهور لردود النماذج أوتوماتيكياً
    gids = ["0", "1853673750", "608678000", "2087453444"] 
    
    for gid in gids:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cache={datetime.now().timestamp()}"
        try:
            df = pd.read_csv(url)
            # لو لقينا جدول وفيه أكتر من عمود، يبقى هي دي الصفحة المطلوبة
            if len(df.columns) > 1:
                return df
        except:
            continue
    return pd.DataFrame()

# --- 2. الواجهة ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["🔍 إدارة العملاء", "➕ إضافة عميل جديد"])

if menu == "🔍 إدارة العملاء":
    st.header("👤 قاعدة بيانات العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    df = get_google_data()
    
    if not df.empty:
        # تنظيف العناوين
        df.columns = [str(c).strip() for c in df.columns]
        
        search = st.text_input("🔍 ابحث بالاسم")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
            
        for _, row in df.iterrows():
            # محاولة قراءة الأعمدة بأي مسمى متاح
            name = row.get('الاسم') or row.get('name') or row.get('Name') or "عميل"
            phone = str(row.get('الهاتف') or row.get('رقم التليفون') or row.get('Phone') or "").strip()
            area = row.get('المنطقة') or row.get('area') or "غير محدد"
            
            with st.expander(f"👤 {name} | 📍 {area}"):
                if phone and phone != "nan":
                    cola, colb = st.columns(2)
                    cola.markdown(f'''<a href="tel:{phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:10px;">📞 اتصل</button></a>''', unsafe_allow_html=True)
                    
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    colb.markdown(f'''<a href="https://wa.me/{clean_p}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:10px;">💬 واتساب</button></a>''', unsafe_allow_html=True)
                else:
                    st.write("رقم الهاتف غير مسجل")
    else:
        st.warning("⚠️ الداتا لسه مظهرتش في الشيت.")
        st.info("تأكد إنك فاتح الشيت وعامل Share -> Anyone with link can view")

elif menu == "➕ إضافة عميل جديد":
    st.header("➕ تسجيل بيانات العميل")
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800, scrolling=True)
