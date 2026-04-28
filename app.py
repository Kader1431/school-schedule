import streamlit as st
import pandas as pd
from datetime import date
import io

# --- إعدادات البرنامج ---
APP_NAME = "SmarTimetable PRO ⚡"
EXPIRY_DATE = date(2027, 4, 28)

# قائمة الأكواد النشطة (تأكد أن الكود 14 حرفاً)
if 'valid_keys' not in st.session_state:
    st.session_state.valid_keys = ["A1B2-C3D4-E5F6", "LK-PRO-2026-X1"]

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- دالة الحماية (المصلحة لمنع التعليق) ---
def run_security():
    if date.today() > EXPIRY_DATE:
        st.error("❌ انتهت صلاحية الترخيص السنوي.")
        return False

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل رخصة الاستخدام")
        st.info("أدخل الكود المكون من 14 حرفاً لتفعيل النسخة (صالح لمرة واحدة).")
        
        license_input = st.text_input("كود التفعيل", max_chars=14, key="license_field")
        
        if st.button("تفعيل الآن"):
            if license_input in st.session_state.valid_keys:
                # حذف الكود فوراً لمنع إعادة استخدامه
                st.session_state.valid_keys.remove(license_input)
                st.session_state.authenticated = True
                st.success("✅ تم التفعيل بنجاح!")
                st.rerun() # إعادة التشغيل لفتح البرنامج
            else:
                st.error("❌ الكود غير صحيح أو مستخدم مسبقاً.")
        return False
    return True

# --- تشغيل البرنامج الرئيسي ---
if run_security():
    # استرجاع البيانات المخزنة للحصص
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    st.title(f"⚡ {APP_NAME}")
    
    # القائمة الجانبية للإدخال
    with st.sidebar:
        st.header("➕ إضافة حصة جديدة")
        teacher = st.text_input("الأستاذ *")
        subject = st.text_input("المادة *")
        classroom = st.text_input("القسم *")
        days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
        day = st.selectbox("اليوم", days)
        
        hours = [f"{h:02d}:00" for h in range(8, 18)]
        c1, c2 = st.columns(2)
        start_t = c1.selectbox("من", hours)
        end_t = c2.selectbox("إلى", hours)

        if st.button("تثبيت في الجدول"):
            if teacher and subject and classroom and hours.index(start_t) < hours.index(end_t):
                st.session_state.schedule.append({
                    "teacher": teacher, "subject": subject, "classroom": classroom,
                    "day": day, "start": start_t, "end": end_t
                })
                st.success("تمت الإضافة!")
                st.rerun()
            else:
                st.error("تأكد من ملء البيانات وصحة الوقت")

    # تبويبات العرض
    t1, t2, t3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 الإدارة"])

    def create_table(key, value, label):
        df = pd.DataFrame(index=hours, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[key] == value:
                s_idx = hours.index(item['start'])
                e_idx = hours.index(item['end'])
                for i in range(s_idx, e_idx):
                    df.at[hours[i], item['day']] = f"{item['subject']} ({item[label]})"
        return df

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            sel_t = st.selectbox("اختر الأستاذ:", teachers)
            st.table(create_table('teacher', sel_t, 'classroom'))

    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            sel_c = st.selectbox("اختر القسم:", classes)
            st.table(create_table('classroom', sel_c, 'teacher'))

    with t3:
        if st.session_state.schedule:
            for idx, item in enumerate(st.session_state.schedule):
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{item['subject']}** | {item['teacher']} | {item['day']} ({item['start']}-{item['end']})")
                if col_b.button("حذف", key=f"del_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()
            
            # تصدير Excel
            df_all = pd.DataFrame(st.session_state.schedule)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                df_all.to_excel(wr, index=False)
            st.download_button("📥 تحميل ملف Excel", buf.getvalue(), "schedule.xlsx")

    st.sidebar.markdown("---")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()