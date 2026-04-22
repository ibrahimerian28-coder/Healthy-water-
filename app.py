import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. الإعدادات العامة ---
st.set_page_config(page_title="Healthy Water", layout="wide")

# --- 2. إدارة قواعد البيانات ---
def load_db(file, cols):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_db(df, file): df.to_csv(file, index=False)

C_COLS = ['id', 'اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'الموقع', 'دورة الصيانة', 'تاريخ الزيارة القادمة', 'تاريخ آخر زيارة']
H_COLS = ['id_زيارة', 'id_عميل', 'تاريخ الزيارة', 'p1', 'p2', 'p3', 'ممبرين', 'بوست كاربون', 'كالسيت', 'انفر ريد', 'اخري', 'المبلغ']

df_c = load_db("customers_v4.csv", C_COLS)
df_h = load_db("history_v4.csv", H_COLS)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water - تسجيل الدخول")
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات العام"])

# --- 5. تسجيل عميل جديد ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    with st.form("add_client"):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام (ضع فاصلة بين كل رقم)")
        addr = st.text_input("العنوان")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط جوجل مابس")
        cycle = st.number_input("دورة الصيانة (شهور)", value=3)
        if st.form_submit_button("حفظ"):
            new_id = 101 if df_c.empty else int(df_c['id'].max()) + 1
            new_row = {'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 'تاريخ الزيارة القادمة': str(datetime.now().date()), 'تاريخ آخر زيارة': 'لم تتم'}
            df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
            save_db(df_c, "customers_v4.csv")
            st.success(f"تم الحفظ بكود {new_id}")

# --- 6. صفحة بيانات العملاء (العرض والتعديل) ---
elif menu == "بيانات العملاء":
    st.header("👥 قاعدة بيانات العملاء")
    search = st.text_input("🔎 ابحث بالاسم أو الرقم")
    
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]

    for i, row in f_df.iterrows():
        with st.expander(f"📌 {row['id']} - {row['اسم العميل']} | {row['المنطقه']}"):
            tab_info, tab_edit, tab_history = st.tabs(["📄 بيانات العميل", "✏️ تعديل البيانات", "🔧 سجل الصيانات"])
            
            with tab_info:
                st.write(f"**العنوان:** {row['العنوان']}")
                # عرض كل أرقام الهاتف مع أزرار
                phone_list = str(row['الهواتف']).split(',')
                for p in phone_list:
                    p = p.strip()
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"📞 {p}")
                    c2.link_button("اتصال", f"tel:{p}")
                    c3.link_button("واتساب", f"https://wa.me/2{p}")
                
                if pd.notna(row['الموقع']) and "http" in str(row['الموقع']):
                    st.link_button("📍 فتح الموقع على الخريطة", row['الموقع'])

            with tab_edit:
                with st.form(f"edit_{row['id']}"):
                    u_name = st.text_input("الاسم", value=row['اسم العميل'])
                    u_phones = st.text_input("الهواتف", value=row['الهواتف'])
                    u_addr = st.text_input("العنوان", value=row['العنوان'])
                    u_loc = st.text_input("الموقع", value=row['الموقع'])
                    if st.form_submit_button("تحديث البيانات"):
                        df_c.loc[df_c['id'] == row['id'], ['اسم العميل', 'الهواتف', 'العنوان', 'الموقع']] = [u_name, u_phones, u_addr, u_loc]
                        save_db(df_c, "customers_v4.csv")
                        st.success("تم التعديل")
                        st.rerun()

            with tab_history:
                st.subheader("➕ إضافة زيارة جديدة")
                with st.form(f"visit_{row['id']}"):
                    v_date = st.date_input("تاريخ الزيارة", value=datetime.now().date())
                    c1, c2, c3, c4 = st.columns(4)
                    p1 = c1.checkbox("P1")
                    p2 = c2.checkbox("P2")
                    p3 = c3.checkbox("P3")
                    mem = c4.checkbox("ممبرين")
                    post = c1.checkbox("بوست")
                    calc = c2.checkbox("كالسيت")
                    infra = c3.checkbox("انفرا")
                    other = st.text_input("قطع أخرى")
                    price = st.number_input("المبلغ", min_value=0)
                    
                    if st.form_submit_button("حفظ الزيارة"):
                        v_id = 1 if df_h.empty else int(df_h['id_زيارة'].max()) + 1
                        new_v = {'id_زيارة': v_id, 'id_عميل': row['id'], 'تاريخ الزيارة': str(v_date), 'p1': p1, 'p2': p2, 'p3': p3, 'ممبرين': mem, 'بوست كاربون': post, 'كالسيت': calc, 'انفر ريد': infra, 'اخري': other, 'المبلغ': price}
                        df_h = pd.concat([df_h, pd.DataFrame([new_v])], ignore_index=True)
                        save_db(df_h, "history_v4.csv")
                        # تحديث ميعاد القادم
                        next_v = v_date + timedelta(days=int(row['دورة الصيانة']) * 30)
                        df_c.loc[df_c['id'] == row['id'], 'تاريخ الزيارة القادمة'] = str(next_v)
                        save_db(df_c, "customers_v4.csv")
                        st.rerun()

                st.subheader("📜 الزيارات السابقة (يمكنك التعديل مباشرة)")
                client_h = df_h[df_h['id_عميل'] == row['id']]
                edited_h = st.data_editor(client_h, key=f"editor_{row['id']}")
                if st.button("حفظ تعديلات الزيارات", key=f"btn_{row['id']}"):
                    df_h.update(edited_h)
                    save_db(df_h, "history_v4.csv")
                    st.success("تم تحديث السجل")

# --- 7. سجل الصيانات العام ---
elif menu == "سجل الصيانات العام":
    st.header("📋 سجل الزيارات الكلي")
    st.dataframe(df_h, use_container_width=True)
