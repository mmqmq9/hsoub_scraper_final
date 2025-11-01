from scraper import scrape_hsoub_io
from database import Database

# دالة وهمية لتقييم المحتوى (لأغراض الاختبار)
def _evaluate_content(data):
    # محاكاة لتقييم الجودة وتحديد نوع السؤال
    content = data.get("full_content", "")
    comments_count = len(data.get("comments", []))
    votes = data.get("votes", 0)
    
    # تحسين تقييم الجودة: يعتمد على الطول والأصوات
    quality_score = 0.4 + (len(content) / 8000) * 0.3 + (min(votes, 50) / 100) * 0.3
    quality_score = min(1.0, quality_score)
    
    question_type = "استفسار"
    if "كيف" in content or "طريقة" in content or "خطوات" in content:
        question_type = "إجرائي"
    elif comments_count > 10 and votes > 5:
        question_type = "نقاشي"
    elif "مشكلة" in content or "خطأ" in content:
        question_type = "تقني/حل مشكلات"
        
    return quality_score, question_type

def scrape_post(url: str):
    """
    تقوم باستخراج منشور واحد، وتقييمه، وحفظه في جدول بيانات التدريب المحسنة.
    """
    db = Database()
    
    # 1. استخراج البيانات الأولية
    scraped_data_list = scrape_hsoub_io(url)
    if not scraped_data_list:
        raise Exception("فشل في استخراج البيانات من الرابط")
        
    data = scraped_data_list[0]
    
    # 2. التقييم المحسن
    quality_score, question_type = _evaluate_content(data)
    
    # 3. إعداد البيانات للحفظ في جدول التدريب المحسن
    enhanced_data = {
        "url": url,
        "title": data.get("title", ""),
        "author": data.get("author", "غير معروف"),
        "date": data.get("date", "غير محدد"),
        "main_content": data.get("full_content", ""),
        "total_comments": len(data.get("comments", [])),
        "votes": data.get("votes", 0),
        "tags": data.get("tags", []),
        "question_type": question_type,
        "content_quality_score": quality_score,
        "comments": data.get("comments", []),
        # معيار الجاهزية للتدريب: جودة عالية (أكثر من 0.7) ومحتوى أساسي لا يقل عن 200 حرف
        "training_ready": quality_score > 0.7 and len(data.get("full_content", "")) > 200
    }
    
    # 4. حفظ البيانات
    db.save_enhanced_training_data(enhanced_data)
    
    return enhanced_data
