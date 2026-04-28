import streamlit as st
import pandas as pd
from datetime import date
import io

# --- 1. إعدادات الحماية والنسخة التجريبية (يمكنك تعديلها) ---
USER_NAME = "listerk"       # اسم المستخدم للدخول
PASSWORD = "123"            # كلمة السر للدخول
EXPIRY_DATE = date(2026, 6, 1)  # تاريخ انتهاء النسخة التجريبية (سنة، شهر، يوم)

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="نظام Lister K للجداول الذكية", layout="wide", page_icon="🏫")

# --- 2. دالة فحص تاريخ الصلاحية ---
def is_expired():
    if date.today() > EXPIRY_DATE:
        return True
    return False

# --- 3. دالة التحقق من تسجيل الدخول ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تسجيل الدخول للنظام")
        st.info(f"هذه النسخة تابعة لـ Lister K ومحمية بحقوق الملكية.")
        
        user_input = st.text_input("اسم المستخدم")
        pw_input = st.text_input("كلمة السر", type="password")
        
        if st.button("دخول"):
            if user_input == USER_NAME and pw_input == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة السر غير صحيحة!")
        return False
    return True

# --- 4. تشغيل منطق الحماية والبرنامج ---
if is_expired():
    st.error(f"❌ انتهت صلاحية هذه النسخة بتاريخ {EXPIRY_DATE}")
    st.warning("يرجى التواصل مع المطور Lister K لتجديد الاشتراك.")
    st.markdown("📩 **للتواصل:** [ضع وسيلة اتصالك هنا]")

elif check_password():
    # --- بداية البرنامج الأصلي بعد تخطي الحماية ---
    
    st.sidebar.success(f"مرحباً بك: {USER_NAME}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🏫 نظام تنظيم الجدول المدرسي الذكي")
    st.write("إدارة الحصص، منع التضارب، وتصدير الجداول - النسخة الاحترافية")

    # إعدادات الوقت والأيام
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    times = ["08:00 - 10:00", "10:00 - 12:00", "13:00 - 15:00", "15:00 - 17:00"]

    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # القائمة الجانبية لإضافة الحصص
    with st.sidebar:
        st.header("➕ إضافة حصة جديدة")
        teacher = st.text_input("اسم الأستاذ")
        subject = st.text_input("المادة")
        classroom = st.text_input("القسم / القاعة")
        day = st.selectbox("اختر اليوم", days)
        time = st.selectbox("اختر التوقيت", times)
        
        if st.button("إضافة إلى الجدول"):
            # خوارزمية فحص التضارب
            conflict = False
            for entry in st.session_state.schedule:
                if entry['day'] == day and entry['time'] == time:
                    if entry['teacher'] == teacher:
                        st.error(f"⚠️ تضارب: {teacher} لديه حصة أخرى في هذا الوقت!")
                        conflict = True
                    if entry['classroom'] == classroom:
                        st.error(f"⚠️ تضارب: القسم {classroom} مشغول في هذا الوقت!")
                        conflict = True
            
            if not conflict:
                if teacher and subject and classroom:
                    st.session_state.schedule.append({
                        "teacher": teacher, "subject": subject, 
                        "classroom": classroom, "day": day, "time": time
                    })
                    st.success("تمت إضافة الحصة بنجاح!")
                else:
                    st.warning("يرجى إكمال جميع الحقول")

    # عرض الجداول وتصديرها
    st.divider()
    tab1, tab2, tab3 = st.tabs(["📊 جدول الأستاذ", "🏢 جدول القسم", "📥 تصدير البيانات"])

    with tab1:
        teacher_list = sorted(list(set([item['teacher'] for item in st.session_state.schedule])))
        if teacher_list:
            selected_t = st.selectbox("اختر الأستاذ لعرض جدوله:", teacher_list)
            df_t = pd.DataFrame(index=times, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['teacher'] == selected_t:
                    df_t.at[item['time'], item['day']] = f"{item['subject']} ({item['classroom']})"
            st.table(df_t)
        else:
            st.info("لا توجد بيانات حالياً.")

    with tab2:
        class_list = sorted(list(set([item['classroom'] for item in st.session_state.schedule])))
        if class_list:
            selected_c = st.selectbox("اختر القسم لعرض جدوله:", class_list)
            df_c = pd.DataFrame(index=times, columns=days).fillna("-")
            for item in st.session_state.schedule:
                if item['classroom'] == selected_c:
                    df_c.at[item['time'], item['day']] = f"{item['subject']} ({item['teacher']})"
            st.table(df_c)

    with tab3:
        if st.session_state.schedule:
            all_data = pd.DataFrame(st.session_state.schedule)
            st.write("قائمة جميع الحصص المضافة:")
            st.dataframe(all_data)
            
            # ميزة التصدير إلى Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                all_data.to_excel(writer, index=False, sheet_name='الجدول العام')
            
            st.download_button(
                label="📥 تحميل الجدول بصيغة Excel",
                data=buffer.getvalue(),
                file_name=f"جدول_مدرسي_{date.today()}.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            if st.button("🗑️ مسح كل البيانات"):
                st.session_state.schedule = []
                st.rerun()

    # تذييل الصفحة
    st.markdown("---")
    st.caption(f"تم التطوير بواسطة Lister K | نسخة تجريبية تنتهي في {EXPIRY_DATE}")