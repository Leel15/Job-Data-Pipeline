import json
import os
import time
import requests

from dotenv import load_dotenv 

load_dotenv()
URL = "https://jsearch.p.rapidapi.com/search-v2"

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

TARGET_JOBS =  10

NUM_PAGES = 5

TIMEOUT = 30


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "raw")

RAW_FILE = os.path.join(DATA_DIR, "saudi_technical_jobs.json")
SEEN_URLS_FILE = os.path.join(DATA_DIR, "seen_job_urls.json")


HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
}


TECH_KEYWORDS = [
    "software engineer",
    "software developer",
    "web developer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "data engineer",
    "data analyst",
    "data scientist",
    "machine learning engineer",
    "AI engineer",
    "cybersecurity",
    "cyber security",
    "information security",
    "cloud engineer",
    "DevOps engineer",
    "network engineer",
    "database administrator",
    "IT engineer",
    "IT specialist",
    "computer engineer",
    "systems engineer",
    "QA engineer",
    "quality assurance",
]



os.makedirs("data/raw", exist_ok=True)



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
                        url = get_job_url(job)
                        if url:
                            seen_urls.add(url)
        except Exception as e:
            print(f"⚠️ خطأ في استخراج روابط الوظائف القديمة من الملف الخام: {e}")

    return seen_urls

def save_seen_urls(seen_urls):

    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:

        json.dump(
            sorted(seen_urls),
            f,
            ensure_ascii=False,
            indent=2
        )


