import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# --- بيانات الربط المحدثة بالـ GID الجديد ---
SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"              # صفحة البيانات الأساسية
MAINT_GID = "2120582392"    # صفحة سجل الصيانات (الرقم اللي إنت بعته)

# قائمة المناطق المعتمدة
MANATEQ = [
    "حدائق العاصمة", "مدينتي", "الشروق", "بدر", "العبور", 
    "التجمع الاول", "التجمع الخامس", "الرحاب", "المستقبل", 
    "جسر السويس", "مصر الجديده", "مدينه نصر", "عين شمس", 
    "المرج", "الضاهر", "الجيزة", "الهرم", "٦ اكتوبر", "شبرا", "اخري"
]

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        # كسر الكاش لضمان رؤية التعديلات فوراً
        df = pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.markdown("---")
menu = st.sidebar.radio("القائمة الرئيسية", ["🔍 بحث وإدارة العملاء", "📋 جدول صيانة الأسبوع", "➕ تسجيل عميل جديد", "🔧 إضافة سجل صيانة"])

# --- 3. صفحة البحث وإدارة العملاء ---
if menu == "🔍 بحث وإدارة العملاء":
    st.header("📇 سجل العملاء الاحترافي")
    
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)

    if not df_customers.empty:
        search = st.text_input("🔍 ابحث (بالاسم، الرقم، أو المنطقة)")
        if search:
            df_customers = df_customers[df_customers.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for _, row in df_customers.iterrows():
            name = row.get('الاسم', '---')
            area = row.get('المنطقة', '---')
            cycle_val = row.get('دورة الصيانة', 3)
            try:
                cycle = int(cycle_val)
            except:
                cycle = 3
            
            # جلب آخر صيانة للعميل
            last_visit = pd.DataFrame()
            if not df_maint.empty and 'الاسم' in df_maint.columns:
                last_visit = df_maint[df_maint['الاسم'] == name].tail(1)

            with st.expander(f"👤 {name} | 📍 {area}"):
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    st.write(f"🔧 **دورة الصيانة:** كل {cycle} شهور")
                
                with c2:
                    # حساب ميعاد الصيانة القادم
                    if not last_visit.empty:
                        try:
                            last_date_str = str(last_visit['تاريخ الزيارة'].values[0])
                            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
                            next_date = last_date + timedelta(days=cycle*30)
                            st.metric("الصيانة القادمة", next_date.strftime('%Y-%m-%d'))
                            st.caption(f"آخر زيارة: {last_date_str}")
                        except:
                            st.write("⚠️ تأكد من تنسيق التاريخ في الشيت (YYYY-MM-DD)")
                    else:
                        st.info("لا توجد سجلات صيانة")

                with c3:
                    loc_url = row.get('اللوكيشن', '')
                    if pd.notna(loc_url) and "http" in str(loc_url):
                        st.markdown(f'<a href="{loc_url}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#ea4335; color:white; border:none; padding:10px; cursor:pointer;">📍 الموقع على الخريطة</button></a>', unsafe_allow_html=True)
                    
                    # التذكير الخاص
                    if not last_visit.empty and 'تاريخ تذكير خاص' in last_visit.columns:
                        special = str(last_visit['تاريخ تذكير خاص'].values[0])
                        if special != "nan" and special != "":
                            st.warning(f"🔔 موعد خاص: {special}")

                st.markdown("---")
                st.write("**📞 أرقام التواصل:**")
                phones_raw = str(row.get('الأرقام', ''))
                phones = [p.strip() for p in phones_raw.split(',') if p.strip()]
                for p in phones:
                    cp1, cp2, cp3 = st.columns([2,1,1])
                    cp1.write(f"📱 {p}")
                    cp2.markdown(f'<a href="tel:{p}"><button style="width:100%; background-color:#007bff; color:white; border:none; border-radius:5px; padding:5px; width:100%;">📞 اتصال</button></a>', unsafe_allow_html=True)
                    clean_p = "".join(filter(str.isdigit, p))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    cp3.markdown(f'<a href="https://wa.me/{clean_p}"><button style="width:100%; background-color:#25d366; color:white; border:none; border-radius:5px; padding:5px; width:100%;">💬 واتس</button></a>', unsafe_allow_html=True)

# --- 4. صفحة جدول صيانة الأسبوع ---
elif menu == "📋 جدول صيانة الأسبوع":
    st.header("🗓️ العملاء المطلوب زيارتهم")
    st.info("هذه الميزة تعتمد على مقارنة تاريخ اليوم بموعد الصيانة القادم لكل عميل.")
    # يمكن هنا مستقبلاً إضافة كود يفلتر العملاء الذين حان موعدهم خلال 7 أيام

# --- 5. صفحة تسجيل عميل جديد ---
elif menu == "➕ تسجيل عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    with st.form("new_customer"):
        n_name = st.text_input("الاسم بالكامل")
        n_phones = st.text_input("الأرقام (افصل بفاصلة لو أكثر من رقم)")
        n_area = st.selectbox("المنطقة", MANATEQ)
        n_address = st.text_area("العنوان بالتفصيل")
        n_loc = st.text_input("رابط اللوكيشن من جوجل مابس")
        n_cycle = st.selectbox("دورة الصيانة (شهور)", [1,2,3,4,5,6], index=2)
        n_date = st.date_input("تاريخ أول تركيب", datetime.now())
        
        if st.form_submit_button("عرض السطر للنسخ للشيت"):
            row = [n_name, n_phones, n_address, n_area, n_loc, n_date.strftime('%Y-%m-%d'), n_cycle]
            st.code(" | ".join(map(str, row)))
            st.success("انسخ السطر وضعه في صفحة Data")

# --- 6. صفحة إضافة سجل صيانة ---
elif menu == "🔧 إضافة سجل صيانة":
    st.header("📝 تسجيل زيارة صيانة (شمعات)")
    df_customers = load_data(DATA_GID)
    
    if not df_customers.empty:
        with st.form("maint_entry"):
            m_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
            m_date = st.date_input("تاريخ الزيارة", datetime.now())
            
            st.markdown("#### المستبدل (Check Box):")
            col_a, col_b = st.columns(2)
            with col_a:
                p1 = st.checkbox("الشمعة 1 (P1)")
                p2 = st.checkbox("الشمعة 2 (P2)")
                p3 = st.checkbox("الشمعة 3 (P3)")
                mem = st.checkbox("ممبرين")
            with col_b:
                post = st.checkbox("بوست كاربون")
                calc = st.checkbox("كالسيت")
                infra = st.checkbox("انفرا ريد")
                other = st.text_input("أخرى")
            
            m_cost = st.number_input("التكلفة", min_value=0)
            m_notes = st.text_area("ملاحظات الزيارة")
            m_special = st.date_input("تاريخ تذكير خاص (اختياري)", value=None)
            
            if st.form_submit_button("تجهيز سطر الصيانة"):
                def f_c(v): return "تم" if v else "-"
                m_row = [m_name, m_date.strftime('%Y-%m-%d'), f_c(p1), f_c(p2), f_c(p3), f_c(mem), f_c(post), f_c(calc), f_c(infra), other, m_cost, m_notes, m_special.strftime('%Y-%m-%d') if m_special else ""]
                st.code(" | ".join(map(str, m_row)))
                st.success("انسخ السطر وضعه في صفحة Maintenance")
    else:
        st.error("سجل عملاء أولاً لتتمكن من إضافة صيانات لهم.")
