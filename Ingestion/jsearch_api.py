import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"
API_HOST = "jsearch.p.rapidapi.com"

TECH_KEYWORDS = [
    "software engineer", "software developer", "backend developer",
    "frontend developer", "full stack developer", "mobile developer",
    "data scientist", "data analyst", "data engineer",
    "machine learning engineer", "AI engineer", "cyber security",
    "devops engineer", "cloud engineer", "network engineer",
    "database administrator", "QA engineer", "IT support",
    "UI UX designer", "business intelligence"
]

LOCATIONS = ["Saudi Arabia"]

# كلمات تقنية بسيطة للتحقق من العنوان — نفس منطق jooble للاتساق بين المصادر
TECH_TITLE_WORDS = [
    "engineer", "developer", "programmer", "scientist", "analyst",
    "architect", "administrator", "devops", "security", "cloud",
    "network", "database", "data", "software", "system", "it ",
    "machine learning", "ai ", "ux", "ui", "qa", "test", "cyber",
    "backend", "frontend", "full stack", "mobile", "web", "bi ",
    "etl", "sre", "sysadmin"
]

CLEAR_EXCLUDE_WORDS = [
    "sales representative", "sales manager", "account executive",
    "marketing manager", "financial analyst", "civil engineer",
    "mechanical engineer", "electrical technician"
]

SAUDI_INDICATORS = [
    "saudi arabia", "riyadh", "jeddah", "dammam", "khobar",
    "mecca", "medina", "ksa", "dhahran", "jubail", "taif", "abha"
]

US_STATE_INDICATORS = [
    ", oh", ", in", ", ca", ", tx", ", ny", ", pa", ", il",
    ", fl", ", ga", ", mi", ", nc", ", va", ", az", ", wa",
    "county", "ohio", "indiana", "california", "texas"
]


def create_resilient_session() -> requests.Session:
    """ينشئ session واحدة مع إعادة محاولة تلقائية عند فشل الاتصال أو أخطاء السيرفر المؤقتة."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def is_saudi_location(location: str) -> bool:
    """فلترة خفيفة: تقبل الفاضي (البحث أصلاً بموقع سعودي)، تستبعد فقط إشارة أمريكية واضحة."""
    if not location:
        return True

    loc_lower = location.lower()
    for us_signal in US_STATE_INDICATORS:
        if us_signal in loc_lower:
            return False

    return True


def is_tech_title(title: str) -> bool:
    """فلترة بسيطة: كلمة تقنية واحدة كافية، استبعاد فقط للحالات الواضحة جدًا."""
    if not title:
        return False

    title_lower = title.lower()
    for excluded in CLEAR_EXCLUDE_WORDS:
        if excluded in title_lower:
            return False

    return any(word in title_lower for word in TECH_TITLE_WORDS)


def search_jsearch(session: requests.Session, api_key: str, query: str, max_pages: int = 4):
    """
    يستدعي search-v2 مع دعم cursor-based pagination.
    max_pages: عدد "الصفحات" (كل صفحة = طلب واحد) المراد سحبها لكل كلمة بحث.
    """
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }

    all_jobs = []
    cursor = None
    page_num = 1

    while page_num <= max_pages:
        params = {
            "query": query,
            "num_pages": "1",
            "country": "sa",
            "date_posted": "all"
        }

        if cursor:
            params["next_page_cursor"] = cursor

        try:
            response = session.get(BASE_URL, headers=headers, params=params, timeout=30)
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ فشل الاتصال ({query} - صفحة {page_num}): {e}")
            break
        except requests.exceptions.Timeout:
            print(f"⏱️ انتهت مهلة الاتصال ({query} - صفحة {page_num})")
            break

        if response.status_code != 200:
            print(f"⚠️ خطأ HTTP ({query} - صفحة {page_num}): {response.status_code}")
            break

        body = response.json()
        data_section = body.get("data", {})
        jobs = data_section.get("jobs", [])
        cursor = data_section.get("cursor")

        if not jobs:
            break

        all_jobs.extend(jobs)

        if not cursor:
            break

        page_num += 1
        time.sleep(0.5)  # تأخير بسيط بين الصفحات

    return all_jobs


def get_jsearch_jobs(max_pages_per_query: int = 2) -> pd.DataFrame:
    """
    يسحب الوظائف من JSearch ويطبّق فلترة أساسية فقط (تقني + سعودي).
    لا يوجد هنا أي تنظيف عميق (لا استخراج مهارات، لا خبرة، لا راتب من النص)
    — هذي العمليات تُطبَّق لاحقًا عبر Transformation/cleaning.py.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("لم يتم العثور على RAPIDAPI_KEY في ملف .env")

    session = create_resilient_session()

    all_jobs = []
    total_calls_estimate = len(TECH_KEYWORDS) * len(LOCATIONS)
    print(f"🔄 بدء السحب عبر {len(TECH_KEYWORDS)} كلمة × {len(LOCATIONS)} موقع (≈{total_calls_estimate} طلب أساسي + صفحات إضافية)\n")

    for location in LOCATIONS:
        for keyword in TECH_KEYWORDS:
            query = f"{keyword} in {location}"
            jobs = search_jsearch(session, api_key, query, max_pages=max_pages_per_query)
            print(f"✅ {query}: {len(jobs)} وظيفة")

            for job in jobs:
                job["_search_query"] = query
                job["_search_location"] = location

            all_jobs.extend(jobs)
            time.sleep(1)  # تأخير بين كل كلمة بحث

    if not all_jobs:
        print("⚠️ لم يتم سحب أي بيانات")
        return pd.DataFrame()

    structured = []
    for job in all_jobs:
        structured.append({
            "title": job.get("job_title"),
            "company": job.get("employer_name"),
            "location": job.get("job_location") or job.get("job_city") or job.get("job_country"),
            "date": job.get("job_posted_at_datetime_utc"),
            "salary": job.get("job_salary_string") or job.get("job_min_salary"),
            "snippet": job.get("job_description") or "",  # كامل بدون اقتطاع — التنظيف لاحقًا
            "url": job.get("job_apply_link"),
            "employment_type": job.get("job_employment_type"),
            "source": "jsearch",
            "search_location": job.get("_search_location"),
        })

    df = pd.DataFrame(structured)
    print(f"\n📥 إجمالي الوظائف الخام: {len(df)}")

    before_tech_filter = len(df)
    df = df[df["title"].apply(is_tech_title)]
    print(f"💻 بعد فلترة العناوين التقنية: {len(df)} (أُزيل {before_tech_filter - len(df)})")

    before_location_filter = len(df)
    df = df[df["location"].apply(is_saudi_location)]
    print(f"🌍 بعد الفلترة الجغرافية: {len(df)} (أُزيل {before_location_filter - len(df)})")

    before_dedup = len(df)
    df.drop_duplicates(subset=["title", "company", "url"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"🧹 بعد إزالة التكرار: {len(df)} (أُزيل {before_dedup - len(df)})")

    print(f"📊 إجمالي الوظائف بعد الفلترة الأساسية: {len(df)}")

    return df


if __name__ == "__main__":
    df = get_jsearch_jobs(max_pages_per_query=2)

    if not df.empty:
        print(df[["title", "company", "location"]].head(15))

        output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "jsearch_tech_jobs.json")
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        print(f"💾 تم حفظ JSON في: {json_path}")