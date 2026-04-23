import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

SHEET_ID = "1Dpy1_KVLN_Ejch7LSjuewLvdmSM270skJN-2bBkcIiI"
DATA_GID = "0"
MAINT_GID = "2120582392"

def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(f"{url}&cache={datetime.now().timestamp()}")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
menu = st.sidebar.radio("القائمة", ["🔍 بحث وإدارة العملاء", "📋 جدول صيانة الأسبوع", "➕ تسجيل عميل جديد", "🔧 إضافة سجل صيانة"])

# --- 3. صفحة البحث وإدارة العملاء ---
if menu == "🔍 بحث وإدارة العملاء":
    st.header("📇 سجل العملاء الاحترافي")
    
    df_customers = load_data(DATA_GID)
    df_maint = load_data(MAINT_GID)

    if not df_customers.empty:
        search = st.text_input("🔍 ابحث بالاسم أو الرقم")
        if search:
            df_customers = df_customers[df_customers.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)]

        for _, row in df_customers.iterrows():
            name = str(row.get('الاسم', '---')).strip()
            area = row.get('المنطقة', '---')
            try:
                cycle = int(row.get('دورة الصيانة', 3))
            except:
                cycle = 3
            
            # --- معالجة سجل الصيانات للعميل ---
            customer_history = pd.DataFrame()
            if not df_maint.empty and 'الاسم' in df_maint.columns:
                # فلترة الصيانات الخاصة بهذا العميل فقط
                df_maint['الاسم'] = df_maint['الاسم'].astype(str).str.strip()
                customer_history = df_maint[df_maint['الاسم'] == name].copy()
                
                # تحويل التاريخ لنوع تاريخ وتصفية السطور الفارغة
                customer_history['تاريخ الزيارة'] = pd.to_datetime(customer_history['تاريخ الزيارة'], errors='coerce')
                customer_history = customer_history.dropna(subset=['تاريخ الزيارة'])
                
                # الترتيب التلقائي من الأحدث للأقدم
                customer_history = customer_history.sort_values(by='تاريخ الزيارة', ascending=False)

            with st.expander(f"👤 {name} | 📍 {area}"):
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.write(f"🏠 **العنوان:** {row.get('العنوان', '---')}")
                    st.write(f"🔧 **الدورة:** كل {cycle} شهور")
                
                with c2:
                    if not customer_history.empty:
                        last_date = customer_history['تاريخ الزيارة'].iloc[0]
                        next_date = last_date + timedelta(days=cycle*30)
                        st.metric("الصيانة القادمة", next_date.strftime('%Y-%m-%d'))
                        st.caption(f"آخر زيارة: {last_date.strftime('%Y-%m-%d')}")
                    else:
                        st.info("لا توجد سجلات")

                with c3:
                    loc_url = row.get('اللوكيشن', '')
                    if pd.notna(loc_url) and "http" in str(loc_url):
                        st.markdown(f'<a href="{loc_url}" target="_blank"><button style="width:100%; border-radius:10px; background-color:#ea4335; color:white; border:none; padding:10px; cursor:pointer;">📍 الخريطة</button></a>', unsafe_allow_html=True)
                    
                    if not customer_history.empty:
                        special = str(customer_history['تاريخ تذكير خاص'].iloc[0])
                        if special != "nan" and special != "":
                            st.warning(f"🔔 موعد خاص: {special}")

                # --- عرض جدول سجل الصيانات بالكامل ---
                st.markdown("### 📜 سجل الصيانات السابقة")
                if not customer_history.empty:
                    # تحويل التاريخ لشكل نصي للعرض فقط
                    display_df = customer_history.copy()
                    display_df['تاريخ الزيارة'] = display_df['تاريخ الزيارة'].dt.strftime('%Y-%m-%d')
                    
                    # اختيار الأعمدة المهمة للعرض
                    cols_to_show = ['تاريخ الزيارة', 'P1', 'P2', 'P3', 'ممبرين', 'بوست كاربون', 'كالسيت', 'انفرا ريد', 'اخري', 'التكلفه', 'ملاحظات']
                    # التأكد من وجود الأعمدة في الشيت
                    available_cols = [c for c in cols_to_show if c in display_df.columns]
                    
                    st.table(display_df[available_cols])
                else:
                    st.write("لم يتم تسجيل أي زيارات سابقة لهذا العميل.")

                st.markdown("---")
                st.write("**📞 أرقام التواصل:**")
                phones_raw = str(row.get('الأرقام', ''))
                phones = [p.strip() for p in phones_raw.split(',') if p.strip()]
                for p in phones:
                    cp1, cp2, cp3 = st.columns([2,1,1])
                    cp1.write(f"📱 {p}")
                    cp2.markdown(f'<a href="tel:{p}"><button style="width:100%; background-color:#007bff; color:white; border:none; border-radius:5px; padding:5px;">📞 اتصال</button></a>', unsafe_allow_html=True)
                    clean_p = "".join(filter(str.isdigit, p))
                    if clean_p.startswith("01"): clean_p = "2" + clean_p
                    cp3.markdown(f'<a href="https://wa.me/{clean_p}"><button style="width:100%; background-color:#25d366; color:white; border:none; border-radius:5px; padding:5px;">💬 واتس</button></a>', unsafe_allow_html=True)

