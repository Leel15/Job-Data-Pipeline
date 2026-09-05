import json
import os
import time
from bs4 import BeautifulSoup
import requests


API_URL = "https://freehire.me/api/v1/jobs/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://freehire.me/?countries=sa",
}

TARGET_COUNT = 10

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "raw") 

JOBS_FILE = os.path.join(DATA_DIR, "freehire_tech_jobs.json")
LINKS_CACHE_FILE = os.path.join(DATA_DIR, "freehire_extracted_links.json")


def clean_html_description(raw_html):
    if not raw_html:
        return "غير محدد"

    soup = BeautifulSoup(raw_html, "html.parser")

    return soup.get_text(
        separator="\n",
        strip=True
    )


def load_extracted_links():

    extracted_links = set()
    
    if os.path.exists(LINKS_CACHE_FILE):
        try:
            with open(LINKS_CACHE_FILE, "r", encoding="utf-8") as f:
                extracted_links.update(json.load(f))
        except Exception:
            pass

    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
                for item in existing_jobs:
                    unique_id = get_job_unique_id(item)
                    if unique_id:
                        extracted_links.add(unique_id)
        except Exception:
            pass

    return extracted_links

def save_extracted_links(links):

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(
        LINKS_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(links),
            f,
            ensure_ascii=False,
            indent=2
        )


def load_existing_jobs():

    if os.path.exists(JOBS_FILE):

        try:

            with open(
                JOBS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception as e:

            print(
                f"⚠️ خطأ في قراءة ملف الوظائف: {e}"
            )

    return []


def save_jobs(jobs):

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(
        JOBS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_job_unique_id(item):

    possible_ids = [
        item.get("id"),
        item.get("job_id"),
        item.get("uuid"),
        item.get("url"),
    ]

    for value in possible_ids:

        if value is not None and str(value).strip():

            return str(value).strip()

    return None


def get_tech_jobs_50(target_count=TARGET_COUNT):

    print("=" * 70)
    print("FreeHire - Tech Jobs Extractor")
    print("=" * 70)


    existing_jobs = load_existing_jobs()

    print(
        f"\n📊 عدد الوظائف الموجودة بالفعل: "
        f"{len(existing_jobs)}"
    )



    extracted_links = load_extracted_links()

    print(
        f"📚 عدد الوظائف المسجلة في الكاش: "
        f"{len(extracted_links)}"
    )


    new_jobs = []

    limit = 20
    offset = 0

    current_run_links = set()

    print(
        f"\n🚀 الهدف: استخراج "
        f"{target_count} وظيفة جديدة"
    )



    while len(new_jobs) < target_count:

        params = {
            "countries": "sa",
            "is_tech": "tech",
            "limit": limit,
            "offset": offset,
        }

        print("\n" + "-" * 70)

        print(
            f"📄 جاري البحث في الصفحة / الدفعة "
            f"Offset = {offset}"
        )

        print(
            f"🔗 Limit = {limit}"
        )

        try:

            response = requests.get(
                API_URL,
                headers=HEADERS,
                params=params,
                timeout=30
            )

            if response.status_code != 200:

                print(
                    f"❌ خطأ أثناء الاتصال: "
                    f"{response.status_code}"
                )

                break

            payload = response.json()

            raw_jobs = payload.get("data", [])



            if not raw_jobs:

                print(
                    "⚠️ لا توجد نتائج أخرى."
                )

                print(
                    "🛑 تم الوصول إلى نهاية الوظائف المتاحة."
                )

                break

            print(
                f"📦 عدد الوظائف في هذه الصفحة: "
                f"{len(raw_jobs)}"
            )

            new_in_page = 0
            already_used = 0



            for item in raw_jobs:

                unique_id = get_job_unique_id(item)

                if not unique_id:

                    print(
                        "⚠️ وظيفة بدون ID أو URL، تم تجاهلها."
                    )

                    continue

                if unique_id in extracted_links:

                    already_used += 1

                    continue

                if unique_id in current_run_links:

                    continue

              

                record = {
                    "job_title": item.get(
                        "title",
                        "غير محدد"
                    ),

                    "company_name": item.get(
                        "company",
                        "غير محدد"
                    ),

                    "location": item.get(
                        "location",
                        "Saudi Arabia"
                    ),

                    "cities": item.get(
                        "cities",
                        []
                    ),

                    "posted_date": (
                        item.get("posted_at")
                        or item.get(
                            "created_at",
                            "غير محدد"
                        )
                    ),

                    "category": (
                        item.get(
                            "enrichment",
                            {}
                        ).get(
                            "category",
                            "tech"
                        )
                    ),

                    "skills": item.get(
                        "skills",
                        []
                    ),

                    "job_description": clean_html_description(
                        item.get(
                            "description",
                            ""
                        )
                    ),

                    "source_url": item.get(
                        "url",
                        ""
                    ),

                    "original_source": item.get(
                        "source",
                        "freehire"
                    ),
                }



                new_jobs.append(record)

                current_run_links.add(
                    unique_id
                )

                new_in_page += 1

                print(
                    f"   🆕 وظيفة جديدة: "
                    f"{record['job_title']}"
                )

                if len(new_jobs) >= target_count:

                    break



            print(
                f"\n📊 وظائف مستخدمة سابقاً: "
                f"{already_used}"
            )

            print(
                f"🆕 وظائف جديدة: "
                f"{new_in_page}"
            )

            print(
                f"🎯 إجمالي الوظائف الجديدة: "
                f"{len(new_jobs)} / {target_count}"
            )


            offset += limit

            time.sleep(1)

        except Exception as e:

            print(
                f"❌ حدث خطأ: {e}"
            )

            break


    combined_jobs = existing_jobs + new_jobs


    unique_jobs = []

    seen_ids = set()

    for job in combined_jobs:

        job_url = job.get(
            "source_url",
            ""
        )

        if not job_url:

            unique_jobs.append(job)

            continue

        if job_url not in seen_ids:

            unique_jobs.append(job)

            seen_ids.add(job_url)


    for job in new_jobs:

        job_url = job.get(
            "source_url",
            ""
        )

        if job_url:

            extracted_links.add(
                job_url
            )

    save_extracted_links(
        extracted_links
    )


    save_jobs(
        unique_jobs
    )


    print("\n" + "=" * 70)

    print(
        "✅ اكتملت العملية!"
    )

    print(
        f"🆕 وظائف جديدة في هذا التشغيل: "
        f"{len(new_jobs)}"
    )

    print(
        f"📊 إجمالي الوظائف المحفوظة: "
        f"{len(unique_jobs)}"
    )

    print(
        f"📚 إجمالي الروابط في الكاش: "
        f"{len(extracted_links)}"
    )

    print(
        f"📁 ملف الوظائف: "
        f"{JOBS_FILE}"
    )

    print(
        f"📁 ملف الكاش: "
        f"{LINKS_CACHE_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    get_tech_jobs_50()