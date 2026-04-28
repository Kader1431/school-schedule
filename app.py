import streamlit as st
import pandas as pd
from datetime import date
import io

# --- 1. قائمة الأكواد النشطة (تضعها هنا يدوياً حالياً) ---
# بمجرد أن يبيع Lister K كوداً، يضيفه هنا.
if 'valid_keys' not in st.session_state:
    st.session_state.valid_keys = ["A1B2-C3D4-E5F6", "LK99-X001-Z999"] 

EXPIRY_DATE = date(2027, 4, 28)

st.set_page_config(page_title="SmarTimetable PRO ⚡", layout="wide")

def check_license():
    # التحقق من الصلاحية الزمنية
    if date.today() > EXPIRY_DATE:
        st.error("❌ انتهت صلاحية الترخيص السنوي.")
        return False

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل رخصة الاستخدام لمرة واحدة")
        st.warning("تحذير: هذا الكود صالح لجهاز واحد فقط وسيتم إبطاله فور التفعيل.")
        
        license_input = st.text_input("أدخل كود التفعيل (14 حرفاً)", max_chars=14)
        
        if st.button("تفعيل البرنامج الآن"):
            if license_input in st.session_state.valid_keys:
                # العملية السحرية: حذف الكود من القائمة فور استخدامه
                st.session_state.valid_keys.remove(license_input)
                st.session_state.authenticated = True
                st.success("✅ تم التفعيل بنجاح! هذا الجهاز مرخص الآن لمدة عام.")
                st.rerun()
            else:
                st.error("❌ الكود غير صحيح، أو تم استخدامه مسبقاً من قبل شخص آخر!")
        return False
    return True

# --- 2. تشغيل البرنامج الرئيسي ---
if check_license():
    st.title("⚡ SmarTimetable PRO")
    st.sidebar.info(f"النسخة مرخصة لـ: {date.today().year}")
    
    # هنا تضع كود الجداول المطور (الذي يدعم الساعات وحذف الخانات)
    # ... (الكود السابق) ...