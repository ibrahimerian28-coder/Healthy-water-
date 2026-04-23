import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# بيانات الشيت (تأكد أن GID هو 0 بعد مسح الصفحات الأخرى أو هاته من الرابط)
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
# غالباً بعد مسح الصفحات وتسمية الأساسية Data، الـ GID بيرجع 0
GID = "0" 
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def load_data():
    try:
        # كسر الكاش لضمان رؤية التعديلات فوراً
        df = pd.read_csv(f"{DATA_URL}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 2. الواجهة الرئيسية ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.info("نظام إدارة الصيانة والعملاء")
menu = st.sidebar.radio("القائمة", ["🔍 بحث وإدارة العملاء", "➕ تعليمات إضافة عميل"])

# --- 3. صفحة البحث والعرض ---
if menu == "🔍 بحث وإدارة العملاء":
    st.header("📇 سجل العملاء الاحترافي")
    
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

    df = load_data()
    
    if not df.empty:
        # خانة البحث الشامل
        search = st.text_input("🔍 ابحث (بالاسم، الرقم، أو المنطقة)")
        
        if search:
            # البحث بذكاء في كل الخانات
            mask = df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)
            df = df[mask]

        st.write(f"عدد العملاء الحاليين: {len(df)}")
        st.markdown("---")

        for _, row in df.iterrows():
            name = row.get('الاسم', 'عميل غير مسجل')
            area = row.get('المنطقة', '---')
            # الأرقام مفصولة بفاصلة في الشيت لتعدد الأرقام
            phones_raw = str(row.get('الأرقام', ''))
            phones = [p.strip() for p in phones_raw.split(',') if p.strip()]
            loc_url = row.get('اللوكيشن', '')
            inst_date = row.get('تاريخ التركيب', '')
            cycle = row.get('دورة الصيانة', 'غير محدد')

            with st.expander(f"👤 {name} | 📍 {area}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    if pd.notna(inst_date) and str(inst_date).strip() != "" and str(inst_date).lower() != "nan":
                        st.write(f"📅 **تاريخ التركيب:** {inst_date}")
                    st.write(f"🔧 **دورة الصيانة:** كل {cycle} شهور")

                with col2:
                    if pd.notna(loc_url) and "http" in str(loc_url):
                        st.markdown(f'''<a href="{loc_url}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#ea4335; color:white; border:none; padding:12px; cursor:pointer;">📍 فتح الموقع على الخرائط</button></a>''', unsafe_allow_html=True)
                    else:
                        st.info("لا يوجد لوكيشن مسجل")

                st.markdown("**📞 أرقام التواصل:**")
                if phones:
                    for p in phones:
                        c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
                        c_p1.markdown(f"**📱 {p}**")
                        # اتصال
                        c_p2.markdown(f'''<a href="tel:{p}" style="text-decoration:none;"><button style="width:100%; background-color:#007bff; color:white; border:none; border-radius:5px; padding:5px;">📞 اتصال</button></a>''', unsafe_allow_html=True)
                        # واتساب
                        clean_p = "".join(filter(str.isdigit, p))
                        if clean_p.startswith("01"): clean_p = "2" + clean_p
                        c_p3.markdown(f'''<a href="https://wa.me/{clean_p}" style="text-decoration:none;"><button style="width:100%; background-color:#25d366; color:white; border:none; border-radius:5px; padding:5px;">💬 واتس</button></a>''', unsafe_allow_html=True)
                else:
                    st.warning("لا توجد أرقام مسجلة")
                
                st.write("---")
                st.caption("للتعديل أو الحذف، يرجى استخدام تطبيق Google Sheets مباشرة.")

    else:
        st.warning("⚠️ الشيت يبدو فارغاً أو الصفحة غير موجودة.")
        st.info("تأكد أن اسم الصفحة في الشيت هو 'Data' وأنها تحتوي على بيانات.")

# --- 4. صفحة التعليمات ---
elif menu == "➕ تعليمات إضافة عميل":
    st.header("📝 كيف تضيف عميل جديد؟")
    st.write("""
    بما أننا نستخدم نظاماً احترافياً الآن، يمكنك إضافة العميل مباشرة من تطبيق **Google Sheets** على موبايلك:
    1. افتح صفحة **Data**.
    2. أضف الاسم، ثم الأرقام (إذا كان هناك أكثر من رقم ضع بينهما فاصلة `,`).
    3. ضع رابط اللوكيشن من خرائط جوجل في خانة 'اللوكيشن'.
    4. حدد دورة الصيانة (مثلاً: 3).
    5. ارجع هنا واضغط **تحديث البيانات** وستجد الكارت ظهر فوراً.
    """)
    st.markdown(f"[اضغط هنا لفتح الشيت مباشرة](https://docs.google.com/spreadsheets/d/{SHEET_ID})")
                        
