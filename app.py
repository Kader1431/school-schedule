import streamlit as st
import pandas as pd
from datetime import date, time
import io

# --- 1. إعدادات الحماية والاسم الجديد ---
USER_NAME = "listerk"
PASSWORD = "123"
EXPIRY_DATE = date(2026, 6, 1)
APP_NAME = "SmarTimetable ⚡" # الاسم الجديد للبرنامج

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. نظام الحماية ---
def is_expired():
    return date.today() > EXPIRY_DATE

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title(f"🔐 دخول {APP_NAME}")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if u == USER_NAME and p == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("بيانات خاطئة")
        return False
    return True

if is_expired():
    st.error("انتهت الصلاحية، تواصل مع Lister K")
elif check_password():
    st.title(f"⚡ {APP_NAME}")
    st.subheader("نظام تنظيم الجداول المدرسية بدقة الساعة")

    # --- 3. إعدادات الوقت (بالساعة والدقيقة) ---
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    
    # تعريف الساعات المتاحة في النظام (من 8 صباحاً إلى 5 مساءً)
    working_hours = [f"{h:02d}:00" for h in range(8, 18)]

    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # --- 4. إدخال البيانات بالساعة ---
    with st.sidebar:
        st.header("➕ إضافة حصة دقيقة")
        teacher = st.text_input("الأستاذ")
        subject = st.text_input("المادة")
        classroom = st.text_input("القسم")
        day = st.selectbox("اليوم", days)
        
        col1, col2 = st.columns(2)
        with col1:
            start_t = st.selectbox("من الساعة", working_hours)
        with col2:
            end_t = st.selectbox("إلى الساعة", working_hours)
            
        full_time = f"{start_t} - {end_t}"

        if st.button("تثبيت في الجدول"):
            # منع التضارب
            conflict = False
            for entry in st.session_state.schedule:
                if entry['day'] == day and entry['time'] == full_time:
                    if entry['teacher'] == teacher or entry['classroom'] == classroom:
                        st.error("⚠️ تضارب في التوقيت!")
                        conflict = True
            
            if not conflict and teacher and subject:
                st.session_state.schedule.append({
                    "teacher": teacher, "subject": subject, 
                    "classroom": classroom, "day": day, "time": full_time
                })
                st.success("تم الإضافة!")

    # --- 5. عرض الجداول ---
    tab1, tab2, tab3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 تصدير"])

    with tab1:
        t_list = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if t_list:
            sel_t = st.selectbox("اختر الأستاذ:", t_list)
            # عرض الجدول بالساعات
            df_t = pd.DataFrame(index=working_hours, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['teacher'] == sel_t:
                    # تلوين الخانات بين وقت البداية والنهاية (تبسيطاً سنضعها في وقت البداية)
                    start_key = item['time'].split(" - ")[0]
                    df_t.at[start_key, item['day']] = f"✅ {item['subject']} ({item['classroom']})"
            st.table(df_t)

    with tab2:
        c_list = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if c_list:
            sel_c = st.selectbox("اختر القسم:", c_list)
            df_c = pd.DataFrame(index=working_hours, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['classroom'] == sel_c:
                    start_key = item['time'].split(" - ")[0]
                    df_c.at[start_key, item['day']] = f"📖 {item['subject']} ({item['teacher']})"
            st.table(df_c)

    with tab3:
        if st.session_state.schedule:
            df_all = pd.DataFrame(st.session_state.schedule)
            st.dataframe(df_all)
            
            # تصدير Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, index=False)
            
            st.download_button("📥 تحميل ملف Excel", buffer.getvalue(), "schedule.xlsx")
            
            if st.button("🗑️ مسح الكل"):
                st.session_state.schedule = []
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()