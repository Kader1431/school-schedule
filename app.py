import streamlit as st
import pandas as pd
from datetime import date
import io

# --- 1. نظام الأكواد المستخدمة لمرة واحدة ---
# ملاحظة: في النسخ الاحترافية نستخدم قاعدة بيانات (مثل SQLite أو Supabase)
# هنا سنستخدم قائمة أكواد برمجية (يمكنك تغييرها في كل مرة تبيع فيها البرنامج)
VALID_KEYS = ["LK-2026-A1B2C3", "LK-2026-D4E5F6", "LK-2026-G7H8I9"] 
EXPIRY_DATE = date(2027, 4, 28)

st.set_page_config(page_title="SmarTimetable PRO ⚡", layout="wide")

def check_license():
    if date.today() > EXPIRY_DATE:
        st.error("❌ انتهت صلاحية النسخة السنوية.")
        return False

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔑 تفعيل النسخة المدفوعة")
        st.info("يرجى إدخال كود التفعيل المكون من 14 حرفاً (صالح لجهاز واحد فقط).")
        
        license_input = st.text_input("كود التفعيل", max_chars=14)
        
        if st.button("تفعيل الآن"):
            if license_input in VALID_KEYS:
                st.session_state.authenticated = True
                # ملاحظة: هنا يمكن إضافة كود لتعطيل المفتاح في قاعدة البيانات
                st.success("✅ تم التفعيل بنجاح.")
                st.rerun()
            else:
                st.error("❌ الكود غير صحيح أو تم استخدامه مسبقاً!")
        return False
    return True

# --- تشغيل البرنامج ---
if check_license():
    st.title("⚡ SmarTimetable PRO")
    # ... بقية كود الجدول الذي كتبناه سابقاً ...
    st.write("مرحباً بك في نسختك المرخصة.")
    
    # قائمة جانبية للخروج
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()