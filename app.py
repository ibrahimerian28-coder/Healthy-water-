import streamlit as st
import requests

# الرابط الجديد بتاعك
API_URL = "https://api.steinhq.com/v1/storages/69e9cdbc92b1163e973e0f5e"

st.title("🕵️‍♂️ فحص السيرفر يا وحش")

if st.button("افحص الشيت دلوقتي"):
    try:
        # بنطلب من Stein يقولنا إيه الصفحات اللي هو شايفها
        res = requests.get(API_URL)
        if res.status_code == 200:
            st.success("السيرفر شغال تمام!")
            st.write("الصفحات اللي Stein شايفها هي:")
            st.json(res.json()) # هيعرض لك أسامي الصفحات (Data, Maintenance)
        else:
            st.error(f"السيرفر مش شايف الشيت أصلاً! الرد: {res.status_code}")
    except Exception as e:
        st.error(f"فيه مشكلة في الاتصال: {e}")

st.markdown("---")
st.write("لو ظهر لك اسم Data تحت، يبقى إحنا ماشيين صح وهنرجع الكود الكبير فوراً!")
