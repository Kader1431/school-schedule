import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import io

# --- 1. إعدادات الصفحة (يجب أن يكون أول سطر برمجي) ---
st.set_page_config(page_title="SmarTimetable PRO ⚡", layout="wide")

# --- 2. تعريف المكونات ---
conn = st.connection("gsheets", type=GSheetsConnection)

# استدعاء مدير الكوكيز بشكل آمن
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

def check_license():
    # محاولة جلب التفعيل المخزن
    try:
        saved_auth = cookie_manager.get("lister_auth")
        if saved_auth == "valid":
            st.session_state.authenticated = True
            return True
    except:
        pass

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل نظام Lister K")
        st.info("أدخل الكود للتفعيل لمدة 30 يوماً.")
        
        user_key = st.text_input("كود التفعيل", type="password").strip()
        
        if st.button("تفعيل وحفظ"):
            try:
                df_k = conn.read(ttl=0)
                df_k.columns = [str(c).strip().lower() for c in df_k.columns]
                keys_dict = dict(zip(df_k['keys'].astype(str), df_k['status'].astype(str).str.lower()))
                
                if user_key in keys_dict and keys_dict[user_key] == "active":
                    st.session_state.authenticated = True
                    # حفظ التفعيل في الكوكيز
                    cookie_manager.set("lister_auth", "valid", expires_at=datetime.now() + timedelta(days=30))
                    st.success("✅ تم التفعيل!")
                    st.rerun()
                else:
                    st.error("❌ الكود غير صحيح.")
            except:
                st.error("⚠️ فشل الاتصال بالقاعدة.")
        return False
    return True

# --- 3. البرنامج الرئيسي ---
if check_license():
    # تعريف القوائم
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours = [f"{h:02d}:00" for h in range(8, 18)]
    
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # واجهة البرنامج
    st.title("⚡ SmarTimetable PRO")
    
    with st.sidebar:
        st.success("النسخة نشطة ✅")
        if st.button("🗑️ تسجيل الخروج"):
            cookie_manager.delete("lister_auth")
            st.session_state.authenticated = False
            st.rerun()
        st.divider()
        # خانات الإدخال
        t_in = st.text_input("الأستاذ")
        s_in = st.text_input("المادة")
        c_in = st.text_input("القسم")
        d_in = st.selectbox("اليوم", days)
        h_start = st.selectbox("من", hours)
        h_end = st.selectbox("إلى", hours)
        if st.button("حفظ"):
            if t_in and s_in and hours.index(h_start) < hours.index(h_end):
                st.session_state.schedule.append({
                    "teacher": t_in, "subject": s_in, "classroom": c_in,
                    "day": d_in, "start": h_start, "end": h_end
                })
                st.rerun()

    # التبويبات
    t1, t2, t3 = st.tabs(["📊 الجداول", "🕵️ الانتظار", "📥 الإدارة"])
    
    with t1:
        st.write("استخدم القائمة الجانبية لإضافة البيانات.")
        if st.session_state.schedule:
            st.write(pd.DataFrame(st.session_state.schedule)) # عرض مبدئي للتأكد من العمل