import json
import os
import time
import requests
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

URL = "https://jsearch.p.rapidapi.com/search-v2"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

TARGET_JOBS = 5
NUM_PAGES = 2
TIMEOUT = 60

# ============ المسارات المحددة حسب طلبك ============
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

RAW_FILE = os.path.join(DATA_DIR, "jsearch_tech_jobs.json")
SEEN_URLS_FILE = os.path.join(DATA_DIR, "Extracted links", "Jsearch_links_cache.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SEEN_URLS_FILE), exist_ok=True)

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
}

TECH_KEYWORDS = [
    "software",
    "developer",
    "programmer",
    "IT",
    "technology",
    "digital",
    
    "data",
    "analyst",
    "scientist",
    "AI",
    "machine learning",
    "business intelligence",
    
    "devops",
    "cloud",
    "network",
    "systems",
    "database",
    "IT support",
    "technical support",
    "administrator",
    
    "cybersecurity",
    "security",
    "information security",
    
    "full stack",
    "frontend",
    "backend",
    "web",
    "mobile",
    "QA",
    "tester"
]


def load_seen_urls():
    seen_urls = set()
    if os.path.exists(SEEN_URLS_FILE):
        try:
            with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
                urls = json.load(f)
                if isinstance(urls, list):
                    seen_urls.update(urls)
        except Exception as e:
            print(f"⚠️ خطأ في قراءة ملف الروابط السابقة: {e}")

    if os.path.exists(RAW_FILE):
        try:
            with open(RAW_FILE, "r", encoding="utf-8") as f:
                old_jobs = json.load(f)
                if isinstance(old_jobs, list):
                    for job in old_jobs:
                        url = job.get("url")
                        if url:
                            seen_urls.add(url)
        except Exception as e:
            print(f"⚠️ خطأ في استخراج الروابط القديمة: {e}")

    return seen_urls


def save_seen_urls(seen_urls):
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen_urls), f, ensure_ascii=False, indent=2)


def load_old_jobs():
    if not os.path.exists(RAW_FILE):
        return []
    try:
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            if isinstance(jobs, list):
                return jobs
    except Exception as e:
        print(f"⚠️ خطأ في قراءة ملف الوظائف القديمة: {e}")
    return []


# ============ دالة الرفع إلى Snowflake ============
def load_jobs_to_snowflake(jobs_list):
    if not jobs_list:
        return

    conn = None
    cursor = None
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAFE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        cursor = conn.cursor()

        print(f"☁️ جاري إرسال {len(jobs_list)} وظيفة جديدة إلى جدول RAW_JSEARCH_JOBS في Snowflake...")
        insert_query = "INSERT INTO RAW_JSEARCH_JOBS (RAW_PAYLOAD) SELECT PARSE_JSON(%s)"

        for job in jobs_list:
            json_str = json.dumps(job, ensure_ascii=False)
            cursor.execute(insert_query, (json_str,))

        conn.commit()
        print("✅ تم رفع البيانات إلى Snowflake بنجاح!")

    except Exception as e:
        print(f"❌ خطأ أثناء الرفع لـ Snowflake: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_jobs(keyword):
    querystring = {
        "query": f"{keyword} jobs in Saudi Arabia",
        "num_pages": str(NUM_PAGES),
        "country": "sa",
        "date_posted": "all",
    }

    try:
        response = requests.get(URL, headers=HEADERS, params=querystring, timeout=TIMEOUT)

        if response.status_code == 200:
            result = response.json()
            data = result.get("data", {})
            if isinstance(data, dict):
                jobs = data.get("jobs", [])
            elif isinstance(data, list):
                jobs = data
            else:
                jobs = []

            return [j for j in jobs if isinstance(j, dict)]

        elif response.status_code == 429:
            print("⚠️ تم الوصول إلى حد الطلبات في RapidAPI.")
            return []
        elif response.status_code in [401, 403]:
            print(f"❌ مشكلة في API Key | Status Code: {response.status_code}")
            return []
        else:
            print(f"❌ فشل البحث عن '{keyword}' | Status Code: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ خطأ أثناء البحث عن {keyword}: {e}")
        return []


def get_job_url(job):
    for field in ["job_apply_link", "job_google_link", "job_link"]:
        val = job.get(field)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def is_saudi_job(job):
    country = str(job.get("job_country", "")).strip().upper()
    if country == "SA":
        return True

    combined_location = (
        str(job.get("job_location", "")) + " " +
        str(job.get("job_city", "")) + " " +
        str(job.get("job_state", ""))
    ).lower()

    saudi_words = [
        "saudi arabia", "السعودية", "السعوديه", "riyadh", "jeddah",
        "dammam", "khobar", "mecca", "makkah", "medina", "madinah",
        "tabuk", "abha", "buraydah", "qassim", "jazan", "jubail", "yanbu"
    ]
    return any(word in combined_location for word in saudi_words)


def format_job_record(job):
    """تنسيق الوظيفة بالشكل المطلوب تماماً"""
    return {
        "title": job.get("job_title", "بدون عنوان"),
        "company": job.get("employer_name", "بدون شركة"),
        "location": job.get("job_location", "السعودية"),
        "date": job.get("job_posted_at_datetime_utc"),
        "salary": job.get("job_min_salary"), # أو حسب حقل الراتب المتاح لديك
        "snippet": job.get("job_description", "")[:300], # اقتطف جزء أو الوصف كامل حسب الرغبة
        "url": get_job_url(job),
        "employment_type": job.get("job_employment_type", "دوام كامل"),
        "source": "jsearch"
    }


def main():
    print("=" * 70)
    print("JSearch - استخراج الوظائف التقنية في السعودية")
    print("=" * 70)

    seen_urls = load_seen_urls()
    old_jobs = load_old_jobs()

    print(f"📦 الوظائف الموجودة مسبقًا: {len(old_jobs)}")
    print(f"🔗 الروابط المحفوظة مسبقًا: {len(seen_urls)}")

    new_jobs = []
    new_urls = set()

    for keyword in TECH_KEYWORDS:
        if len(new_jobs) >= TARGET_JOBS:
            break

        print(f"\n🔎 البحث عن: {keyword}")
        jobs = search_jobs(keyword)

        for job in jobs:
            if len(new_jobs) >= TARGET_JOBS:
                break

            if not is_saudi_job(job):
                continue

            job_url = get_job_url(job)
            if not job_url or job_url in seen_urls or job_url in new_urls:
                continue

            # تنسيق السجل بالشكل المطلوب
            formatted_record = format_job_record(job)

            new_jobs.append(formatted_record)
            new_urls.add(job_url)

            print(f"✅ {len(new_jobs)}/{TARGET_JOBS} | {formatted_record['title']} ({formatted_record['company']})")

        time.sleep(1)

    if not new_jobs:
        print("\n✨ لا توجد وظائف جديدة لإضافتها.")
        return

    seen_urls.update(new_urls)
    all_jobs = old_jobs + new_jobs

    # الحفظ محلياً
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    save_seen_urls(seen_urls)

    print(f"\n✅ تم الانتهاء! تمت إضافة {len(new_jobs)} وظيفة جديدة.")
    
    # 🚀 رفع الوظائف الجديدة فقط إلى Snowflake
    load_jobs_to_snowflake(new_jobs)


if __name__ == "__main__":
    main()