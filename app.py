import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import uuid

# --- إعدادات ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(page_title=APP_NAME, layout="wide")

# الاتصال بجدول جوجل
conn = st.connection("gsheets", type=GSheetsConnection)

# مدير الكوكيز
cookie_manager = stx.CookieManager()

def check_license():
    # 1. فحص هل يوجد تفعيل سابق مخزن في كوكيز الجهاز
    saved_token = cookie_manager.get("lister_auth_token")
    
    if saved_token:
        st.session_state.authenticated = True
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل النسخة الاحترافية")
        st.info("أدخل الكود للتفعيل لمدة 30 يوماً على هذا الجهاز.")
        
        user_key = st.text_input("كود التفعيل", type="password").strip()
        
        if st.button("تفعيل وحفظ على الجهاز"):
            try:
                df_k = conn.read(ttl=0)
                df_k.columns = [str(c).strip().lower() for c in df_k.columns]
                keys_dict = dict(zip(df_k['keys'].astype(str), df_k['status'].astype(str).str.lower()))
                
                if user_key in keys_dict and keys_dict[user_key] == "active":
                    # نجاح التفعيل: إنشاء توكن وحفظه في الكوكيز لمدة 30 يوم
                    st.session_state.authenticated = True
                    
                    # حفظ الكوكيز (ينتهي بعد 30 يوم)
                    cookie_manager.set(
                        "lister_auth_token", 
                        str(uuid.uuid4()), 
                        expires_at=datetime.now() + timedelta(days=30)
                    )
                    
                    st.success("✅ تم التفعيل! سيتذكرك الجهاز لمدة 30 يوماً.")
                    st.rerun()
                else:
                    st.error("❌ الكود غير صحيح أو منتهي.")
            except:
                st.error("⚠️ خطأ في الاتصال بالقاعدة.")
        return False
    return True

# --- تشغيل البرنامج ---
if check_license():
    st.success("مرحباً بك مجدداً! النسخة نشطة ✅")
    
    # زر لمسح التفعيل يدوياً
    if st.sidebar.button("🗑️ مسح التفعيل من الجهاز"):
        cookie_manager.delete("lister_auth_token")
        st.session_state.authenticated = False
        st.rerun()

    # هنا تكمل بقية كود الجداول الخاص بك...
    st.write("واجهة الجداول تعمل الآن...")