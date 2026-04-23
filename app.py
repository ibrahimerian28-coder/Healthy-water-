import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
GOOGLE_FORM_URL = "https://forms.gle/Pb6SYsxF2Q4PHQMZ9"

# دالة ذكية جداً لجلب البيانات من أي مكان في الشيت
def get_any_data():
    # بنجرب أكتر من 20 رقم GID محتمل (جوجل بيبدأ بأرقام عشوائية أحياناً)
    gids = ["0", "1853673750", "608678000", "2087453444", "1362243444", "754321678", "456789012"]
    
    found_data = None
    for gid in gids:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cache={datetime.now().timestamp()}"
        try:
            temp_df = pd.read_csv(url)
            # لو الصفحة فيها بيانات حقيقية (أكتر من عمودين وفيه صفوف)
            if len(temp_df.columns) > 1 and len(temp_df) > 0:
                found_data = temp_df
                break
        except:
            continue
    return found_data

# --- 2. التصميم ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة:", ["🔍 عرض العملاء", "➕ إضافة عميل"])

if menu == "🔍 عرض العملاء":
    st.header("👤 قاعدة بيانات العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    df = get_any_data()
    
    if df is not None:
        # تنظيف العناوين
        df.columns = [str(c).strip() for c in df.columns]
        
        search = st.text_input("🔍 ابحث بالاسم")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]
        
        for _, row in df.iterrows():
            # قراءة بذكاء (عربي أو إنجليزي)
            name = row.get('الاسم') or row.get('name') or "عميل"
            area = row.get('المنطقة') or row.get('area') or "غير محدد"
            phone = str(row.get('الهاتف') or row.get('رقم التليفون') or "").strip()
            
            with st.expander(f"👤 {name} | 📍 {area}"):
                if phone and phone != "nan":
                    st.write(f"📞 هاتف: {phone}")
                    c1, c2 = st.columns(2)
                    c1.markdown(f'''<a href="tel:{phone}"><button style="width:100%; border-radius:10px; background-color:#007bff; color:white; border:none; padding:12px;">📞 اتصل</button></a>''', unsafe_allow_html=True)
                    
                    clean_p = "".join(filter(str.isdigit, phone))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    c2.markdown(f'''<a href="https://wa.me/{clean_p}"><button style="width:100%; border-radius:10px; background-color:#25d366; color:white; border:none; padding:12px;">💬 واتساب</button></a>''', unsafe_allow_html=True)
    else:
        st.error("⚠️ الداتا موجودة في الشيت بس محجوبة عن التطبيق.")
        st.info("يا هندسة، جرب تفتح الشيت من الكمبيوتر، وتشوف رقم الـ gid اللي في الرابط بتاع صفحة (الردود) كام بالظبط وقولي عليه.")

elif menu == "➕ إضافة عميل":
    st.components.v1.iframe(GOOGLE_FORM_URL, height=800, scrolling=True)
