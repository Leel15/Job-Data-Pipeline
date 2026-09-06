import os
import json
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# قائمة شاملة من المسميات التقنية لتغطية أوسع لسوق العمل السعودي
TECH_KEYWORDS = [
    # هندسة البرمجيات والتطوير
    "software engineer", "software developer", "backend developer",
    "frontend developer", "full stack developer", "mobile developer",
    "iOS developer", "Android developer", "web developer",
    "QA engineer", "quality assurance engineer", "test engineer",
    "embedded systems engineer", "game developer",

    # البيانات والذكاء الاصطناعي
    "data scientist", "data analyst", "data engineer", "data architect",
    "machine learning", "artificial intelligence", "AI engineer",
    "big data engineer", "NLP engineer", "computer vision engineer",
    "deep learning engineer", "business intelligence",

    # البنية التحتية والأنظمة والشبكات
    "devops", "site reliability engineer", "infrastructure engineer",
    "systems administrator", "system administrator", "network engineer",
    "network administrator", "cloud engineer", "cloud architect",
    "database administrator",

    # الأمن السيبراني
    "cyber security", "penetration tester", "security analyst",
    "SOC analyst", "information security engineer",

    # الإدارة التقنية
    "technical project manager", "IT manager", "IT project manager",
    "IT support", "engineering manager",

    # تصميم وتجربة المستخدم
    "UI UX designer", "UX researcher", "product designer",

    # قواعد البيانات والتحليلات
    "ETL developer", "BI developer", "data warehouse engineer"
]

LOCATIONS = [
    "Saudi Arabia",
    "Riyadh, Saudi Arabia",
    "Jeddah, Saudi Arabia",
    "Dammam, Saudi Arabia",
    "Khobar, Saudi Arabia",
    "Mecca, Saudi Arabia",
    "Medina, Saudi Arabia"
]

# كلمات تقنية بسيطة للتحقق من العنوان — مجرد وجود كلمة واحدة كافٍ
TECH_TITLE_WORDS = [
    "engineer", "developer", "programmer", "scientist", "analyst",
    "architect", "administrator", "devops", "security", "cloud",
    "network", "database", "data", "software", "system", "it ",
    "machine learning", "ai ", "ux", "ui", "qa", "test", "cyber",
    "backend", "frontend", "full stack", "mobile", "web", "bi ",
    "etl", "sre", "sysadmin"
]

# استبعاد فقط الحالات الواضحة جدًا التي لا علاقة لها بالتقنية إطلاقًا
CLEAR_EXCLUDE_WORDS = [
    "sales representative", "sales manager", "account executive",
    "marketing manager", "financial analyst", "civil engineer",
    "mechanical engineer", "electrical technician"
]

US_STATE_INDICATORS = [
    ", oh", ", in", ", ca", ", tx", ", ny", ", pa", ", il",
    ", fl", ", ga", ", mi", ", nc", ", va", ", az", ", wa",
    "county", "ohio", "indiana", "california", "texas"
]


def fetch_all_pages(api_key: str, keyword: str, location: str):
    url = f"https://jooble.org/api/{api_key}"
    all_jobs = []
    page = 1
    total_count_reported = None

    while True:
        payload = {"keywords": keyword, "location": location, "page": page}
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            print(f"⚠️ خطأ ({keyword} | {location} - صفحة {page}): {response.status_code}")
            break

        data = response.json()
        jobs = data.get("jobs", [])

        if total_count_reported is None:
            total_count_reported = data.get("totalCount", "غير متوفر")

        if not jobs:
            break

        all_jobs.extend(jobs)
        page += 1

        if page > 50:
            break

    print(f"✅ {keyword} | {location}: استلمنا {len(all_jobs)} من إجمالي معلن {total_count_reported}")
    return all_jobs


def is_saudi_location(location: str) -> bool:
    """فلترة خفيفة: تقبل الموقع الفاضي (لأن البحث أصلاً كان بموقع سعودي)
    وتستبعد فقط لو ظهرت إشارة واضحة لمكان غير سعودي."""
    if not location:
        return True

    loc_lower = location.lower()

    for us_signal in US_STATE_INDICATORS:
        if us_signal in loc_lower:
            return False

    return True


