import streamlit as st
import pandas as pd
from datetime import date
import io

# --- 1. الإعدادات الأساسية ---
USER_NAME = "listerk"
PASSWORD = "123"
EXPIRY_DATE = date(2026, 6, 1)
APP_NAME = "SmarTimetable ⚡"

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. نظام الدخول ---
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
    # إنشاء قائمة الساعات كأرقام لتسهيل العمليات الحسابية
    hours_list = [f"{h:02d}:00" for h in range(8, 18)]

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
        with c1: start_t = st.selectbox("من", hours_list)
        with c2: end_t = st.selectbox("إلى", hours_list)
            
        if st.button("تثبيت في الجدول"):
            if not teacher or not subject or not classroom:
                st.error("❌ الحقول (*) إلزامية")
            elif hours_list.index(start_t) >= hours_list.index(end_t):
                st.error("❌ وقت النهاية يجب أن يكون بعد وقت البداية")
            else:
                # التحقق من التضارب
                conflict = False
                for entry in st.session_state.schedule:
                    if entry['day'] == day:
                        # فحص تداخل الساعات
                        e_start = hours_list.index(entry['start'])
                        e_end = hours_list.index(entry['end'])
                        current_start = hours_list.index(start_t)
                        current_end = hours_list.index(end_t)
                        
                        if not (current_end <= e_start or current_start >= e_end):
                            if entry['teacher'] == teacher or entry['classroom'] == classroom:
                                st.error(f"⚠️ تضارب! الوقت محجوز مسبقاً لـ {entry['teacher']} أو {entry['classroom']}")
                                conflict = True
                                break
                
                if not conflict:
                    st.session_state.schedule.append({
                        "teacher": teacher, "subject": subject, "classroom": classroom,
                        "day": day, "start": start_t, "end": end_t
                    })
                    st.success("✅ تمت الإضافة")

    # --- 4. العرض الذكي (تعبئة الفراغات) ---
    t1, t2, t3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 إدارة الحصص"])

    def fill_table(filter_key, filter_value, display_format):
        df = pd.DataFrame(index=hours_list, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[filter_key] == filter_value:
                idx_start = hours_list.index(item['start'])
                idx_end = hours_list.index(item['end'])
                # تعبئة كل الخانات من البداية للنهاية
                for i in range(idx_start, idx_end):
                    df.at[hours_list[i], item['day']] = display_format.format(s=item['subject'], t=item['teacher'], c=item['classroom'])
        return df

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            sel_t = st.selectbox("اختر الأستاذ:", teachers)
            st.table(fill_table('teacher', sel_t, "📖 {s} ({c})"))
        else: st.info("لا توجد بيانات")

    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            sel_c = st.selectbox("اختر القسم:", classes)
            st.table(fill_table('classroom', sel_c, "📝 {s} ({t})"))
        else: st.info("لا توجد بيانات")

    with t3:
        if st.session_state.schedule:
            for idx, item in enumerate(st.session_state.schedule):
                col_text, col_btn = st.columns([4, 1])
                col_text.info(f"**{item['subject']}** | {item['teacher']} | {item['classroom']} | {item['day']} ({item['start']} - {item['end']})")
                if col_btn.button("حذف 🗑️", key=f"del_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()
            
            # تصدير إكسيل
            df_all = pd.DataFrame(st.session_state.schedule)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, index=False)
            st.download_button("📥 تحميل Excel", buffer.getvalue(), "schedule.xlsx")
        else: st.info("القائمة فارغة")

    st.sidebar.markdown("---")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()