# (بقية الكود الخاص بالإضافة يبقى كما هو دون تغيير)
elif menu == "📋 جدول صيانة الأسبوع":
    st.header("🗓️ العملاء المطلوب زيارتهم")
    st.info("قريباً: سيتم عرض العملاء الذين حان موعدهم تلقائياً هنا.")

elif menu == "➕ تسجيل عميل جديد":
    st.header("📝 تسجيل بيانات عميل")
    with st.form("new_customer"):
        n_name = st.text_input("الاسم بالكامل")
        n_phones = st.text_input("الأرقام (افصل بفاصلة)")
        n_area = st.selectbox("المنطقة", [
            "حدائق العاصمة", "مدينتي", "الشروق", "بدر", "العبور", 
            "التجمع الاول", "التجمع الخامس", "الرحاب", "المستقبل", 
            "جسر السويس", "مصر الجديده", "مدينه نصر", "عين شمس", 
            "المرج", "الضاهر", "الجيزة", "الهرم", "٦ اكتوبر", "شبرا", "اخري"
        ])
        n_address = st.text_area("العنوان")
        n_loc = st.text_input("اللوكيشن")
        n_cycle = st.selectbox("الدورة (شهور)", [1,2,3,4,5,6], index=2)
        n_date = st.date_input("التاريخ", datetime.now())
        if st.form_submit_button("عرض السطر"):
            row = [n_name, n_phones, n_address, n_area, n_loc, n_date.strftime('%Y-%m-%d'), n_cycle]
            st.code(" | ".join(map(str, row)))

elif menu == "🔧 إضافة سجل صيانة":
    st.header("📝 تسجيل زيارة صيانة")
    df_customers = load_data(DATA_GID)
    if not df_customers.empty:
        with st.form("maint_entry"):
            m_name = st.selectbox("اسم العميل", df_customers['الاسم'].tolist())
            m_date = st.date_input("تاريخ الزيارة", datetime.now())
            col_a, col_b = st.columns(2)
            with col_a:
                p1, p2, p3, mem = st.checkbox("P1"), st.checkbox("P2"), st.checkbox("P3"), st.checkbox("ممبرين")
            with col_b:
                post, calc, infra = st.checkbox("بوست كاربون"), st.checkbox("كالسيت"), st.checkbox("انفرا ريد")
                other = st.text_input("أخرى")
            m_cost = st.number_input("التكلفة", min_value=0)
            m_notes = st.text_area("ملاحظات")
            m_special = st.date_input("تذكير خاص", value=None)
            if st.form_submit_button("تجهيز السطر"):
                def f_c(v): return "تم" if v else "-"
                m_row = [m_name, m_date.strftime('%Y-%m-%d'), f_c(p1), f_c(p2), f_c(p3), f_c(mem), f_c(post), f_c(calc), f_c(infra), other, m_cost, m_notes, m_special.strftime('%Y-%m-%d') if m_special else ""]
                st.code(" | ".join(map(str, m_row)))
