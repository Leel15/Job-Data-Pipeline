import json
import os
import time
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://freehire.me/api/v1/jobs/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://freehire.me/?countries=sa",
}

TARGET_COUNT = 50


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

    all_jobs = []
    limit = 20
    offset = 0

    print(f"🚀 جاري سحب {target_count} وظيفة تقنية من FreeHire...")

    while len(all_jobs) < target_count:
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
                record = {
                    "job_title": item.get("title", "غير محدد"),
                    "company_name": item.get("company", "غير محدد"),
                    "location": item.get("location", "Saudi Arabia"),
                    "cities": item.get("cities", []),
                    "posted_date": item.get("posted_at") or item.get("created_at", "غير محدد"),
                    "category": item.get("enrichment", {}).get("category", "tech"),
                    "skills": item.get("skills", []),
                    "job_description": item.get("description", ""),  # خام كما هو (فيه HTML)، التنظيف لاحقًا
                    "source_url": item.get("url", ""),
                    "original_source": item.get("source", "freehire"),
                }
                all_jobs.append(record)

                if len(all_jobs) >= target_count:
                    break

            print(f"📦 تم جمع {len(all_jobs)} من أصل {target_count}...")
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

    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "freehire_tech_jobs.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(output_dir, "freehire_tech_jobs.csv")
    pd.DataFrame(all_jobs).to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\n🎯 اكتملت العملية بنجاح! تم حفظ {len(all_jobs)} وظيفة في:")
    print(f"📁 {json_path}")
    print(f"📁 {csv_path}")


if __name__ == "__main__":
    get_tech_jobs_50()