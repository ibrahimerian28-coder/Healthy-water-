import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
st.set_page_config(page_title="Healthy Water", layout="wide")

LOGO_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/logo.png"
BG_URL = "https://raw.githubusercontent.com/alshatby/healthy-water-/main/background.png"

# --- 2. إدارة البيانات ---
def load_db(file, cols):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_db(df, file): df.to_csv(file, index=False)

C_COLS = ['id', 'اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'الموقع', 'دورة الصيانة', 'تاريخ الزيارة القادمة', 'تاريخ آخر زيارة']
H_COLS = ['id_عميل', 'اسم العميل', 'تاريخ الزيارة', 'التفاصيل', 'المبلغ']
S_COLS = ['العنصر', 'الكميه', 'سعر الوحده', 'القيمه الاجماليه']

df_c = load_db("customers_final.csv", C_COLS)
df_h = load_db("history_final.csv", H_COLS)
df_s = load_db("stock_final.csv", S_COLS)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.image(LOGO_URL, width=150)
    st.title("💧 Healthy Water")
    pwd = st.text_input("باسورد المدير", type="password")
    if st.button("دخول الإدارة"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة الجانبية ---
st.sidebar.image(LOGO_URL, width=80)
menu = st.sidebar.radio("القائمة الرئيسية", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات", "المخزن"])

# --- 5. صفحة تسجيل عميل جديد ---
if menu == "تسجيل عميل جديد":
    st.header("📝 تسجيل عميل جديد")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("👤 اسم العميل")
        phones = st.text_input("📞 الهواتف (فاصلة بين الأرقام)")
        addr = st.text_area("🏠 العنوان")
        area = st.text_input("📍 المنطقة")
        loc = st.text_input("🔗 رابط اللوكيشن من جوجل مابس")
        cycle = st.number_input("📅 دورة الصيانة (شهور)", min_value=1, value=3)
        last_v = st.date_input("🗓️ تاريخ آخر زيارة", value=datetime.now().date())
        
        if st.form_submit_button("✅ حفظ"):
            new_id = 101 if df_c.empty else int(df_c['id'].max()) + 1
            next_v = last_v + timedelta(days=int(cycle) * 30)
            new_row = {'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 'تاريخ الزيارة القادمة': str(next_v), 'تاريخ آخر زيارة': str(last_v)}
            df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
            save_db(df_c, "customers_final.csv")
            st.success(f"تم الحفظ! كود العميل: {new_id}")

# --- 6. صفحة بيانات العملاء (عرض الكروت) ---
elif menu == "بيانات العملاء":
    st.header("👥 قائمة العملاء")
    search = st.text_input("🔎 ابحث بالاسم أو الرقم أو الكود")
    
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False) | (f_df['id'].astype(str) == search)]

    for i, row in f_df.iterrows():
        # تحديد لون الحالة
        try:
            diff = (pd.to_datetime(row['تاريخ الزيارة القادمة']).date() - datetime.now().date()).days
            color = "🔴 متأخر" if diff < 0 else "🟡 قريب" if diff <= 7 else "🟢 منتظم"
        except: color = "⚪ غير محدد"

        with st.container():
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 10px; border-right: 5px solid {'red' if diff < 0 else 'green'}; margin-bottom: 10px; color: black;">
                <h4>ID: {row['id']} | {row['اسم العميل']} <span style="float:left; font-size: 14px;">{color}</span></h4>
                <p>📍 {row['المنطقه']} - {row['العنوان']}</p>
                <p>🗓️ الموعد القادم: <b>{row['تاريخ الزيارة القادمة']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            # زر الاتصال
            main_phone = str(row['الهواتف']).split(',')[0].strip()
            c1.link_button("📞 اتصل الآن", f"tel:{main_phone}", use_container_width=True)
            # زر اللوكيشن
            if pd.notna(row['الموقع']) and "http" in str(row['الموقع']):
                c2.link_button("📍 فتح الخرائط", row['الموقع'], use_container_width=True)
            else:
                c2.button("🚫 لا يوجد موقع", disabled=True, use_container_width=True)
            # زر الواتساب
            c3.link_button("💬 واتساب", f"https://wa.me/2{main_phone}", use_container_width=True)
            st.divider()

# --- 7. سجل الصيانات ---
elif menu == "سجل الصيانات":
    st.header("🔧 تسجيل صيانة جديدة")
    if df_c.empty:
        st.warning("لا يوجد عملاء مسجلين حالياً.")
    else:
        with st.form("service_form"):
            customer_list = df_c.apply(lambda x: f"{x['id']} - {x['اسم العميل']}", axis=1).tolist()
            selected = st.selectbox("اختر العميل", customer_list)
            v_date = st.date_input("تاريخ الزيارة", value=datetime.now().date())
            
            p_cols = st.columns(3)
            p1 = p_cols[0].checkbox("شمعة 1")
            p2 = p_cols[1].checkbox("شمعة 2")
            p3 = p_cols[2].checkbox("شمعة 3")
            
            details = st.text_area("تفاصيل إضافية (ممبرين، قطع غيار...)")
            amount = st.number_input("المبلغ المحصل", min_value=0)
            
            if st.form_submit_button("✅ حفظ الصيانة"):
                c_id = int(selected.split(" - ")[0])
                c_name = selected.split(" - ")[1]
                new_h = {'id_عميل': c_id, 'اسم العميل': c_name, 'تاريخ الزيارة': str(v_date), 'التفاصيل': details, 'المبلغ': amount}
                df_h = pd.concat([df_h, pd.DataFrame([new_h])], ignore_index=True)
                save_db(df_h, "history_final.csv")
                
                # تحديث ميعاد الزيارة القادمة تلقائياً للعميل
                cycle = df_c.loc[df_c['id'] == c_id, 'دورة الصيانة'].values[0]
                next_v = v_date + timedelta(days=int(cycle) * 30)
                df_c.loc[df_c['id'] == c_id, 'تاريخ الزيارة القادمة'] = str(next_v)
                df_c.loc[df_c['id'] == c_id, 'تاريخ آخر زيارة'] = str(v_date)
                save_db(df_c, "customers_final.csv")
                
                st.success("تم تسجيل الصيانة وتحديث ميعاد الزيارة القادم!")

    st.subheader("📜 سجل الزيارات السابق")
    st.dataframe(df_h, use_container_width=True)

# --- خروج ---
if st.sidebar.button("خروج"):
    st.session_state.role = None
    st.rerun()
