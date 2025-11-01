import streamlit as st
import time
import json
from database import Database
from datetime import datetime
from enhanced_scraper import scrape_post
from scraper import scrape_category # استيراد الدالة الجديدة
import pandas as pd

# تهيئة قاعدة البيانات في session_state
if "db" not in st.session_state:
    st.session_state.db = Database()

# -------------------------------------------
# الصفحة الرئيسية
def show_home():
    st.title("🏠 الرئيسية")
    st.write("مرحباً بك في تطبيق استخراج وتحليل بيانات حسوب IO")

# -------------------------------------------
# صفحة استخراج البيانات العادية
def show_scraping_page():
    st.title("🔍 استخراج البيانات")
    st.info("يمكنك استخراج البيانات من منشورات حسوب IO وحفظها في قاعدة البيانات.")

    st.markdown("---")
    st.markdown("### 🔗 استخراج منشورات فردية")
    
    urls_text = st.text_area("📌 أدخل روابط المنشورات (واحد في كل سطر)")
    urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

    if st.button("🚀 بدء الاستخراج"):
        if not urls:
            st.warning("❌ يرجى إدخال رابط واحد على الأقل")
            return

        db = st.session_state.db

        for i, url in enumerate(urls, 1):
            with st.spinner(f"⏳ استخراج المنشور {i}/{len(urls)}..."):
                try:
                    scrape_post(url)  # حفظ مباشر في قاعدة البيانات
                    st.success(f"✅ تم حفظ المنشور: {url}")
                except Exception as e:
                    st.error(f"❌ فشل استخراج المنشور: {url}\n{e}")

        st.balloons()
        st.success("🎉 اكتمل الاستخراج لجميع المنشورات!")

    st.markdown("---")
    st.markdown("### 🕸️ زاحف التصنيفات (Category Crawler)")
    st.info("استخدم هذه الميزة لاستخراج روابط المنشورات من صفحات التصنيف (مثل https://io.hsoub.com/culture).")
    
    category_url = st.text_input("🔗 أدخل رابط صفحة التصنيف")
    num_pages = st.number_input("🔢 عدد الصفحات المراد استخراجها", min_value=1, value=1, step=1)
    
    if st.button("🕷️ بدء زحف التصنيفات"):
        if not category_url:
            st.warning("❌ يرجى إدخال رابط صفحة التصنيف")
            return
        
        with st.spinner(f"⏳ جاري استخراج الروابط من {num_pages} صفحات..."):
            try:
                # استخدام الدالة الجديدة
                new_links = scrape_category(category_url, pages=num_pages)
                
                if new_links:
                    st.success(f"✅ تم استخراج {len(new_links)} رابط جديد.")
                    
                    # عرض الروابط المستخرجة في مربع النص لتمكين المستخدم من استخراجها
                    st.text_area("روابط المنشورات المستخرجة (يمكنك نسخها ولصقها في الأعلى للاستخراج)", 
                                 value="\n".join(new_links), height=300)
                    st.info("💡 يمكنك الآن نسخ الروابط أعلاه ولصقها في مربع 'استخراج منشورات فردية' والضغط على '🚀 بدء الاستخراج' لحفظها في قاعدة البيانات.")
                else:
                    st.warning("⚠️ لم يتم العثور على أي روابط في الصفحات المحددة.")
            except Exception as e:
                st.error(f"❌ فشل زحف التصنيفات: {e}")


# -------------------------------------------
# صفحة بيانات التدريب المحسنة (ملخص)
def show_enhanced_data_page():
    st.title("🧠 بيانات التدريب المحسنة (ملخص)")
    st.info("💡 هذه الصفحة تعرض ملخصاً للبيانات المحسنة التي تم استخراجها للتدريب")

    db = st.session_state.db
    df = db.get_enhanced_training_data() if db.get_enhanced_training_data() is not None else pd.DataFrame()

    if not df.empty:
        st.success(f"📊 إجمالي بيانات التدريب: {len(df)}")

        # إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 إجمالي المنشورات", len(df))
        with col2:
            ready_count = len(df[df['training_ready'] == 1])
            st.metric("✅ جاهز للتدريب", ready_count)
        with col3:
            total_comments = df['total_comments'].sum()
            st.metric("💬 إجمالي التعليقات", total_comments)
        with col4:
            avg_quality = df['content_quality_score'].mean()
            st.metric("⭐ متوسط الجودة", f"{avg_quality:.2f}")

        st.markdown("---")

        # البحث والتصفية
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 بحث في العناوين والمحتوى")
        with col2:
            show_only_ready = st.checkbox("عرض الجاهز للتدريب فقط", value=True)

        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(search_term, case=False, na=False) |
                filtered_df['main_content'].str.contains(search_term, case=False, na=False)
            ]
        if show_only_ready:
            filtered_df = filtered_df[filtered_df['training_ready'] == 1]

        st.dataframe(
            filtered_df[['title', 'author', 'total_comments', 'votes', 'question_type', 'content_quality_score']],
            use_container_width=True,
            height=400
        )

        st.markdown("---")
        st.markdown("### 📥 تحميل بيانات التدريب")

        if st.button("💾 تصدير جميع بيانات التدريب (JSON)"):
            training_data = []
            for _, row in df.iterrows():
                item = {
                    'title': row['title'],
                    'author': row['author'],
                    'content': row['main_content'],
                    'comments': json.loads(row['comments_json']) if row['comments_json'] else [],
                    'votes': row['votes'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'question_type': row['question_type'],
                    'quality_score': row['content_quality_score']
                }
                training_data.append(item)

            json_data = json.dumps(training_data, ensure_ascii=False, indent=2)
            st.download_button(
                "تحميل JSON",
                json_data,
                f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
    else:
        st.info("📝 لا توجد بيانات تدريب محسنة بعد. استخدم صفحة استخراج البيانات لإضافة منشورات.")

# -------------------------------------------
# صفحة عرض البيانات التفصيلية (الخام)
def show_detailed_data():
    st.title("📋 عرض البيانات التفصيلية")
    st.info("هذه الصفحة تعرض جميع الحقول المستخرجة بما في ذلك البيانات الخام والتقييمات.")

    db = st.session_state.db
    df = db.get_enhanced_training_data() if db.get_enhanced_training_data() is not None else pd.DataFrame()

    if not df.empty:
        st.success(f"📊 إجمالي السجلات التفصيلية: {len(df)}")
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.info("📝 لا توجد بيانات تفصيلية لعرضها بعد.")

# -------------------------------------------
# الصفحة الرئيسية
def main():
    page = st.sidebar.radio(
        "اختر الصفحة",
        ["🏠 الرئيسية", "🔍 استخراج البيانات", "🧠 بيانات التدريب (ملخص)", "📋 عرض البيانات التفصيلية"]
    )

    if page == "🏠 الرئيسية":
        show_home()
    elif page == "🔍 استخراج البيانات":
        show_scraping_page()
    elif page == "🧠 بيانات التدريب (ملخص)":
        show_enhanced_data_page()
    elif page == "📋 عرض البيانات التفصيلية":
        show_detailed_data()

if __name__ == "__main__":
    main()
