import streamlit as st
import pandas as pd
from datetime import date
import io

# --- 1. إعدادات الحماية والاسم ---
USER_NAME = "listerk"
PASSWORD = "123"
EXPIRY_DATE = date(2026, 6, 1)
APP_NAME = "SmarTimetable ⚡"

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. نظام الحماية ---
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

if date.today() > EXPIRY_DATE:
    st.error("انتهت الصلاحية، تواصل مع Lister K")
elif check_password():
    st.title(f"⚡ {APP_NAME}")

    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    working_hours = [f"{h:02d}:00" for h in range(8, 18)]

    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # --- 3. إدخال البيانات ---
    with st.sidebar:
        st.header("➕ إضافة حصة جديدة")
        teacher = st.text_input("الأستاذ *")
        subject = st.text_input("المادة *")
        classroom = st.text_input("القسم *")
        day = st.selectbox("اليوم", days)
        
        c1, c2 = st.columns(2)
        with c1: start_t = st.selectbox("من", working_hours)
        with c2: end_t = st.selectbox("إلى", working_hours)
            
        full_time = f"{start_t} - {end_t}"

        if st.button("تثبيت في الجدول"):
            if not teacher or not subject or not classroom:
                st.error("❌ جميع الحقول (*) إلزامية")
            elif start_t == end_t:
                st.error("❌ وقت البداية يجب أن يختلف عن النهاية")
            else:
                conflict = False
                for entry in st.session_state.schedule:
                    if entry['day'] == day and entry['time'] == full_time:
                        if entry['teacher'] == teacher or entry['classroom'] == classroom:
                            st.error("⚠️ تضارب في التوقيت!")
                            conflict = True
                
                if not conflict:
                    st.session_state.schedule.append({
                        "teacher": teacher, 
                        "subject": subject, 
                        "classroom": classroom, 
                        "day": day, 
                        "time": full_time
                    })
                    st.success("✅ تمت الإضافة!")

    # --- 4. العرض (هنا تم إصلاح عرض المادة) ---
    t1, t2, t3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 إدارة الحصص"])

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            sel_t = st.selectbox("اختر الأستاذ:", teachers)
            df_t = pd.DataFrame(index=working_hours, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['teacher'] == sel_t:
                    st_key = item['time'].split(" - ")[0]
                    # هنا التعديل: إظهار المادة والقسم معاً
                    df_t.at[st_key, item['day']] = f"📖 {item['subject']} \n ({item['classroom']})"
            st.table(df_t)

    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            sel_c = st.selectbox("اختر القسم:", classes)
            df_c = pd.DataFrame(index=working_hours, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['classroom'] == sel_c:
                    st_key = item['time'].split(" - ")[0]
                    # هنا التعديل: إظهار المادة والأستاذ معاً
                    df_c.at[st_key, item['day']] = f"📝 {item['subject']} \n ({item['teacher']})"
            st.table(df_c)

    with t3:
        if st.session_state.schedule:
            st.write("### 📋 إدارة الحصص المضافة")
            for idx, item in enumerate(st.session_state.schedule):
                col_text, col_btn = st.columns([4, 1])
                col_text.info(f"**{item['subject']}** | {item['teacher']} | {item['classroom']} | {item['day']} ({item['time']})")
                if col_btn.button("حذف 🗑️", key=f"del_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()

            st.divider()
            df_all = pd.DataFrame(st.session_state.schedule)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, index=False)
            st.download_button("📥 تحميل ملف Excel", buffer.getvalue(), "schedule.xlsx")
            
            if st.button("🗑️ مسح الكل"):
                st.session_state.schedule = []
                st.rerun()
        else:
            st.info("لا توجد بيانات حالياً.")

    st.sidebar.markdown("---")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()