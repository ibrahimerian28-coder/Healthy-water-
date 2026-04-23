import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import uuid

# --- 1. الإعدادات والروابط ---
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# الرابط الجديد (2a05)
API_URL = "https://api.steinhq.com/v1/storages/69e9d16c92b1163e973e2a05"

def get_data(sheet):
    try:
        res = requests.get(f"{API_URL}/{sheet}", timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

def send_post(sheet, payload):
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(f"{API_URL}/{sheet}", json=payload, headers=headers, timeout=15)
        return resp
    except Exception as e: return str(e)

# --- 2. القائمة الجانبية ---
st.sidebar.title("🌊 Healthy Water")
st.sidebar.info("01286609535")
menu = st.sidebar.radio("القائمة الرئيسية", 
    ["➕ إضافة عميل جديد", "🔍 إدارة العملاء وتواصل", "🛠️ تسجيل صيانة", "📅 جدول الأسبوع"])

# --- 3. إضافة عميل جديد ---
if menu == "➕ إضافة عميل جديد":
    st.header("📝 كارت عميل جديد")
    with st.form("new_cust", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم العميل")
            address = st.text_input("العنوان بالتفصيل")
            area = st.text_input("المنطقة")
        with col2:
            location = st.text_input("رابط لوكيشن جوجل")
            install_date = st.date_input("تاريخ التركيب", datetime.now())
            p_raw = st.text_area("أرقام الهاتف (كل رقم في سطر)")
        
        if st.form_submit_button("✅ حفظ البيانات"):
            if name and p_raw:
                p_list = [{"number": p.strip()} for p in p_raw.split("\n") if p.strip()]
                cust_id = str(uuid.uuid4())[:8]
                payload = [{
                    "id": cust_id, "name": name, "phones_json": str(p_list),
                    "address": address, "area": area, "location": location,
                    "install_date": str(install_date)
                }]
                res = send_post("Data", payload)
                if hasattr(res, 'status_code') and res.status_code == 200:
                    st.success(f"تم التسجيل بنجاح! كود العميل: {cust_id}")
                    st.balloons()
                else:
                    st.error(f"السيرفر لسه فيه حاجة: {res.text if hasattr(res, 'text') else res}")

# --- 4. إدارة العملاء وتواصل سريع ---
elif menu == "🔍 إدارة العملاء وتواصل":
    st.header("👤 قاعدة بيانات العملاء")
    df = get_data("Data")
    if not df.empty:
        search = st.text_input("🔍 ابحث بالاسم أو المنطقة")
        if search:
            df = df[df['name'].str.contains(search, na=False, case=False) | df['area'].str.contains(search, na=False, case=False)]
        
        for _, row in df.iterrows():
            with st.expander(f"👤 {row['name']} | 📍 {row['area']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"🏠 **العنوان:** {row['address']}")
                    st.write(f"📅 **التركيب:** {row['install_date']}")
                with c2:
                    if row['location'] and "http" in str(row['location']):
                        st.markdown(f"[📍 فتح الخريطة]({row['location']})")
                
                st.write("---")
                try:
                    phones = eval(row['phones_json'])
                    for p in phones:
                        num = p['number'].replace(" ", "").replace("+", "")
                        cola, colb, colc = st.columns([2, 1, 1])
                        cola.write(f"📞 {p['number']}")
                        colb.markdown(f"[📞 اتصل](tel:{num})")
                        colc.markdown(f"[💬 واتساب](https://wa.me/{num})")
                except: st.write("لا توجد أرقام")

# --- باقي الأقسام ---
else:
    st.info("الأقسام دي هتشتغل أول ما تضيف أول عميل وتتأكد إن الربط تمام!")
