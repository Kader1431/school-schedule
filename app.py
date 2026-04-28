def check_license():
    # 1. محاولة جلب البيانات مع معالجة الأخطاء
    try:
        # قراءة الجدول مع إلغاء التخزين المؤقت (ttl=0) لضمان رؤية الأكواد الجديدة فوراً
        df = conn.read(ttl=0)
        
        # تنظيف البيانات: إزالة الفراغات الزائدة من الأكواد وحالات التفعيل
        df['keys'] = df['keys'].astype(str).str.strip()
        df['status'] = df['status'].astype(str).str.strip().str.lower()
        
        # تحويل الجدول إلى قاموس للبحث السريع
        valid_keys_dict = dict(zip(df['keys'], df['status']))
    except Exception as e:
        st.error("⚠️ فشل الاتصال بجدول الأكواد. تأكد من رابط Secrets وصلاحيات المشاركة في جوجل.")
        # خيار للطوارئ: عرض الخطأ للمطور (اختياري)
        # st.exception(e) 
        return False

    # 2. إدارة حالة الجلسة
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # 3. واجهة إدخال الكود
    if not st.session_state.authenticated:
        st.title("🔐 تفعيل نظام SmarTimetable PRO")
        st.markdown(f"**المطور:** Lister K | **الحالة:** نسخة محمية")
        
        # حقل الإدخال
        user_key = st.text_input("أدخل كود التفعيل المكون من 14 حرفاً", placeholder="XXXX-XXXX-XXXXXX").strip()
        
        if st.button("تفعيل البرنامج"):
            if user_key in valid_keys_dict:
                if valid_keys_dict[user_key] == "active":
                    st.session_state.authenticated = True
                    st.success("✅ تم التفعيل بنجاح! سيتم فتح الجدول الآن...")
                    st.rerun()
                else:
                    st.error("❌ عذراً، هذا الكود معطل (status ليس active).")
            else:
                st.error("❌ الكود غير موجود في قاعدة البيانات. تأكد من كتابته بدقة.")
        
        return False
    
    return True