import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import uuid

# إعدادات الصفحة
st.set_page_config(page_title="Healthy Water Pro", layout="wide", page_icon="💧")

# الرابط (2a05) - لاحظ إننا شلنا /Data من الكود تحت
API_URL = "https://api.steinhq.com/v1/storages/69e9d16c92b1163e973e2a05"

st.header("💧 تسجيل العميل - المحاولة الأخيرة لرد الشرف")

with st.form("emergency_form", clear_on_submit=True):
    name = st.text_input("الاسم")
    area = st.text_input("المنطقة")
    phones = st.text_area("التليفون")
    
    if st.form_submit_button("🚀 تنفيذ الضربة القاضية"):
        if name and phones:
            # داتا بسيطة جداً عشان السيرفر ميتلككش
            payload = [{
                "id": str(uuid.uuid4())[:8],
                "name": name,
                "phones_json": phones,
                "area": area,
                "install_date": str(datetime.now().date())
            }]
            
            try:
                # السر هنا: بنبعت للرابط من غير اسم الصفحة
                res = requests.post(API_URL, json=payload, timeout=15)
                
                if res.status_code == 200:
                    st.success("أيوة كدة يا وحش! البالونات أهي 🎈🎈🎈")
                    st.balloons()
                else:
                    # لو لسه فيه مشكلة، هنعرف العيب فينا ولا في Stein
                    st.error(f"Stein لسه معاند: {res.text}")
                    st.info("لو طلع لك نفس الخطأ، يبقى لازم نمسح الـ API من موقع Stein ونعمل واحد جديد تماماً برابط الشيت الحالي.")
            except Exception as e:
                st.error(f"عطل في الشبكة: {e}")
        else:
            st.warning("دخل البيانات يا هندسة!")

st.write("---")
st.info("يا ريس لو دي منجحتش، جرب تعمل 'Refresh' لصفحة Stein HQ من الموبايل قبل ما تدوس حفظ.")
