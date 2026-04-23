import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
# تأكد أن اسم الصفحة في الشيت هو Data ورقم الـ GID هو 0
GID = "0" 
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def load_data():
    try:
        df = pd.read_csv(f"{DATA_URL}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("الانتقال إلى:", ["🔍 إدارة ومتابعة العملاء", "➕ تسجيل عميل جديد"])

# قائمة المناطق اللي إنت بعتها
MANATEQ = [
    "حدائق العاصمة", "مدينتي", "الشروق", "بدر", "العبور", 
    "التجمع الاول", "التجمع الخامس", "الرحاب", "المستقبل", 
    "جسر السويس", "مصر الجديده", "مدينه نصر", "عين شمس", 
    "المرج", "الضاهر", "الجيزة", "الهرم", "٦ اكتوبر", "شبرا", "اخري"
]

# --- 3. صفحة البحث والإدارة ---
if menu == "🔍 إدارة ومتابعة العملاء":
    st.header("📇 سجل العملاء")
    
    if st.button("🔄 تحديث"):
        st.rerun()

    df = load_data()
    
    if not df.empty:
        search = st.text_input("🔍 ابحث (بالاسم، الرقم، أو المنطقة)")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for index, row in df.iterrows():
            name = row.get('الاسم', '---')
            area = row.get('المنطقة', '---')
            phones_raw = str(row.get('الأرقام', ''))
            phones = [p.strip() for p in phones_raw.split(',') if p.strip()]
            loc = row.get('اللوكيشن', '')
            inst_date = row.get('تاريخ التركيب', '')
            cycle = row.get('دورة الصيانة', '3')

            with st.expander(f"👤 {name} | 📍 {area}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    if pd.notna(inst_date) and str(inst_date).strip() != "" and str(inst_date).lower() != "nan":
                        st.write(f"📅 **التركيب:** {inst_date}")
                    st.write(f"🔧 **دورة الصيانة:** كل {cycle} شهور")
                
                with c2:
                    if pd.notna(loc) and "http" in str(loc):
                        st.markdown(f'<a href="{loc}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#ea4335; color:white; border:none; padding:10px; cursor:pointer;">📍 فتح اللوكيشن على الخرائط</button></a>', unsafe_allow_html=True)
                
                st.write("**📞 أرقام التواصل:**")
                for p in phones:
                    cp1, cp2, cp3 = st.columns([2,1,1])
                    cp1.write(f"📱 {p}")
                    cp2.markdown(f'<a href="tel:{p}"><button style="width:100%; background-color:#007bff; color:white; border:none; border-radius:5px;">📞 اتصال</button></a>', unsafe_allow_html=True)
                    clean_p = "".join(filter(str.isdigit, p))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    cp3.markdown(f'<a href="https://wa.me/{clean_p}"><button style="width:100%; background-color:#25d366; color:white; border:none; border-radius:5px;">💬 واتس</button></a>', unsafe_allow_html=True)

# --- 4. صفحة الإضافة (واجهة تسجيل) ---
elif menu == "➕ تسجيل عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    
    with st.form("add_form"):
        st.info("سجل البيانات هنا ثم انقلها للشيت يدوياً حالياً لضمان الدقة")
        name = st.text_input("الاسم بالكامل")
        # تعدد الأرقام
        phones = st.text_input("أرقام الهاتف (لو أكتر من رقم افصل بينهم بفاصلة , )")
        # القائمة اللي إنت طلبتها
        area = st.selectbox("اختر المنطقة", MANATEQ)
        address = st.text_area("العنوان بالتفصيل")
        loc_link = st.text_input("رابط اللوكيشن من جوجل مابس")
        maint_cycle = st.selectbox("دورة الصيانة (شهور)", [1, 2, 3, 4, 5, 6], index=2)
        inst_date = st.date_input("تاريخ التركيب", value=None)
        
        if st.form_submit_button("عرض البيانات للنسخ"):
            st.success("البيانات جاهزة للنسخ للشيت:")
            st.code(f"{name} | {phones} | {address} | {area} | {loc_link} | {inst_date} | {maint_cycle}")

    st.markdown(f"[🔗 اضغط هنا لفتح الشيت مباشرة وإضافة السطر](https://docs.google.com/spreadsheets/d/{SHEET_ID})")
