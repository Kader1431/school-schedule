import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. إعدادات الصفحة ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. الاتصال بقاعدة بيانات جوجل ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_license():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title(f"🔐 تفعيل نظام {APP_NAME}")
        st.info("يرجى إدخال كود التفعيل المكون من 14 حرفاً.")
        
        user_key = st.text_input("كود التفعيل", type="password", placeholder="XXXX-XXXX-XXXXXX").strip()
        
        if st.button("دخول"):
            try:
                # قراءة الجدول مع إلغاء التخزين المؤقت
                df_keys = conn.read(ttl=0)
                
                # تنظيف أسماء الأعمدة (إزالة أي مسافات زائدة وتحويلها لحروف صغيرة)
                df_keys.columns = [str(c).strip().lower() for c in df_keys.columns]
                
                # التأكد من وجود الأعمدة المطلوبة
                if 'keys' in df_keys.columns and 'status' in df_keys.columns:
                    # تنظيف البيانات داخل الأعمدة
                    df_keys['keys'] = df_keys['keys'].astype(str).str.strip()
                    df_keys['status'] = df_keys['status'].astype(str).str.strip().str.lower()
                    
                    # تحويل لقاموس للبحث
                    valid_keys = dict(zip(df_keys['keys'], df_keys['status']))
                    
                    if user_key in valid_keys:
                        if valid_keys[user_key] == "active":
                            st.session_state.authenticated = True
                            st.success("✅ تم التفعيل بنجاح!")
                            st.rerun()
                        else:
                            st.error("❌ هذا الكود منتهي الصلاحية أو معطل.")
                    else:
                        st.error("❌ كود التفعيل غير صحيح.")
                else:
                    st.error("⚠️ خطأ في تنسيق الجدول: تأكد أن العناوين هي keys و status.")
            except Exception as e:
                st.error("⚠️ فشل الاتصال بالجدول. تأكد من إعدادات Secrets وصلاحية المشاركة (Anyone with link).")
        
        st.caption("برمجة وتطوير Lister K © 2026")
        return False
    return True

# --- 3. البرنامج الرئيسي ---
if check_license():
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    st.title(f"⚡ {APP_NAME}")
    
    # القائمة الجانبية
    with st.sidebar:
        st.success("النسخة مرخصة ✅")
        st.header("➕ إضافة حصة")
        teacher = st.text_input("الأستاذ *")
        subject = st.text_input("المادة *")
        classroom = st.text_input("القسم *")
        days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
        day = st.selectbox("اليوم", days)
        
        hours = [f"{h:02d}:00" for h in range(8, 18)]
        c1, c2 = st.columns(2)
        start_t = c1.selectbox("من", hours)
        end_t = c2.selectbox("إلى", hours)
            
        if st.button("تثبيت الحصة"):
            if teacher and subject and classroom and hours.index(start_t) < hours.index(end_t):
                st.session_state.schedule.append({
                    "teacher": teacher, "subject": subject, "classroom": classroom,
                    "day": day, "start": start_t, "end": end_t
                })
                st.success("تم الحفظ!")
                st.rerun()
            else:
                st.error("بيانات ناقصة أو وقت خاطئ")

        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.rerun()

    # التبويبات
    t1, t2, t3 = st.tabs(["📊 الأستاذ", "🏢 القسم", "📥 الإدارة"])

    def create_table(key, value, label_key):
        df = pd.DataFrame(index=hours, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[key] == value:
                s_idx, e_idx = hours.index(item['start']), hours.index(item['end'])
                for i in range(s_idx, e_idx):
                    df.at[hours[i], item['day']] = f"{item['subject']} ({item[label_key]})"
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
                col1, col2 = st.columns([5, 1])
                col1.info(f"{item['subject']} | {item['teacher']} | {item['day']} ({item['start']}-{item['end']})")
                if col2.button("حذف", key=f"d_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()
            
            # تصدير Excel
            df_ex = pd.DataFrame(st.session_state.schedule)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_ex.to_excel(writer, index=False)
            st.download_button("📥 تحميل Excel", buf.getvalue(), "schedule.xlsx")
            # --- دالة تلوين الخلايا (CSS) ---
def get_subject_style(subject):
    colors = {
        "رياضيات": "#D6EAF8", # أزرق فاتح
        "فيزياء": "#D5F5E3",   # أخضر فاتح
        "علوم": "#FADBD8",     # وردي فاتح
        "عربية": "#FCF3CF",    # أصفر فاتح
        "فرنسية": "#E8DAEF",   # بنفسجي فاتح
        "إنجليزية": "#FAE5D3"  # برتقالي فاتح
    }
    # إذا لم تكن المادة في القائمة، نستخدم لوناً رمادياً خفيفاً
    return f'background-color: {colors.get(subject, "#F4F6F6")}'

# --- تعديل دالة إنشاء الجدول لدعم الألوان ---
def create_display_table(key, value, label_key):
    df = pd.DataFrame(index=hours_list, columns=days).fillna("-")
    for item in st.session_state.schedule:
        if item[key] == value:
            s_idx = hours_list.index(item['start'])
            e_idx = hours_list.index(item['end'])
            for i in range(s_idx, e_idx):
                df.at[hours_list[i], item['day']] = f"{item['subject']} ({item[label_key]})"
    
    # تطبيق التلوين (Styler)
    def apply_color(val):
        if "(" in val:
            subject_name = val.split(" (")[0]
            return get_subject_style(subject_name)
        return ""
    
    return df.style.applymap(apply_color)

# --- إضافة تبويب "نظام الانتظار" ---
t1, t2, t3, t4 = st.tabs(["📊 الأستاذ", "🏢 القسم", "🕵️ نظام الانتظار", "📥 الإدارة"])

with t3:
    st.subheader("🕵️ البحث عن أستاذ مستخلف (شاغر)")
    col_day, col_hour = st.columns(2)
    search_day = col_day.selectbox("اختر اليوم:", days, key="search_day")
    search_hour = col_hour.selectbox("اختر الساعة:", hours_list, key="search_hour")
    
    if st.button("بحث عن الأساتذة الأحرار"):
        all_teachers = set([i['teacher'] for i in st.session_state.schedule])
        busy_teachers = set()
        
        for item in st.session_state.schedule:
            if item['day'] == search_day:
                s_idx = hours_list.index(item['start'])
                e_idx = hours_list.index(item['end'])
                curr_idx = hours_list.index(search_hour)
                if s_idx <= curr_idx < e_idx:
                    busy_teachers.add(item['teacher'])
        
        free_teachers = all_teachers - busy_teachers
        
        if free_teachers:
            st.success(f"الأساتذة الأحرار يوم {search_day} على الساعة {search_hour}:")
            for t in sorted(free_teachers):
                st.write(f"✅ الأستاذ: **{t}**")
        else:
            st.warning("جميع الأساتذة لديهم حصص في هذا الوقت.")