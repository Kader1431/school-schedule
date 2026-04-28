import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io
from datetime import date

# --- 1. إعدادات الصفحة ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(
    page_title=APP_NAME, 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- 2. الاتصال بقاعدة البيانات (الأكواد) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_license():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل نظام Lister K")
        st.info("أدخل كود التفعيل المكون من 14 حرفاً.")
        
        user_key = st.text_input("كود التفعيل", type="password", help="أدخل الكود هنا").strip()
        
        if st.button("دخول"):
            try:
                df_keys = conn.read(ttl=0)
                df_keys.columns = [str(c).strip().lower() for c in df_keys.columns]
                
                if 'keys' in df_keys.columns and 'status' in df_keys.columns:
                    df_keys['keys'] = df_keys['keys'].astype(str).str.strip()
                    df_keys['status'] = df_keys['status'].astype(str).str.strip().str.lower()
                    
                    valid_keys = dict(zip(df_keys['keys'], df_keys['status']))
                    
                    if user_key in valid_keys:
                        if valid_keys[user_key] == "active":
                            st.session_state.authenticated = True
                            st.success("✅ تم التفعيل!")
                            st.rerun()
                        else:
                            st.error("❌ الكود معطل.")
                    else:
                        st.error("❌ كود غير صحيح.")
                else:
                    st.error("⚠️ خطأ في أعمدة الجدول (keys/status).")
            except:
                st.error("⚠️ فشل الاتصال بالجدول. تأكد من Secrets والمشاركة.")
        return False
    return True

# --- 3. تشغيل البرنامج الرئيسي ---
if check_license():
    # القوائم الأساسية
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours_list = [f"{h:02d}:00" for h in range(8, 18)]

    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # نظام الألوان
    def get_subject_style(subject):
        colors = {
            "رياضيات": "#D6EAF8", "فيزياء": "#D5F5E3", "علوم": "#FADBD8",
            "عربية": "#FCF3CF", "فرنسية": "#E8DAEF", "إنجليزية": "#FAE5D3"
        }
        bg = colors.get(subject, "#F4F6F6")
        return f'background-color: {bg}; color: black; font-weight: bold;'

    st.title(f"⚡ {APP_NAME}")

    # --- القائمة الجانبية ---
    with st.sidebar:
        st.success("النسخة مرخصة ✅")
        st.header("➕ إضافة حصة")
        teacher = st.text_input("الأستاذ *")
        subject = st.text_input("المادة *")
        classroom = st.text_input("القسم *")
        day = st.selectbox("اليوم", days)
        c1, c2 = st.columns(2)
        start_t = c1.selectbox("من", hours_list)
        end_t = c2.selectbox("إلى", hours_list)

        if st.button("تثبيت الحصة"):
            if teacher and subject and classroom and hours_list.index(start_t) < hours_list.index(end_t):
                st.session_state.schedule.append({
                    "teacher": teacher, "subject": subject, "classroom": classroom,
                    "day": day, "start": start_t, "end": end_t
                })
                st.success("✅ تم الحفظ")
                st.rerun()
            else:
                st.error("تأكد من البيانات والوقت")
        
        st.divider()
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # --- التبويبات ---
    t1, t2, t3, t4 = st.tabs(["📊 الأستاذ", "🏢 القسم", "🕵️ نظام الانتظار", "📥 الإدارة"])

    def create_styled_table(key, value, label_key):
        df = pd.DataFrame(index=hours_list, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[key] == value:
                s_idx, e_idx = hours_list.index(item['start']), hours_list.index(item['end'])
                for i in range(s_idx, e_idx):
                    df.at[hours_list[i], item['day']] = f"{item['subject']} ({item[label_key]})"
        
        def apply_color(val):
            if "(" in str(val):
                sub = str(val).split(" (")[0]
                return get_subject_style(sub)
            return ""
        return df.style.applymap(apply_color)

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            sel_t = st.selectbox("اختر الأستاذ المطلوب عرض جدوله:", teachers)
            st.table(create_styled_table('teacher', sel_t, 'classroom'))

    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            sel_c = st.selectbox("اختر القسم المطلوب عرض جدوله:", classes)
            st.table(create_styled_table('classroom', sel_c, 'teacher'))

    with t3:
        st.subheader("🕵️ البحث عن أستاذ شاغر")
        cd, ch = st.columns(2)
        s_day = cd.selectbox("اليوم المختار:", days, key="sd_key")
        s_hour = ch.selectbox("الساعة المختارة:", hours_list, key="sh_key")
        
        if st.button("بحث عن الأحرار"):
            all_t = set([i['teacher'] for i in st.session_state.schedule])
            busy_t = set()
            for item in st.session_state.schedule:
                if item['day'] == s_day:
                    if hours_list.index(item['start']) <= hours_list.index(s_hour) < hours_list.index(item['end']):
                        busy_t.add(item['teacher'])
            free_t = sorted(list(