def is_tech_title(title: str) -> bool:
    """فلترة بسيطة: تكفي كلمة تقنية واحدة بالعنوان، واستبعاد فقط للحالات الواضحة."""
    if not title:
        return False

    title_lower = title.lower()

    for excluded in CLEAR_EXCLUDE_WORDS:
        if excluded in title_lower:
            return False

    return any(word in title_lower for word in TECH_TITLE_WORDS)


def get_jooble_jobs() -> pd.DataFrame:
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        raise ValueError("لم يتم العثور على JOOBLE_API_KEY في ملف .env")

    raw_jobs = []
    total_calls = len(TECH_KEYWORDS) * len(LOCATIONS)
    print(f"🔄 بدء السحب عبر {len(TECH_KEYWORDS)} كلمة × {len(LOCATIONS)} موقع = {total_calls} طلب بحث\n")

    for location in LOCATIONS:
        for keyword in TECH_KEYWORDS:
            jobs = fetch_all_pages(api_key, keyword, location)
            for job in jobs:
                job["_search_location"] = location
            raw_jobs.extend(jobs)

    structured = []
    for job in raw_jobs:
        title = job.get("title", "")
        structured.append({
            "title": title,
            "company": job.get("company"),
            "location": job.get("location"),
            "date": job.get("updated"),
            "salary": job.get("salary"),
            "snippet": job.get("snippet"),
            "url": job.get("link"),
            "source": "jooble",
            "search_location": job.get("_search_location"),
        })

    df = pd.DataFrame(structured)

    if df.empty:
        print("⚠️ لم يتم سحب أي بيانات")
        return df

    print(f"\n📥 إجمالي الوظائف الخام (قبل أي فلترة): {len(df)}")

    before_tech_filter = len(df)
    df = df[df["title"].apply(is_tech_title)]
    print(f"💻 بعد فلترة العناوين التقنية: {len(df)} (أُزيل {before_tech_filter - len(df)})")

    before_location_filter = len(df)
    df = df[df["location"].apply(is_saudi_location)]
    print(f"🌍 بعد الفلترة الجغرافية: {len(df)} (أُزيل {before_location_filter - len(df)})")

    before_dedup = len(df)
    df.drop_duplicates(subset=["title", "company", "url"], inplace=True)
    print(f"🧹 بعد إزالة التكرار: {len(df)} (أُزيل {before_dedup - len(df)})")

    print(f"📊 إجمالي الوظائف التقنية النهائية: {len(df)}")

    return df


def load_existing_jobs(json_path: str) -> dict:
    """يقرأ ملف JSON السابق ويرجعه كـ dict مفهرس بالـ url للدمج السريع."""
    if not os.path.exists(json_path):
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        return {job["url"]: job for job in existing if job.get("url")}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ تعذّرت قراءة الملف السابق ({e})، سيتم البدء بقائمة فاضية")
        return {}


def merge_and_save_jobs(new_df: pd.DataFrame, json_path: str):
    """يدمج الوظائف الجديدة مع القديمة (upsert باستخدام url) ويحفظ JSON واحد فقط."""
    now = datetime.now(timezone.utc).isoformat()

    existing_jobs = load_existing_jobs(json_path)
    print(f"📂 عدد الوظائف الموجودة مسبقًا بالملف: {len(existing_jobs)}")

    new_records = new_df.to_dict(orient="records")

    added_count = 0
    updated_count = 0

    for job in new_records:
        url = job.get("url")
        if not url:
            continue  # نتجاهل أي سجل بدون رابط فريد

        if url in existing_jobs:
            job["first_seen"] = existing_jobs[url].get("first_seen", now)
            job["last_seen"] = now
            existing_jobs[url] = job
            updated_count += 1
        else:
            job["first_seen"] = now
            job["last_seen"] = now
            existing_jobs[url] = job
            added_count += 1

    print(f"➕ وظائف جديدة أُضيفت: {added_count}")
    print(f"🔄 وظائف موجودة تم تحديثها: {updated_count}")
    print(f"📊 إجمالي الوظائف بعد الدمج: {len(existing_jobs)}")

    final_list = list(existing_jobs.values())

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    print(f"💾 تم حفظ JSON في: {json_path}")


if __name__ == "__main__":
    df = get_jooble_jobs()
    print(df[["title", "company", "location"]].head(20))

    json_path = os.path.join(os.path.dirname(__file__), "..", "output", "jooble_tech_jobs.json")
    merge_and_save_jobs(df, json_path)