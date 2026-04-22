import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px # للمخططات البيانية

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
H_COLS = ['id_عميل', 'اسم العميل', 'تاريخ الزيارة', 'p1', 'p2', 'p3', 'ممبرين', 'بوست كاربون', 'كالسيت', 'انفر ريد', 'اخري', 'المبلغ', 'تكلفة البضاعة']
S_COLS = ['العنصر', 'الكميه', 'سعر الوحده', 'القيمه الاجماليه']
EXP_COLS = ['التاريخ', 'انتقالات', 'عمولات', 'نثريات', 'بيان']

df_c = load_db("customers_final.csv", C_COLS)
df_h = load_db("history_final.csv", H_COLS)
df_s = load_db("stock_final.csv", S_COLS)
df_e = load_db("expenses_final.csv", EXP_COLS)

# --- 3. نظام الدخول (كما هو) ---
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
menu = st.sidebar.radio("القائمة الرئيسية", ["بيانات العملاء", "تسجيل عميل جديد", "سجل الصيانات", "المخزن", "الحسابات والمصروفات", "الأرباح والتقارير"])

# --- إصلاح دالة تلوين الجدول ---
def color_date(val):
    try:
        diff = (pd.to_datetime(val).date() - datetime.now().date()).days
        if diff < 0: return 'background-color: #ffcccc'
        if diff <= 7: return 'background-color: #ffffcc'
        return 'background-color: #ccffcc'
    except: return ''

if menu == "بيانات العملاء":
    st.header("👥 قاعدة البيانات")
    search = st.text_input("🔎 بحث سريع")
    f_df = df_c.copy()
    if search:
        f_df = f_df[f_df['اسم العميل'].str.contains(search, na=False) | f_df['الهواتف'].str.contains(search, na=False)]
    
    # استخدام .map بدلاً من .applymap لحل المشكلة
    st.dataframe(f_df.style.map(color_date, subset=['تاريخ الزيارة القادمة']), use_container_width=True)

elif menu == "الحسابات والمصروفات":
    st.header("💰 المصروفات اليومية")
    with st.form("exp_form"):
        col1, col2, col3 = st.columns(3)
        trans = col1.number_input("🚗 انتقالات", min_value=0)
        comm = col2.number_input("💸 عمولات", min_value=0)
        misc = col3.number_input("☕ نثريات", min_value=0)
        note = st.text_input("📝 بيان المصرف")
        if st.form_submit_button("حفظ المصروف"):
            new_e = {'التاريخ': datetime.now().date(), 'انتقالات': trans, 'عمولات': comm, 'نثريات': misc, 'بيان': note}
            df_e = pd.concat([df_e, pd.DataFrame([new_e])], ignore_index=True)
            save_db(df_e, "expenses_final.csv")
            st.success("تم تسجيل المصروف")

    st.subheader("سجل المصروفات")
    st.table(df_e.tail(10))

elif menu == "الأرباح والتقارير":
    st.header("📈 تقارير الأرباح")
    
    total_revenue = pd.to_numeric(df_h['المبلغ']).sum()
    total_cost = pd.to_numeric(df_h['تكلفة البضاعة']).sum()
    total_expenses = df_e[['انتقالات', 'عمولات', 'نثريات']].sum().sum()
    
    net_profit = total_revenue - (total_cost + total_expenses)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي التحصيل", f"{total_revenue:,}")
    c2.metric("تكلفة البضاعة", f"{total_cost:,}")
    c3.metric("المصروفات", f"{total_expenses:,}")
    c4.metric("صافي الربح", f"{net_profit:,}", delta_color="normal")

    # رسم بياني بسيط للتوضيح
    if not df_h.empty:
        df_h['تاريخ الزيارة'] = pd.to_datetime(df_h['تاريخ الزيارة'])
        daily_rev = df_h.groupby(df_h['تاريخ الزيارة'].dt.date)['المبلغ'].sum().reset_index()
        fig = px.line(daily_rev, x='تاريخ الزيارة', y='المبلغ', title="تطور التحصيل اليومي")
        st.plotly_app(fig)

# (بقية الأكواد السابقة تسجيل العميل والمخزن تظل كما هي مع إضافة تكلفة البضاعة عند الحفظ)
