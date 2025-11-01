مشروع Streamlit لاستخراج بيانات من حسوب IO (واجهة عربية)

كيفية التشغيل على جهازك المحلي:
1. تأكد أنك تستخدم Python 3.10+ وأنك قمت بتفعيل بيئة افتراضية:
   python -m venv .venv
   source .venv/bin/activate    # على لينكس/ماك
   .venv\Scripts\activate     # على ويندوز

2. ثبّت المتطلبات:
   pip install -r requirements.txt

3. شغّل التطبيق:
   streamlit run app.py

ملاحظات هامة:
- السكربر (scraper.py) ابتدائي: مواقع محمية بجافاسكربت/Cloudflare قد تتطلب Playwright أو متصفح آلي.
- قاعدة البيانات الافتراضية هي hsoub_scraper.db في نفس مجلد المشروع.
- يمكنك تعديل المسارات وأسماء الملفات بسهولة.

تم تجهيز المشروع باللغة العربية كما طلبت.