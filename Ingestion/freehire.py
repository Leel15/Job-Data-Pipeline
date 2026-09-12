import json
import os
import time
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import snowflake.connector
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://freehire.me/api/v1/jobs/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://freehire.me/?countries=sa",
}

TARGET_COUNT = 10

# مسار ملف الـ JSON المحلي لفحص الروابط الموجودة مسبقاً
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
JSON_PATH = os.path.join(RAW_DIR, "freehire_tech_jobs.json")


def load_existing_jobs():
    """قراءة الوظائف الموجودة محلياً مسبقاً لتجنب التكرار."""
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


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

        print(f"☁️ جاري إرسال {len(jobs_list)} وظيفة جديدة إلى جدول RAW_FREEHIRE_JOBS في Snowflake...")
        insert_query = "INSERT INTO RAW_FREEHIRE_JOBS (RAW_PAYLOAD) SELECT PARSE_JSON(%s)"

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

def create_resilient_session() -> requests.Session:
    """ينشئ session واحدة مع إعادة محاولة تلقائية عند أخطاء السيرفر المؤقتة."""
    session = requests.Session()

    retry_strategy = Retry(
        total=2,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def get_tech_jobs_50(target_count=TARGET_COUNT):
    """
    يسحب وظائف تقنية سعودية من FreeHire (الفلترة الأساسية تتم عبر
    باراميترات الـ API نفسها: countries=sa, is_tech=tech).
    لا يوجد هنا أي تنظيف عميق (لا تنظيف HTML من الوصف، لا معالجة إضافية)
    — هذي العمليات تُطبَّق لاحقًا عبر Transformation/cleaning.py.
    """
    session = create_resilient_session()

    # 1. تحميل الوظائف القديمة واستخراج روابطها
    existing_jobs = load_existing_jobs()
    existing_urls = {job.get("source_url") for job in existing_jobs if job.get("source_url")}
    print(f"📊 عدد الوظائف الموجودة محلياً مسبقاً: {len(existing_jobs)}")

    new_fetched_jobs = []
    limit = 20
    offset = 0

    print(f"🚀 جاري سحب الوظائف التقنية من FreeHire...")

    while len(new_fetched_jobs) < target_count:
        params = {
            "countries": "sa",
            "is_tech": "tech",
            "limit": limit,
            "offset": offset,
        }

        try:
            response = session.get(API_URL, headers=HEADERS, params=params, timeout=30)

            if response.status_code != 200:
                print(f"❌ خطأ أثناء الاتصال: {response.status_code}")
                break

            payload = response.json()
            raw_jobs = payload.get("data", [])

            if not raw_jobs:
                print("⚠️ انتهت النتائج المتاحة.")
                break

            for item in raw_jobs:
                job_url = item.get("url", "")

                # 2. التحقق مما إذا كانت الوظيفة موجودة مسبقاً
                if job_url in existing_urls:
                    continue

                record = {
                    "job_title": item.get("title", "غير محدد"),
                    "company_name": item.get("company", "غير محدد"),
                    "location": item.get("location", "Saudi Arabia"),
                    "cities": item.get("cities", []),
                    "posted_date": item.get("posted_at") or item.get("created_at", "غير محدد"),
                    "category": item.get("enrichment", {}).get("category", "tech"),
                    "skills": item.get("skills", []),
                    "job_description": item.get("description", ""),  # خام كما هو (فيه HTML)، التنظيف لاحقًا
                    "source_url": job_url,
                    "original_source": item.get("source", "freehire"),
                }
                new_fetched_jobs.append(record)
                existing_urls.add(job_url)

                if len(new_fetched_jobs) >= target_count:
                    break

            print(f"📦 تم جمع {len(new_fetched_jobs)} وظيفة جديدة حتى الآن...")
            offset += limit
            time.sleep(1)

        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ فشل الاتصال: {e}")
            break
        except requests.exceptions.Timeout:
            print("⏱️ انتهت مهلة الاتصال")
            break
        except Exception as e:
            print(f"❌ حدث خطأ: {e}")
            break

    if not new_fetched_jobs:
        print("✨ لا توجد وظائف جديدة، جميع الوظائف المسحوبة موجودة مسبقاً!")
        return

    # دمج الوظائف القديمة مع الجديدة وحفظ الملف الكامل
    combined_jobs = existing_jobs + new_fetched_jobs

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(combined_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n🎯 اكتملت العملية بنجاح! إجمالي الوظائف المحفوظة: {len(combined_jobs)}")
    print(f"📁 {JSON_PATH}")

    # رفع الوظائف الجديدة فقط إلى Snowflake
    if new_fetched_jobs:
        load_jobs_to_snowflake(new_fetched_jobs)


if __name__ == "__main__":
    get_tech_jobs_50()