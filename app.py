import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# البيانات الأساسية
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
# تم وضع رقم الـ GID اللي إنت بعته هنا
GID_NUMBER = "642262765" 

# رابط سحب البيانات المباشر
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_NUMBER}"
GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

def get_google_data():
    try:
        # كسر الكاش لضمان رؤية البيانات الجديدة فوراً
        return pd.read_csv(f"{DATA_URL}&cache={datetime.now().timestamp()}")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return pd.DataFrame()

# --- 2. التصميم الواجهة ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.write("إدارة صيانة الفلاتر")
st.sidebar.markdown("---")
menu = st.sidebar.radio("القائمة الرئيسية:", ["🔍 إدارة العملاء والتواصل", "➕ إضافة عميل جديد"])

# --- 3. صفحة عرض العملاء ---
if menu == "🔍 إدارة العملاء والتواصل":
    st.header("👤 قاعدة بيانات العملاء")
    
    col_refresh, col_search = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 تحديث"):
            st.rerun()

    df = get_google_data()
    
    if not df.empty:
        # تنظيف أسامي الأعمدة
        df.columns = [str(c).strip() for c in df.columns]
        
        with col_search:
            search = st.text_input("🔍 ابحث بالاسم أو المنطقة", placeholder="اكتب هنا للبحث...")
        
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        # ترتيب: الأحدث يظهر أولاً
        if 'Timestamp' in df.columns:
            df = df.sort_values(by='Timestamp', ascending=False)
        elif 'الطابع الزمني' in df.columns:
            df = df.sort_values(by='الطابع الزمني', ascending=False)

        st.write(f"✅ تم العثور على {len(df)} عميل")
        st.markdown("---")

        for _, row in df.iterrows():
            # استخراج البيانات بذكاء حسب مسميات الأعمدة في الشيت
            name = row.get('الاسم') or row.get('name') or row.get('Name') or "عميل"
            area = row.get('المنطقة') or row.get('area') or row.get('Area') or "غير محدد"
            phone = str(row.get('الهاتف') or row.get('رقم التليفون') or row.get('Phone') or "").strip()
            address = row.get('العنوان') or row.get('address') or "لا يوجد عنوان"

            with st.expander(f"👤 {name} | 📍 {area}"):
                st.write(f"🏠 **العنوان:** {address}")
                
                if phone and phone != "nan" and phone != "":
                    st.write(f"📞 **الهاتف:** {phone}")
                    c1, c2 = st.columns(2)
                    
                    # زر الاتصال
                    c1.markdown(f'''<a href="tel:{phone}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:12px; cursor:pointer; width:100%;">📞 اتصل الآن</button></a>''', unsafe_allow_html=True)
                    
                    # زر الواتساب
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    c2.markdown(f'''<a href="https://wa.me/{clean_p}" style="text-decoration:none;"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:12px; cursor:pointer; width:100%;">💬 واتساب</button></a>''', unsafe_allow_html=True)
                else:
                    st.warning("رقم الهاتف غير مسجل")
    else:
        st.warning("البيانات لم تظهر بعد. تأكد من إدخال بيانات في الفورم.")

# --- 4. صفحة إضافة عميل ---
elif menu == "➕ إضافة عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    st.info("قم بملء النموذج بالأسفل واضغط على 'إرسال' أو 'Submit'")
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800, scrolling=True)
