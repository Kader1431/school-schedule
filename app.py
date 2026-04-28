import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import uuid
import io

# --- 1. إعدادات الصفحة ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. أدوات الاتصال والتخزين ---
conn = st.connection("gsheets", type=GSheetsConnection)
cookie_manager = stx.CookieManager()

def check_license():
    # التحقق من وجود تفعيل مخزن في المتصفح
    saved_token = cookie_manager.get("lister_auth_token")
    if saved_token:
        st.session_state.authenticated = True
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 تفعيل نظام Lister K")
        st.info("أدخل الكود للتفعيل لمدة 30 يوماً على هذا الجهاز.")
        user_key = st.text_input("كود التفعيل", type="password").strip()
        
        if st.button("تفعيل وحفظ على الجهاز"):
            try:
                df_k = conn.read(ttl=0)
                df_k.columns = [str(c).strip().lower() for c in df_k.columns]
                keys_dict = dict(zip(df_k['keys'].astype(str), df_k['status'].astype(str).str.lower()))
                
                if user_key in keys_dict and keys_dict[user_key] == "active":
                    st.session_state.authenticated = True
                    # حفظ التفعيل لمدة 30 يوم
                    cookie_manager.set("lister_auth_token", str(uuid.uuid4()), 
                                     expires_at=datetime.now() + timedelta(days=30))
                    st.success("✅ تم التفعيل بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ الكود غير صحيح أو منتهي.")
            except:
                st.error("⚠️ فشل الاتصال بقاعدة البيانات.")
        return False
    return True

# --- 3. تشغيل البرنامج الرئيسي ---
if check_license():
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours = [f"{h:02d}:00" for h in range(8, 18)]
    
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    # نظام الألوان
    def get_style(sub):
        clrs = {"رياضيات": "#D6EAF8", "فيزياء": "#D5F5E3", "علوم": "#FADBD8", "عربية": "#FCF3CF"}
        return f'background-color: {clrs.get(sub, "#F4F6F6")}; color: black; font-weight: bold;'

    with st.sidebar:
        st.success("النسخة نشطة ✅")
        if st.button("🗑️ مسح التفعيل"):
            cookie_manager.delete("lister_auth_token")
            st.session_state.authenticated = False
            st.rerun()
        st.divider()
        st.header("➕ إضافة حصة")
        t_in = st.text_input("الأستاذ")
        s_in = st.text_input("المادة")
        c_in = st.text_input("القسم")
        d_in = st.selectbox("اليوم", days)
        start_in = st.selectbox("من", hours)
        end_in = st.selectbox("إلى", hours)
        if st.button("تثبيت"):
            if t_in and s_in and hours.index(start_in) < hours.index(end_in):
                st.session_state.schedule.append({"teacher":t_in,"subject":s_in,"classroom":c_in,"day":d_in,"start":start_in,"end":end_in})
                st.rerun()

    st.title(f"⚡ {APP_NAME}")
    t1, t2, t3, t4 = st.tabs(["📊 الأستاذ", "🏢 القسم", "🕵️ الانتظار", "📥 الإدارة"])

    def draw_table(k, val, lbl):
        df = pd.DataFrame(index=hours, columns=days).fillna("-")
        for i in st.session_state.schedule:
            if i[k] == val:
                for h in range(hours.index(i['start']), hours.index(i['end'])):
                    df.at[hours[h], i['day']] = f"{i['subject']} ({i[lbl]})"
        return df.style.applymap(lambda v: get_style(v.split(" (")[0]) if "(" in str(v) else "")

    with t1:
        ts = sorted(list(set([x['teacher'] for x in st.session_state.schedule])))
        if ts: st.table(draw_table('teacher', st.selectbox("اختر الأستاذ:", ts), 'classroom'))
    
    with t2:
        cs = sorted(list(set([x['classroom'] for x in st.session_state.schedule])))
        if cs: st.table(draw_table('classroom', st.selectbox("اختر القسم:", cs), 'teacher'))

    with t3:
        st.subheader("🕵️ البحث عن أستاذ شاغر")
        c1, c2 = st.columns(2)
        sd, sh = c1.selectbox("يوم البحث", days), c2.selectbox("ساعة البحث", hours)
        if st.button("بحث"):
            all_t = set([x['teacher'] for x in st.session_state.schedule])
            busy = set([x['teacher'] for x in st.session_state.schedule if x['day']==sd and hours.index(x['start']) <= hours.index(sh) < hours.index(x['end'])])
            free = sorted(list(all_t - busy))
            st.success(f"الأساتذة الأحرار: {', '.join(free)}" if free else "لا يوجد أحرار")

    with t4:
        for idx, item in enumerate(st.session_state.schedule):
            ca, cb = st.columns([5, 1])
            ca.write(f"{item['subject']} | {item['teacher']} | {item['day']}")
            if cb.button("حذف", key=f"d_{idx}"):
                st.session_state.schedule.pop(idx); st.rerun()
        if st.session_state.schedule:
            df_ex = pd.DataFrame(st.session_state.schedule)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_ex.to_excel(writer, index=False)
            st.download_button("📥 تحميل Excel", buf.getvalue(), "timetable.xlsx")