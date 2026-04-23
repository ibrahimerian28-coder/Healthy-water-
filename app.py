import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
GID = "0" # تأكد أن صفحة Data هي الأولى
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# رابط الفورم القديم (هنستخدمه كبوابة خلفية للإرسال عشان نسهل عليك الموضوع)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdvv3M7XlqXqXqXqXq/formResponse" # ده مثال، هتحتاج رابط الـ POST بتاع فورم جوجل لو عايز إرسال مباشر

def load_data():
    try:
        return pd.read_csv(f"{DATA_URL}&cache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["🔍 بحث وإدارة", "➕ إضافة عميل جديد"])

# --- 3. صفحة البحث والإدارة ---
if menu == "🔍 بحث وإدارة":
    st.header("📇 سجل العملاء")
    df = load_data()
    
    if not df.empty:
        search = st.text_input("🔍 ابحث بالاسم، الرقم، أو المنطقة")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for index, row in df.iterrows():
            with st.expander(f"👤 {row.get('الاسم', '---')} | 📍 {row.get('المنطقة', '---')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    st.write(f"🔧 **الصيانة:** كل {row.get('دورة الصيانة', '3')} شهور")
                with c2:
                    loc = row.get('اللوكيشن', '')
                    if pd.notna(loc) and "http" in str(loc):
                        st.markdown(f'<a href="{loc}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#ea4335; color:white; border:none; padding:10px;">📍 فتح اللوكيشن</button></a>', unsafe_allow_html=True)
                
                st.write("📞 **التواصل:**")
                phones = str(row.get('الأرقام', '')).split(',')
                for p in phones:
                    p = p.strip()
                    if p:
                        cp1, cp2, cp3 = st.columns([2,1,1])
                        cp1.write(f"📱 {p}")
                        cp2.markdown(f'<a href="tel:{p}"><button style="width:100%; background-color:#007bff; color:white; border:none; border-radius:5px;">📞 اتصال</button></a>', unsafe_allow_html=True)
                        clean_p = "".join(filter(str.isdigit, p))
                        if clean_p.startswith("01"): clean_p = "2" + clean_p
                        cp3.markdown(f'<a href="https://wa.me/{clean_p}"><button style="width:100%; background-color:#25d366; color:white; border:none; border-radius:5px;">💬 واتس</button></a>', unsafe_allow_html=True)

# --- 4. صفحة الإضافة (الفورم الاحترافي) ---
elif menu == "➕ إضافة عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    
    # تنبيه بسيط: بما إننا معندناش Apps Script، هنستخدم فورم جوجل كـ "خزان" خلفي
    # أو الأسهل حالياً إنك تضيف في الشيت ويسمع هنا فوراً
    st.warning("⚠️ ميزة الحذف والتعديل المباشر تتطلب فتح Apps Script من كمبيوتر (مرة واحدة فقط).")
    
    with st.form("add_form"):
        name = st.text_input("اسم العميل")
        phones = st.text_input("أرقام الهاتف (ضع فاصلة بين الأرقام)")
        area = st.selectbox("المنطقة", ["الظاهر", "العباسية", "الوايلي", "أخرى"])
        address = st.text_area("العنوان")
        loc = st.text_input("رابط اللوكيشن")
        cycle = st.slider("دورة الصيانة (شهور)", 1, 12, 3)
        
        submitted = st.form_submit_button("حفظ العميل")
        if submitted:
            st.info("جاري الحفظ... (بما أننا في النسخة التجريبية، يرجى التأكد من إضافة البيانات في صفحة Data بالشيت)")
            # هنا ممكن نربط بـ Google Form POST لإرسال البيانات أوتوماتيكياً
