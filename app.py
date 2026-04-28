import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io
from datetime import date

# --- 1. إعدادات الصفحة الأساسية ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(
    page_title=APP_NAME, 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- 2. الاتصال بقاعدة بيانات جوجل (الأكواد) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_license():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title(f"🔐 تفعيل نظام {APP_NAME}")
        st.info("يرجى إدخال كود التفعيل (صالح لهذه الجلسة فقط).")
        
        user_key = st.text_input("كود التفعيل", type="password", placeholder="XXXX-XXXX-XXXXXX")
        
        if st.button("دخول"):
            try:
                # قراءة الأكواد من الجدول (تأكد من وجود أعمدة keys و status)
                df_keys = conn.read(ttl=0)
                # تنظيف البيانات من الفراغات
                df_keys['keys'] = df_keys['keys'].astype(str).str.strip()
                df_keys['status'] = df_keys['status'].astype(str).str.strip().str.lower()
                
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
            except Exception as e:
                st.error("⚠️ خطأ في الاتصال بالجدول. تأكد من إعدادات Secrets وصلاحية المشاركة (Anyone with link).")
        
        st.markdown("---")
        st.caption("برمجة وتطوير Lister K © 2026")
        return False
    return True

# --- 3. تشغيل البرنامج الرئيسي بعد التفعيل ---
if check_license():
    # استرجاع حالة الجدولة
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    st.title(f"⚡ {APP_NAME}")

    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours_list = [f"{h:02d}:00" for h in range(8, 18)]

    # --- القائمة الجانبية لإدخال البيانات ---
    with st.sidebar:
        st.header("➕ إضافة حصة جديدة")
        teacher = st.text_input("الأستاذ *")
        subject = st.text_input("المادة *")
        classroom = st.text_input("القسم *")
        day = st.selectbox("اليوم", days)
        
        c1, c2 = st.columns(2)
        with c1: start_t = st.selectbox("من الساعة", hours_list)
        with c2: end_t = st.selectbox("إلى الساعة", hours_list)
            
        if st.button("تثبيت في الجدول"):
            if not teacher or not subject or not classroom:
                st.error("❌ جميع الحقول (*) إلزامية")
            elif hours_list.index(start_t) >= hours_list.index(end_t):
                st.error("❌ وقت النهاية يجب أن يكون بعد وقت البداية")
            else:
                # التحقق من التضارب (منع التداخل)
                conflict = False
                for entry in st.session_state.schedule:
                    if entry['day'] == day:
                        e_start_idx = hours_list.index(entry['start'])
                        e_end_idx = hours_list.index(entry['end'])
                        curr_start_idx = hours_list.index(start_t)
                        curr_end_idx = hours_list.index(end_t)
                        
                        if not (curr_end_idx <= e_start_idx or curr_start_idx >= e_end_idx):
                            if entry['teacher'] == teacher or entry['classroom'] == classroom:
                                st.error(f"⚠️ تضارب! الوقت محجوز لـ {entry['teacher']} أو {entry['classroom']}")
                                conflict = True
                                break
                
                if not conflict:
                    st.session_state.schedule.append({
                        "teacher": teacher, "subject": subject, "classroom": classroom,
                        "day": day, "start": start_t, "end": end_t
                    })
                    st.success("✅ تمت الإضافة")
                    st.rerun()

        st.divider()
        if st.sidebar.button("تسجيل الخروج (قفل)"):
            st.session_state.authenticated = False
            st.rerun()

    # --- عرض الجداول الذكية ---
    t1, t2, t3 = st.tabs(["📊 عرض الأستاذ", "🏢 عرض القسم", "📥 إدارة الحصص والإكسيل"])

    def create_display_table(key, value, label_key):
        df = pd.DataFrame(index=hours_list, columns=days).fillna("-")
        for item in st.session_state.schedule:
            if item[key] == value:
                s_idx = hours_list.index(item['start'])
                e_idx = hours_list.index(item['end'])
                # تعبئة كل الخانات المشمولة في التوقيت
                for i in range(s_idx, e_idx):
                    df.at[hours_list[i], item['day']] = f"{item['subject']} ({item[label_key]})"
        return df

    with t1:
        teachers = sorted(list(set([i['teacher'] for i in st.session_state.schedule])))
        if teachers:
            sel_t = st.selectbox("اختر الأستاذ المعني:", teachers)
            st.table(create_display_table('teacher', sel_t, 'classroom'))
        else:
            st.info("لا توجد بيانات حالياً.")

    with t2:
        classes = sorted(list(set([i['classroom'] for i in st.session_state.schedule])))
        if classes:
            sel_c = st.selectbox("اختر القسم المعني:", classes)
            st.table(create_display_table('classroom', sel_c, 'teacher'))
        else:
            st.info("لا توجد بيانات حالياً.")

    with t3:
        if st.session_state.schedule:
            st.subheader("📋 قائمة الحصص المثبتة")
            for idx, item in enumerate(st.session_state.schedule):
                col_info, col_del = st.columns([5, 1])
                col_info.info(f"**{item['subject']}** | {item['teacher']} | {item['classroom']} | {item['day']} ({item['start']} - {item['end']})")
                if col_del.button("حذف", key=f"del_{idx}"):
                    st.session_state.schedule.pop(idx)
                    st.rerun()
            
            st.divider()
            # تصدير ملف Excel
            df_export = pd.DataFrame(st.session_state.schedule)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Schedule')
            
            st.download_button(
                label="📥 تحميل الجدول بصيغة Excel",
                data=output.getvalue(),
                file_name=f"schedule_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            if st.button("🗑️ مسح الجدول بالكامل"):
                st.session_state.schedule = []
                st.rerun()
        else:
            st.warning("الجدول فارغ. ابدأ بإضافة الحصص من القائمة الجانبية.")