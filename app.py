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

df_c = load_db("customers_v5.csv", C_COLS)
df_h = load_db("history_v5.csv", H_COLS)

# --- 3. نظام الدخول ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.title("💧 Healthy Water - الدخول")
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول"):
        if pwd == "HgM18082019$&)":
            st.session_state.role = "admin"
            st.rerun()
    st.stop()

# --- 4. القائمة الجانبية ---
menu = st.sidebar.radio("القائمة", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات العام"])

# --- 5. تسجيل عميل جديد (مع تفريغ الخانات) ---
if menu == "تسجيل عميل جديد":
    st.header("📝 إضافة عميل جديد")
    # clear_on_submit تضمن تفريغ البيانات بعد الحفظ
    with st.form("add_client", clear_on_submit=True):
        name = st.text_input("اسم العميل")
        phones = st.text_input("الأرقام (ضع فاصلة بين كل رقم)")
        addr = st.text_input("العنوان الكامل")
        area = st.text_input("المنطقة")
        loc = st.text_input("رابط جوجل مابس (Location)")
        cycle = st.number_input("دورة الصيانة (بالشهور)", min_value=1, value=3)
        if st.form_submit_button("✅ حفظ العميل الجديد"):
            if name and phones:
                new_id = 101 if df_c.empty else int(df_c['id'].max()) + 1
                new_row = {'id': new_id, 'اسم العميل': name, 'الهواتف': phones, 'العنوان': addr, 
                           'المنطقه': area, 'الموقع': loc, 'دورة الصيانة': cycle, 
                           'تاريخ الزيارة القادمة': str(datetime.now().date()), 'تاريخ آخر زيارة': 'لم تتم'}
                df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
                save_db(df_c, "customers_v5.csv")
                st.success(f"تم الحفظ بنجاح! كود العميل هو: {new_id}")
            else:
                st.error("برجاء إدخال الاسم ورقم الهاتف على الأقل")

# --- 6. صفحة بيانات العملاء ---
elif menu == "بيانات العملاء":
    st.header("👥 قاعدة بيانات العملاء")
    search = st.text_input("🔎 ابحث بالاسم، الرقم، المنطقة أو الكود")
    
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | 
                    f_df['الهواتف'].str.contains(search, na=False) | 
                    f_df['المنطقه'].str.contains(search, na=False) | 
                    (f_df['id'].astype(str) == search)]

    for i, row in f_df.iterrows():
        with st.expander(f"👤 {row['id']} - {row['اسم العميل']} ({row['المنطقه']})"):
            tab_info, tab_history, tab_edit = st.tabs(["📋 البيانات الأساسية", "🔧 سجل الزيارات", "✏️ تعديل الملف"])
            
            with tab_info:
                st.write(f"**العنوان:** {row['العنوان']}")
                st.write(f"**دورة الصيانة:** كل {row['دورة الصيانة']} شهور")
                st.info(f"📅 الزيارة القادمة: {row['تاريخ الزيارة القادمة']}")
                
                # تعدد الهواتف مع أزرار اتصال وواتساب
                phone_list = str(row['الهواتف']).split(',')
                for p in phone_list:
                    p = p.strip()
                    if p:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"📞 {p}")
                        c2.link_button("اتصال", f"tel:{p}")
                        c3.link_button("واتساب", f"https://wa.me/2{p}")
                
                if pd.notna(row['الموقع']) and "http" in str(row['الموقع']):
                    st.link_button("📍 فتح الموقع على الخريطة", row['الموقع'])

            with tab_history:
                st.subheader("➕ تسجيل زيارة جديدة")
                # clear_on_submit لتفريغ خانات الصيانة بعد الحفظ
                with st.form(f"visit_form_{row['id']}", clear_on_submit=True):
                    v_date = st.date_input("تاريخ الزيارة", value=datetime.now().date())
                    
                    st.write("**اختيار الشمعات والقطع (بالترتيب المطلوب):**")
                    p1 = st.checkbox("P1")
                    p2 = st.checkbox("P2")
                    p3 = st.checkbox("P3")
                    mem = st.checkbox("ممبرين")
                    post = st.checkbox("بوست كاربون")
                    calc = st.checkbox("كالسيت")
                    infra = st.checkbox("انفرا ريد")
                    
                    other = st.text_input("قطع غيار أخرى / ملاحظات")
                    price = st.number_input("المبلغ المحصل (جنيه)", min_value=0)
                    
                    if st.form_submit_button("✅ حفظ الزيارة وتحديث الموعد"):
                        v_id = 1 if df_h.empty else int(df_h['id_زيارة'].max()) + 1
                        new_v = {'id_زيارة': v_id, 'id_عميل': row['id'], 'تاريخ الزيارة': str(v_date), 
                                 'p1': '✅' if p1 else '', 'p2': '✅' if p2 else '', 'p3': '✅' if p3 else '', 
                                 'ممبرين': '✅' if mem else '', 'بوست كاربون': '✅' if post else '', 
                                 'كالسيت': '✅' if calc else '', 'انفر ريد': '✅' if infra else '', 
                                 'اخري': other, 'المبلغ': price}
                        
                        df_h = pd.concat([df_h, pd.DataFrame([new_v])], ignore_index=True)
                        save_db(df_h, "history_v5.csv")
                        
                        # تحديث ميعاد الزيارة القادمة تلقائياً
                        next_v = v_date + timedelta(days=int(row['دورة الصيانة']) * 30)
                        df_c.loc[df_c['id'] == row['id'], 'تاريخ الزيارة القادمة'] = str(next_v)
                        df_c.loc[df_c['id'] == row['id'], 'تاريخ آخر زيارة'] = str(v_date)
                        save_db(df_c, "customers_v5.csv")
                        st.success("تم تسجيل الصيانة وتحديث ميعاد العميل القادم!")
                        st.rerun()

                st.subheader("📜 أرشيف الصيانات لهذا العميل")
                client_history = df_h[df_h['id_عميل'] == row['id']].sort_values(by='تاريخ الزيارة', ascending=False)
                edited_h = st.data_editor(client_history, key=f"editor_{row['id']}", use_container_width=True)
                if st.button("💾 حفظ أي تعديلات في الجدول", key=f"save_btn_{row['id']}"):
                    df_h.update(edited_h)
                    save_db(df_h, "history_v5.csv")
                    st.success("تم تحديث السجل")

            with tab_edit:
                with st.form(f"edit_form_{row['id']}"):
                    u_name = st.text_input("تعديل الاسم", value=row['اسم العميل'])
                    u_phones = st.text_input("تعديل الأرقام", value=row['الهواتف'])
                    u_addr = st.text_input("تعديل العنوان", value=row['العنوان'])
                    u_area = st.text_input("تعديل المنطقة", value=row['المنطقه'])
                    u_cycle = st.number_input("تعديل الدورة", value=int(row['دورة الصيانة']))
                    u_loc = st.text_input("تعديل الرابط", value=row['الموقع'])
                    if st.form_submit_button("💾 حفظ التعديلات النهائية"):
                        df_c.loc[df_c['id'] == row['id'], ['اسم العميل', 'الهواتف', 'العنوان', 'المنطقه', 'دورة الصيانة', 'الموقع']] = [u_name, u_phones, u_addr, u_area, u_cycle, u_loc]
                        save_db(df_c, "customers_v5.csv")
                        st.success("تم التحديث")
                        st.rerun()

# --- 7. سجل الصيانات العام ---
elif menu == "سجل الصيانات العام":
    st.header("📋 سجل الصيانات والزيارات الكلي")
    # عرض الجدول مرتباً بالأحدث
    st.dataframe(df_h.sort_values(by='تاريخ الزيارة', ascending=False), use_container_width=True)

# --- خروج ---
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.role = None
    st.rerun()