def load_old_jobs():

    if not os.path.exists(RAW_FILE):
        return []

    try:

        with open(RAW_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        if isinstance(jobs, list):
            return jobs

        return []

    except Exception as e:

        print(f"⚠️ خطأ في قراءة ملف الوظائف القديمة: {e}")

        return []



def search_jobs(keyword):

    querystring = {
        "query": f"{keyword} jobs in Saudi Arabia",
        "num_pages": str(NUM_PAGES),
        "country": "sa",
        "date_posted": "all",
    }

    try:

        response = requests.get(
            URL,
            headers=HEADERS,
            params=querystring,
            timeout=TIMEOUT
        )


        if response.status_code == 200:

            result = response.json()



            data = result.get("data", {})

            if isinstance(data, dict):

                jobs = data.get("jobs", [])

            elif isinstance(data, list):

                jobs = data

            else:

                jobs = []

            if not isinstance(jobs, list):

                return []


            valid_jobs = []

            for job in jobs:

                if isinstance(job, dict):
                    valid_jobs.append(job)

            return valid_jobs



        elif response.status_code == 429:

            print("⚠️ تم الوصول إلى حد الطلبات في RapidAPI.")

            return []



        elif response.status_code in [401, 403]:

            print(
                f"❌ مشكلة في API Key "
                f"| Status Code: {response.status_code}"
            )

            print(response.text)

            return []

   

        else:

            print(
                f"❌ فشل البحث عن '{keyword}' "
                f"| Status Code: {response.status_code}"
            )

            print(response.text)

            return []



    except requests.exceptions.Timeout:

        print(
            f"⏰ انتهت مهلة الاتصال أثناء البحث عن: "
            f"{keyword}"
        )

        return []



    except requests.exceptions.ConnectionError as e:

        print(
            f"🌐 مشكلة في الاتصال أثناء البحث عن "
            f"{keyword}: {e}"
        )

        return []



    except Exception as e:

        print(
            f"❌ خطأ غير متوقع أثناء البحث عن "
            f"{keyword}: {e}"
        )

        return []



def get_job_url(job):

    if not isinstance(job, dict):
        return None

    apply_link = job.get("job_apply_link")

    if isinstance(apply_link, str) and apply_link.strip():
        return apply_link.strip()

    google_link = job.get("job_google_link")

    if isinstance(google_link, str) and google_link.strip():
        return google_link.strip()

    job_link = job.get("job_link")

    if isinstance(job_link, str) and job_link.strip():
        return job_link.strip()

    return None




def is_saudi_job(job):

    if not isinstance(job, dict):
        return False

    country = str(
        job.get("job_country", "")
    ).strip().upper()



    if country == "SA":
        return True


    location = str(
        job.get("job_location", "")
    ).lower()

    city = str(
        job.get("job_city", "")
    ).lower()

    state = str(
        job.get("job_state", "")
    ).lower()

    saudi_words = [
        "saudi arabia",
        "السعودية",
        "السعوديه",
        "riyadh",
        "jeddah",
        "dammam",
        "khobar",
        "khobar",
        "mecca",
        "makkah",
        "medina",
        "madinah",
        "tabuk",
        "abha",
        "buraydah",
        "qassim",
        "jazan",
        "jubail",
        "yanbu",
    ]

    combined_location = (
        location + " " + city + " " + state
    )

    for word in saudi_words:

        if word in combined_location:
            return True

    return False



def get_job_unique_id(job):

    if not isinstance(job, dict):
        return None

    job_id = job.get("job_id")

    if job_id:
        return f"id:{job_id}"

    job_url = get_job_url(job)

    if job_url:
        return f"url:{job_url}"

    return None




def main():

    print("=" * 70)
    print("JSearch - استخراج الوظائف التقنية في السعودية")
    print("=" * 70)

    print()
    print(f"🎯 عدد الوظائف المطلوبة: {TARGET_JOBS}")
    print(f"🔎 عدد الكلمات المفتاحية: {len(TECH_KEYWORDS)}")
    print(f"📄 عدد الصفحات لكل بحث: {NUM_PAGES}")

 

    seen_urls = load_seen_urls()

    old_jobs = load_old_jobs()

    print()
    print(
        f"📦 الوظائف الموجودة مسبقًا: "
        f"{len(old_jobs)}"
    )

    print(
        f"🔗 الروابط المحفوظة مسبقًا: "
        f"{len(seen_urls)}"
    )


    new_jobs = []

    new_urls = set()

    new_job_ids = set()



    for keyword in TECH_KEYWORDS:

        if len(new_jobs) >= TARGET_JOBS:
            break

        print()
        print("-" * 70)
        print(f"🔎 البحث عن: {keyword}")
        print("-" * 70)

        jobs = search_jobs(keyword)

        print(
            f"📊 النتائج التي رجعها JSearch: "
            f"{len(jobs)}"
        )


        if not jobs:
            continue


        for job in jobs:


            if len(new_jobs) >= TARGET_JOBS:
                break


            if not isinstance(job, dict):
                continue

            if not is_saudi_job(job):

                print(
                    "   ⏭️ تم تجاهل وظيفة خارج السعودية"
                )

                continue



            job_url = get_job_url(job)

            if not job_url:

                print(
                    "   ⏭️ تم تجاهل وظيفة بدون رابط"
                )

                continue


            if job_url in seen_urls:

                continue


            if job_url in new_urls:

                continue


            unique_id = get_job_unique_id(job)

            if unique_id and unique_id in new_job_ids:
                continue


            new_jobs.append(job)

            new_urls.add(job_url)

            if unique_id:
                new_job_ids.add(unique_id)



            title = job.get(
                "job_title",
                "بدون عنوان"
            )

            company = job.get(
                "employer_name",
                "بدون شركة"
            )

            location = job.get(
                "job_location",
                "بدون موقع"
            )

            publisher = job.get(
                "job_publisher",
                "غير معروف"
            )

            print()
            print(
                f"✅ {len(new_jobs)}/{TARGET_JOBS}"
            )

            print(f"   💼 الوظيفة: {title}")
            print(f"   🏢 الشركة: {company}")
            print(f"   📍 الموقع: {location}")
            print(f"   🌐 المصدر: {publisher}")
            print(f"   🔗 الرابط: {job_url}")

     
        time.sleep(1)


    seen_urls.update(new_urls)


    all_jobs = old_jobs + new_jobs


    with open(
        RAW_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_jobs,
            f,
            ensure_ascii=False,
            indent=2
        )


    save_seen_urls(seen_urls)


    print()
    print("=" * 70)
    print("✅ تم الانتهاء")
    print("=" * 70)

    print()
    print(
        f"🆕 الوظائف الجديدة: "
        f"{len(new_jobs)}"
    )

    print(
        f"📦 إجمالي الوظائف في الملف: "
        f"{len(all_jobs)}"
    )

    print(
        f"🔗 إجمالي الروابط المحفوظة: "
        f"{len(seen_urls)}"
    )

    print()
    print(
        f"📁 ملف الوظائف:"
    )

    print(
        f"   {RAW_FILE}"
    )

    print()
    print(
        f"📁 ملف الروابط:"
    )

    print(
        f"   {SEEN_URLS_FILE}"
    )


    if len(new_jobs) >= TARGET_JOBS:

        print()
        print(
            f"🎯 تم الوصول للعدد المطلوب: "
            f"{TARGET_JOBS} وظيفة جديدة."
        )

    else:

        print()
        print("⚠️ لم يتم العثور على العدد المطلوب.")

        print(
            f"تم العثور على "
            f"{len(new_jobs)} "
            f"وظيفة جديدة فقط من أصل "
            f"{TARGET_JOBS}."
        )

if __name__ == "__main__":
    main()