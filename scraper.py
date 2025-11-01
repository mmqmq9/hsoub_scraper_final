from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9"
}

def scrape_hsoub_io(url: str, delay: float = 1.0):
    """
    قارئ صفحات حسوب io باستخدام Playwright لضمان تحميل محتوى JavaScript.
    """
    try:
        with sync_playwright() as p:
            # استخدام Chromium في وضع headless
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(extra_http_headers=HEADERS)
            
            # الانتقال إلى الصفحة والانتظار حتى يتم تحميل الشبكة بالكامل
            page.goto(url, wait_until="networkidle")
            
            # الانتظار لضمان تحميل عناصر JavaScript (اختياري، لكن يضيف موثوقية)
            time.sleep(delay) 
            
            # الحصول على محتوى الصفحة بعد تحميل JavaScript
            html_content = page.content()
            browser.close()

        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. العنوان
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. محتوى الفكرة/المقال
        content_el = soup.select_one(".post-content, .idea-body, .content-body")
        if not content_el:
            content_el = soup.body
        
        paragraphs = [p.get_text(strip=True) for p in content_el.find_all("p")] if content_el else []
        content = "\n\n".join(paragraphs).strip()

        # 3. الميتا داتا (المؤلف، التاريخ، الأصوات، الوسوم) - محددات أكثر موثوقية
        
        # المؤلف: البحث عن رابط المؤلف داخل منطقة الميتا داتا
        author = "غير معروف"
        meta_area = soup.select_one(".post-meta, .post-info")
        if meta_area:
            author_link = meta_area.select_one("a[href*='/u/'], a[href*='/user/']")
            if author_link:
                author = author_link.get_text(strip=True)
            else:
                author_span = meta_area.select_one(".user-info span, .author-name")
                if author_span:
                    author = author_span.get_text(strip=True)

        # التاريخ: البحث عن عنصر <time>
        date = "غير محدد"
        time_el = soup.select_one("time[datetime], .post-meta .date span")
        if time_el:
            date = time_el.get("datetime") or time_el.get_text(strip=True)
        
        # الأصوات: البحث عن عنصر يحتوي على عدد الأصوات
        votes = 0
        votes_el = soup.select_one(".votes-count, .score-box .score, .post-meta .score")
        if votes_el:
            try:
                votes_text = re.sub(r'[^\d\-]', '', votes_el.get_text(strip=True))
                votes = int(votes_text)
            except ValueError:
                votes = 0

        # الوسوم: البحث عن جميع الروابط داخل منطقة الوسوم
        tags = [tag.get_text(strip=True) for tag in soup.select(".tags a, .tag-list a, .post-tags a")]

        # 4. التعليقات
        comments = []
        for c in soup.select(".comment, .comments .comment-item"):
            text_el = c.select_one(".comment-content, .comment-body")
            text = " ".join(p.get_text(strip=True) for p in text_el.find_all("p")) if text_el else ""
            
            comment_author_el = c.select_one(".author, .user, .comment-author a")
            comment_author = comment_author_el.get_text(strip=True) if comment_author_el else "غير معروف"
            comments.append({"author": comment_author, "content": text})
            
        result = {
            "title": title,
            "link": url,
            "author": author,
            "date": date,
            "votes": votes,
            "tags": tags,
            "text_content": content[:20000],
            "full_content": content,
            "comments": comments
        }
        return [result]
    except Exception as e:
        print("Playwright Scrape error:", e)
        return []

def scrape_category(category_url: str, pages: int = 1, delay: float = 1.0):
    """
    يستخرج روابط المنشورات من صفحات التصنيف باستخدام Playwright.
    """
    all_links = set()
    base_url = "https://io.hsoub.com"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(extra_http_headers=HEADERS)
            
            for i in range(1, pages + 1):
                url = f"{category_url}?page={i}" if i > 1 else category_url
                print(f"Scraping page: {url}")
                page.goto(url, wait_until="networkidle")
                time.sleep(delay)
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                
                # محددات CSS للروابط في صفحة التصنيف
                # نبحث عن الروابط داخل عناصر المنشورات
                for link_el in soup.select(".post-item .post-title a, .idea-item .idea-title a"):
                    href = link_el.get("href")
                    if href and href.startswith("/"):
                        full_url = urljoin(base_url, href)
                        all_links.add(full_url)
                
                # إذا لم نجد أي روابط، نفترض أننا وصلنا إلى نهاية الصفحات
                if not soup.select(".post-item, .idea-item"):
                    break

            browser.close()
            return list(all_links)
    except Exception as e:
        print(f"Category Scrape error: {e}")
        return list(all_links)
