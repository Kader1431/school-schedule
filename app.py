import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. إعدادات الصفحة ---
APP_NAME = "SmarTimetable PRO ⚡"
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="⚡")

# --- 2. الاتصال بقاعدة البيانات ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_license():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 نظام تفعيل Lister K")
        key_input = st.text_input("أدخل كود التفعيل", type="password").strip()
        if st.button("دخول"):
            try:
                df_k = conn.read(ttl=0)
                df_k.columns = [str(c).strip().lower() for c in df_k.columns]
                keys_dict = dict(zip(df_k['keys'].astype(str), df_k['status'].astype(str).str.lower()))
                if key_input in keys_dict and keys_dict[key_input] == "active":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("كود خاطئ أو غير مفعل")
            except:
                st.error("خطأ في الاتصال بالقاعدة")
        return False
    return True

# --- 3. تشغيل البرنامج الرئيسي ---
if check_license():
    days = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
    hours = [f"{h:02d}:00" for h in range(8, 18)]
    if 'schedule' not in st.session_state:
        st.session_state.schedule = []

    def get_style(sub):
        clrs = {"رياضيات": "#D6EAF8", "فيزياء": "#D5F5E3", "علوم": "#FADBD8", "عربية": "#FCF3CF"}
        return f'background-color: {clrs.get(sub, "#F4F6F6")}; color: black;'

    st.title(f"⚡ {APP_NAME}")
    
    with st.sidebar:
        st.success("النسخة مرخصة ✅")
        t_in = st.text_input("الأستاذ")
        s_in = st.text_input("المادة")
        c_in = st.text_input("القسم")
        d_in = st.selectbox("اليوم", days)
        start_in = st.selectbox("من", hours)
        end_in = st.selectbox("إلى", hours)
        if st.button("حفظ الحصة"):
            if t_in and s_in and hours.index(start_in) < hours.index(end_in):
                st.session_state.schedule.append({"teacher":t_in,"subject":s_in,"classroom":c_in,"day":d_in,"start":start_in,"end":end_in})
                st.rerun()

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
        if ts:
            st.table(draw_table('teacher', st.selectbox("الأستاذ:", ts), 'classroom'))

    with t2:
        cs = sorted(list(set([x['classroom'] for x in st.session_state.schedule])))
        if cs:
            st.table(draw_table('classroom', st.selectbox("القسم:", cs), 'teacher'))

    with t3:
        st.subheader("🕵️ البحث عن أستاذ شاغر")
        col1, col2 = st.columns(2)
        sd = col1.selectbox("يوم البحث", days)
        sh = col2.selectbox("ساعة البحث", hours)
        if st.button("بحث"):
            all_t = set([x['teacher'] for x in st.session_state.schedule])
            busy = set([x['teacher'] for x in st.session_state.schedule if x['day']==sd and hours.index(x['start']) <= hours.index(sh) < hours.index(x['end'])])
            free = sorted(list(all_t - busy))
            st.success(f"الأساتذة الأحرار: {', '.join(free)}" if free else "لا يوجد أحرار")

    with t4:
        for idx, item in enumerate(st.session_state.schedule):
            c_a, c_b = st.columns([5, 1])
            c_a.write(f"{item['subject']} | {item['teacher']} | {item['day']} ({item['start']}-{item['end']})")
            if c_b.button("حذف", key=f"del_{idx}"):
                st.session_state.schedule.pop(idx)
                st.rerun()