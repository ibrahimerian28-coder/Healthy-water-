import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات والروابط ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# رابط الشيت للقراءة (Direct CSV)
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# رابط الفورم اللي إنت بعته (تم وضعه في مكانه)
GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

def get_google_data(url):
    try:
        # إضافة timestamp لمنع التخزين المؤقت (Cache) وضمان رؤية أحدث البيانات
        return pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.markdown("---")
menu = st.sidebar.radio("القائمة الرئيسية", ["🔍 إدارة العملاء وتواصل", "➕ إضافة عميل جديد"])

# --- 3. إدارة العملاء وتواصل سريع ---
if menu == "🔍 إدارة العملاء وتواصل":
    st.header("👤 قاعدة بيانات العملاء")
    
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

    df = get_google_data(DATA_URL)
    
    if not df.empty:
        search = st.text_input("🔍 ابحث بالاسم أو المنطقة")
        if search:
            # البحث بذكاء في كل الأعمدة
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        # عرض العملاء في شكل بطاقات (Expander)
        for _, row in df.iterrows():
            # ملحوظة: الكود بيحاول يلاقي اسم العمود سواء بالعربي أو الإنجليزي
            name = row.get('الاسم') or row.get('name') or row.get('Name') or "عميل بدون اسم"
            area = row.get('المنطقة') or row.get('area') or row.get('Area') or "منطقة غير محددة"
            phone = str(row.get('الهاتف') or row.get('phone') or row.get('Phone') or "").strip()
            address = row.get('العنوان') or row.get('address') or row.get('Address') or "لا يوجد عنوان"

            with st.expander(f"👤 {name} | 📍 {area}"):
                st.write(f"🏠 **العنوان:** {address}")
                
                if phone:
                    st.write(f"📞 **الهاتف:** {phone}")
                    cola, colb = st.columns(2)
                    
                    # زر الاتصال
                    cola.markdown(f'''<a href="tel:{phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:10px; cursor:pointer;">📞 اتصل الآن</button></a>''', unsafe_allow_html=True)
                    
                    # زر الواتساب (تنظيف الرقم)
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"):
                        clean_p = "2" + clean_phone if 'clean_phone' in locals() else "2" + clean_p
                    
                    colb.markdown(f'''<a href="https://wa.me/{clean_p}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:10px; cursor:pointer;">💬 واتساب</button></a>''', unsafe_allow_html=True)
    else:
        st.warning("الجدول فاضي حالياً أو الرابط غير متاح للقراءة.")
        st.info("تأكد إنك سجلت ردود في الفورم وربطتها بالشيت.")

# --- 4. إضافة عميل جديد ---
elif menu == "➕ إضافة عميل جديد":
    st.header("➕ تسجيل عميل جديد")
    st.info("سجل البيانات في النموذج بالأسفل، وستظهر في الجدول تلقائياً.")
    
    # عرض الـ Google Form داخل التطبيق
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800, scrolling=True)
