import json
import csv
import os
import re
import random
import time
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup
import requests

# ============ المسارات - حسب هيكلتك ============
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

JOBS_JSON = os.path.join(RAW_DIR, "tanqeeb_tech_jobs.json")
JOBS_CSV = os.path.join(RAW_DIR, "tanqeeb_tech_jobs.csv")
LINKS_CACHE = os.path.join(RAW_DIR, "tanqeeb_links_cache.json")

BASE_URL = "https://saudi.tanqeeb.com"
NUMBER_OF_JOBS = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}

def get_page(url):
    try:
        time.sleep(random.uniform(2, 4))
        r = requests.get(url, headers=HEADERS, timeout=40)
        print(f"[{r.status_code}] {url[:90]}")
        if r.status_code == 200 and len(r.text) > 5000:
            return r.text
        print(f" -> محتوى قصير: {len(r.text)}")
        return None
    except Exception as e:
        print(f"❌ خطأ تحميل: {e}")
        return None

def load_existing():
    if os.path.exists(JOBS_JSON):
        try:
            with open(JOBS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except:
            pass
    return []

def save_all(jobs):
    if not jobs:
        print("⚠️ لا يوجد وظائف لحفظها")
        return
    with open(JOBS_JSON, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    with open(JOBS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)
    print(f"\n💾 تم الحفظ:")
    print(f" JSON: {JOBS_JSON} ({len(jobs)})")
    print(f" CSV: {JOBS_CSV}")

def extract_links_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # فلترة روابط المشاركة
        if any(x in href for x in ["facebook.com", "twitter.com", "linkedin.com", "sharer", "whatsapp", "mailto:"]):
            continue
        if re.search(r"/jobs/\d+\.html", href):
            full = urljoin(BASE_URL, href).split("?")[0]
            if "tanqeeb.com" in full:
                links.add(full)
    return links

def get_job_links():
    all_found = set()
    page = 1
    while len(all_found) < NUMBER_OF_JOBS and page <= 10:
        params = {
            "keywords": "", "country": "54", "state": "0",
            "category": "1002", "workplace": "0",
            "search_period": "0", "lang": "all"
        }
        qs = urlencode(params)
        url = f"{BASE_URL}/ar/jobs/search?{qs}" if page == 1 else f"{BASE_URL}/ar/jobs/search/page/{page}?{qs}"
        print(f"\n📄 صفحة {page}:")
        html = get_page(url)
        if not html:
            page += 1
            continue
        page_links = extract_links_from_html(html)
        print(f" -> وجدت {len(page_links)} رابط")
        all_found.update(page_links)
        if not page_links:
            break
        page += 1
    print(f"\n🎯 مجموع الروابط: {len(all_found)}")
    return list(all_found)[:NUMBER_OF_JOBS]

def scrape_job(url):
    html = get_page(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    ld_data = {}
    tag = soup.find("script", type="application/ld+json")
    if tag and tag.string:
        try:
            j = json.loads(tag.string)
            if isinstance(j, list):
                for item in j:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        ld_data = item
                        break
            elif j.get("@type") == "JobPosting":
                ld_data = j
        except:
            pass

    title = ld_data.get("title")
    if not title:
        h = soup.find("h1") or soup.find("h3", class_="job-title-text")
        title = h.get_text(strip=True) if h else None
    if not title or len(title) < 3:
        return None

    company = "غير محدد"
    if isinstance(ld_data.get("hiringOrganization"), dict):
        company = ld_data["hiringOrganization"].get("name", company)
    else:
        c = soup.find("a", class_="job-meta-company")
        if c:
            company = c.get_text(strip=True)

    desc_div = soup.find("div", id="jobDescriptionBody") or soup.find("div", {"data-jb-field": "description"})
    desc = desc_div.get_text("\n", strip=True) if desc_div else ld_data.get("description","")[:4000]

    return {
        "job_title": title,
        "company_name": company,
        "location": "السعودية",
        "posted_date": ld_data.get("datePosted","").split("T")[0] if ld_data.get("datePosted") else "غير محدد",
        "employment_type": ld_data.get("employmentType","غير محدد"),
        "salary": "غير محدد",
        "experience": "غير محدد",
        "category": "تقنية المعلومات",
        "job_description": desc,
        "job_url": url,
        "source": "tanqeeb"
    }

def main():
    print(f"RAW_DIR = {RAW_DIR}")
    existing = load_existing()
    print(f"وظائف موجودة مسبقاً: {len(existing)}")

    links = get_job_links()
    if not links:
        print("\n❌ فشل استخراج الروابط")
        return

    # === إصلاح حفظ الكاش - كان سبب ظهور [] ===
    with open(LINKS_CACHE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    print(f"💾 تم حفظ الكاش: {len(links)} رابط في {LINKS_CACHE}")

    new_jobs = []
    for i, link in enumerate(links, 1):
        if any(j["job_url"] == link for j in existing):
            print(f"[{i}] تخطي - موجودة: {link}")
            continue
        print(f"\n[{i}/{len(links)}] {link}")
        job = scrape_job(link)
        if job:
            new_jobs.append(job)

    if not new_jobs and not existing:
        print("\n❌ لم يتم استخراج أي وظيفة")
        return

    all_jobs = list({j["job_url"]: j for j in existing + new_jobs}.values())
    save_all(all_jobs)
    print("\n✅ انتهى بنجاح!")

if __name__ == "__main__":
    main()