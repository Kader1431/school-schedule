import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. إعداد الصفحة والاتصال ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# الاتصال بجدول جوجل (يقرأ الرابط من Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. دالة التحقق (تفعيل لكل مرة) ---
def check_license():
    # استخدام session_state للتفعيل المؤقت في هذه الجلسة فقط
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل نظام Lister K")
        st.info("يرجى إدخال كود التفعيل (صالح لهذه الجلسة فقط).")
        
        user_key = st.text_input("كود التفعيل", type="password", placeholder="XXXX-XXXX-XXXXXX")
        
        if st.button("دخول"):
            try:
                # جلب البيانات من الجدول فوراً
                df = conn.read(ttl=0) 
                valid_keys = dict(zip(df['keys'], df['status']))
                
                if user_key in valid_keys:
                    if valid_keys[user_key] == "active":
                        st.session_state.authenticated = True
                        st.success("✅ تم التفعيل بنجاح!")
                        st.rerun()
                    else:
                        st.error("❌ هذا الكود معطل أو مستخدم.")
                else:
                    st.error("❌ كود غير صحيح.")
            except:
                st.error("⚠️ خطأ في الاتصال بقاعدة البيانات. تأكد من إعدادات Secrets ورابط الجدول.")
        
        st.caption("برمجة وتطوير Lister K © 2026")
        return False
    return True

# --- 3. تشغيل البرنامج الرئيسي في حال التفعيل ---
if check_license():
    # القائمة الجانبية وزر الخروج اليدوي
    with st.sidebar:
        st.success("النسخة مرخصة ✅")
        if st.button("إنهاء الجلسة (قفل)"):
            st.session_state.authenticated = False
            st.rerun()
        st.divider()

    # --- هنا تضع كود الجداول المطور الخاص بك ---
    st.title(f"⚡ {APP_NAME}")
    
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # (بقية كود إضافة الحصص والجداول كما هي في النسخ السابقة)
    # ...