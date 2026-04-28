import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

# --- 1. إعدادات الحماية المتقدمة ---
# الكود السري الذي ستبيعه للزبون (يجب أن يكون 14 حرفاً)
# يمكنك تغيير هذا الكود لكل زبون إذا أردت
SECRET_LICENSE_KEY = "LK-2026-X99-PRO" 

# تاريخ انتهاء الصلاحية (صالح لمدة عام من الآن)
EXPIRY_DATE = date(2027, 4, 28) 

APP_NAME = "SmarTimetable PRO ⚡"

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🔐")

# --- 2. نظام التحقق من كود التفعيل ---
def check_license():
    # التحقق من انتهاء الصلاحية الزمنية أولاً
    if date.today() > EXPIRY_DATE:
        st.error(f"❌ انتهت صلاحية هذه النسخة بتاريخ {EXPIRY_DATE}")
        st.info("يرجى التواصل مع Lister K للحصول على كود تفعيل جديد لعام 2027.")
        return False

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔑 تفعيل النظام")
        st.write("مرحباً بك في نظام Lister K. يرجى إدخال كود التفعيل المكون من 14 حرفاً للاستمرار.")
        
        license_input = st.text_input("أدخل كود التفعيل هنا", max_chars=14, placeholder="XXXX-XXXX-XXXXXX")
        
        if st.button("تفعيل البرنامج"):
            if license_input == SECRET_LICENSE_KEY:
                st.session_state.authenticated = True
                st.success("✅ تم التفعيل بنجاح! البرنامج صالح لمدة عام.")
                st.rerun()
            else:
                st.error("❌ كود التفعيل غير صحيح! يرجى التأكد من الكود أو التواصل مع المطور.")
        
        st.markdown("---")
        st.caption("برمجة وتطوير: Lister K | جميع الحقوق محفوظة 2026")
        return False
    return True

# --- 3. تشغيل البرنامج في حال نجاح التفعيل ---
if check_license():
    st.title(f"⚡ {APP_NAME}")
    
    # القوائم والبيانات
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours_list = [f"{h:02d}:00" for h in range(8, 18)]

    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # القائمة الجانبية
    with st.sidebar:
        st.header("➕ إضافة حصة")
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
                st.error("❌ خطأ في اختيار الوقت")
            else:
                # التحقق من التضارب (نفس الكود الذكي السابق)
                conflict = False
                for entry in st.session_state.schedule:
                    if entry['day'] == day:
                        e_start, e_end = hours_list.index(entry['start']), hours_list.index(entry['end'])
                        curr_start, curr_end = hours_list.index(start_t), hours_list.index(end_t)
                        if not (curr_end <= e_start or curr_start >= e_end):
                            if entry['teacher'] == teacher or entry['classroom'] == classroom:
                                st.error(f"⚠️ تضارب مع {entry['teacher']} أو {entry['classroom']}")
                                conflict = True
                                break
                if not conflict:
                    st.session_state.schedule.append({
                        "teacher": teacher, "subject": subject, "classroom": classroom,
                        "day": day, "start": start_t, "end": end_t
                    })
                    st.success("✅ تم")

    # تبويبات العرض
    t1, t2, t3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 الإدارة"])

    def display_table(key, val, fmt):
        df = pd.DataFrame(index=hours_list, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[key] == val:
                for i in range(hours_list.index(item['start']), hours_list.index(item['end'])):
                    df.at[hours_list[i], item['day']] = fmt.format(s=item['subject'], t=item['teacher'], c=item['classroom'])
        return df

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            s_t = st.selectbox("الأستاذ:", teachers)
            st.table(display_table('teacher', s_t, "{s} ({c})"))
    
    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            s_c = st.selectbox("القسم:", classes)
            st.table(display_table('classroom', s_c, "{s} ({t})"))

    with t3:
        if st.session_state.schedule:
            for idx, item in enumerate(st.session_state.schedule):
                col_t, col_b = st.columns([4, 1])
                col_t.info(f"**{item['subject']}** | {item['teacher']} | {item['day']} ({item['start']}-{item['end']})")
                if col_b.button("حذف", key=f"d_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()
            
            # تصدير Excel
            df_all = pd.DataFrame(st.session_state.schedule)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                df_all.to_excel(wr, index=False)
            st.download_button("📥 تحميل Excel", buf.getvalue(), "schedule.xlsx")
        else:
            st.info("لا توجد حصص.")

    st.sidebar.markdown("---")
    st.sidebar.write(f"📅 نسخة مرخصة لغاية: {EXPIRY_DATE}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()