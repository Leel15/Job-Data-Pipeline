import json
import os
import re
import random
import time
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv()
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
BASE_URL = "https://saudi.tanqeeb.com"

NUMBER_OF_JOBS = 5 
MAX_PAGES = 100  

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)             
DATA_DIR = os.path.join(PROJECT_ROOT, "raw")            

JOBS_FILE = os.path.join(DATA_DIR, "tanqeeb_saudi_jobs_tech.json")
LINKS_CACHE_FILE = os.path.join(DATA_DIR, "extracted_links_cache.json")


def get_scrapeops_url(url, render_js=False):
    payload = {
        "api_key": SCRAPEOPS_API_KEY,
        "url": url,
    }
    if render_js:
        payload["render_js"] = "true"
        
    return "https://proxy.scrapeops.io/v1/?" + urlencode(payload)


def get_page(url, render_js=False):
    try:
        response = requests.get(
            get_scrapeops_url(url, render_js=render_js),
            timeout=90
        )

        print("STATUS:", response.status_code)

        if response.status_code == 200:
            print("✅ تم تحميل الصفحة بنجاح")
            return response.text

        print(f"❌ فشل تحميل الصفحة: {response.status_code}")
        return None

    except requests.RequestException as e:
        print(f"❌ خطأ أثناء تحميل الصفحة: {e}")
        return None


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
                for job in existing_jobs:
                    url = job.get("job_url") or job.get("source_url")
                    if url:
                        extracted_links.add(url)
        except Exception:
            pass

    return extracted_links
def save_extracted_links(links):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LINKS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(links), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"   ❌ خطأ في حفظ الروابط: {e}")


def load_existing_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطأ في قراءة الوظائف الموجودة: {e}")
    return []


def save_jobs(jobs):
    """حفظ الوظائف (إضافة للموجود وليس استبدال)"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"\n   💾 تم حفظ {len(jobs)} وظيفة في:")
        print(f"      {JOBS_FILE}")
        print(f"   ✅ الملف محفوظ بنجاح!")
    except Exception as e:
        print(f"   ❌ خطأ في حفظ الملف: {e}")


def job_exists(jobs_list, job_url):
    """التحقق من أن الوظيفة موجودة بالفعل"""
    return any(job.get("job_url") == job_url for job in jobs_list)


def get_job_links():
    print("\n🔍 جاري تصفح قسم تقنية المعلومات واستخراج الوظائف...")

    extracted_links = load_extracted_links()
    print(f"📚 عدد الروابط المستخرجة سابقاً: {len(extracted_links)}")

    job_links = set()
    page = 1

    search_params = {
        "keywords": "",
        "country": "54",
        "state": "0",
        "category": "1002",
        "workplace": "0",
        "search_period": "0",
        "lang": "all"
    }

    while page <= MAX_PAGES:
        query_string = urlencode(search_params)

        if page == 1:
            page_url = f"{BASE_URL}/ar/jobs/search?{query_string}"
        else:
            page_url = f"{BASE_URL}/ar/jobs/search/page/{page}?{query_string}"

        print(f"\n📄 جاري البحث في الصفحة {page}:")
        print(page_url)

        html = get_page(page_url, render_js=False)

        if not html:
            print(f"⚠️ تعذر تحميل الصفحة {page} - سيتم تجربة الصفحة التالية")
            page += 1
            time.sleep(2)
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_links = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()

            if not href:
                continue

            if href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(BASE_URL, href)

            if "saudi.tanqeeb.com" not in full_url:
                continue

            ignored_parts = [
                "/search", "/privacy", "/terms", "/contact",
                "/about", "/login", "/register", "/companies",
                "/categories", "/sites/"
            ]

            if any(part in full_url for part in ignored_parts):
                continue

            if any(domain in full_url for domain in [
                "facebook.com", "twitter.com", "linkedin.com",
                "whatsapp.com", "sharer"
            ]):
                continue

            if re.search(r"/jobs/\d+\.html(?:\?.*)?$", full_url):
                page_links.add(full_url)

        print(f"📌 عدد روابط الوظائف المكتشفة في الصفحة {page}: {len(page_links)}")

        if page_links:
            new_links_in_page = (
                page_links
                - extracted_links
                - job_links
            )

            print(f"🆕 وظائف جديدة في هذه الصفحة: {len(new_links_in_page)}")
            job_links.update(new_links_in_page)
            extracted_links.update(page_links)

            print(f"📊 إجمالي الوظائف الجديدة التي سيتم تحميلها: {len(job_links)}")
        else:
            print(f"⚠️ لم يتم العثور على روابط وظائف في الصفحة {page} - لكن لن نوقف البحث")

        if len(job_links) >= NUMBER_OF_JOBS:
            print(f"\n🎯 تم الوصول إلى العدد المطلوب ({NUMBER_OF_JOBS}) من الوظائف الجديدة.")
            break

        print(f"⏭️ الانتقال للصفحة التالية...")
        page += 1
        time.sleep(2)

    print(f"\n🎯 إجمالي الروابط الجديدة المستخرجة: {len(job_links)}")
    save_extracted_links(extracted_links)

    return list(job_links), extracted_links


def scrape_job(job_url):
    print("\n" + "-" * 70)
    print(f"جاري استخراج: {job_url}")

    html = get_page(job_url, render_js=True)
    if not html:
        print("❌ فشل تحميل الصفحة")
        return None

    soup = BeautifulSoup(html, "html.parser")
    json_ld = soup.find("script", type="application/ld+json")
    ld_data = {}

    if json_ld:
        try:
            raw_json = json.loads(json_ld.string)
            if isinstance(raw_json, list):
                for item in raw_json:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        ld_data = item
                        break
            elif isinstance(raw_json, dict) and raw_json.get("@type") == "JobPosting":
                ld_data = raw_json
        except Exception:
            pass

    title_elem = soup.find("h3", class_="job-title-text") or soup.find("h1")
    job_title = (
        ld_data.get("title")
        or (title_elem.get_text(strip=True) if title_elem else None)
        or "غير محدد"
    )

    print(f"   📋 العنوان المستخرج: {job_title[:60] if len(job_title) > 60 else job_title}")

    if job_title == "غير محدد" or len(job_title) < 3:
        print("⚠️ تم تجاهل الصفحة: لم يتم استخراج عنوان صحيح")
        return None

    comp_elem = soup.find("a", class_="job-meta-company")
    hiring_org = ld_data.get("hiringOrganization", {})
    ld_company = hiring_org.get("name") if isinstance(hiring_org, dict) else None

    company_name = (
        ld_company
        or (comp_elem.get_text(strip=True) if comp_elem else None)
        or "غير محدد"
    )

    location = "السعودية"
    loc_elem = soup.find("div", class_="job-meta-item")
    if loc_elem:
        extracted_location = loc_elem.get_text(" ", strip=True)
        if extracted_location:
            location = extracted_location

    location = re.sub(r"\s+", " ", location).strip()

    posted_date = ld_data.get("datePosted", "غير محدد")
    if posted_date and "T" in posted_date:
        posted_date = posted_date.split("T")[0]

    if posted_date == "غير محدد" or posted_date == "--":
        date_elem = soup.find("div", class_="job-date")
        if date_elem and date_elem.get("data-datetime"):
            datetime_str = date_elem.get("data-datetime")
            posted_date = datetime_str.split("T")[0] if "T" in datetime_str else datetime_str
        else:
            for elem in soup.find_all(["span", "div", "p"]):
                text = elem.get_text(strip=True)
                if text and len(text) < 50:
                    if any(k in text for k in ["2026", "2025", "2024", "-0", "/"]):
                        posted_date = text
                        break

    desc_body = soup.find("div", id="jobDescriptionBody") or soup.find("div", {"data-jb-field": "description"})
    if desc_body:
        full_description = desc_body.get_text(separator="\n", strip=True)
    else:
        raw_desc = ld_data.get("description", "")
        full_description = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n", strip=True) if raw_desc else ""

    full_description = re.sub(r"\n\s*\n", "\n", full_description).strip()

    if not full_description:
        print("⚠️ تم تجاهل الصفحة: الوصف فارغ")
        return None

    employment_type = ld_data.get("employmentType", "غير محدد")
    employment_type_map = {
        "FULL_TIME": "دوام كامل", "PART_TIME": "دوام جزئي", "CONTRACTOR": "عقد",
        "TEMPORARY": "مؤقت", "INTERN": "تدريب", "VOLUNTEER": "تطوعي",
        "PER_DIEM": "حسب اليوم", "OTHER": "أخرى"
    }
    employment_type = employment_type_map.get(employment_type, employment_type)

    salary_data = ld_data.get("baseSalary", {})
    salary = "غير محدد"
    if isinstance(salary_data, dict):
        salary_value = salary_data.get("value", {})
        if isinstance(salary_value, dict):
            salary = salary_value.get("value", "غير محدد")
            salary_unit = salary_value.get("unitText", "")
            if salary_unit:
                salary = f"{salary} ({salary_unit})"
        elif salary_value:
            salary = salary_value

    meta_divs = soup.find_all("div", class_="meta")
    if salary == "غير محدد":
        for meta_div in meta_divs:
            label_span = meta_div.find("span", class_="text-secondary")
            value_span = meta_div.find("span", class_="text-dark")
            if label_span and value_span:
                label = label_span.get_text(strip=True)
                value = value_span.get_text(strip=True)
                if any(k in label for k in ["الراتب", "الراتب الشهري", "salary"]):
                    if value and value != "Not Mentioned":
                        salary = value

    education = "غير محدد"
    description_lower = full_description.lower()
    if any(k in description_lower for k in ["bachelor", "bachelor's"]) or "بكالوريوس" in full_description:
        education = "بكالوريوس"
    elif any(k in description_lower for k in ["master", "master's"]) or "ماجستير" in full_description:
        education = "ماجستير"
    elif any(k in description_lower for k in ["phd", "doctorate"]) or "دكتوراه" in full_description:
        education = "دكتوراه"
    elif any(k in description_lower for k in ["high school", "secondary school"]) or "ثانوي" in full_description:
        education = "ثانوي"

    experience = "غير محدد"
    for meta_div in meta_divs:
        label_span = meta_div.find("span", class_="text-secondary")
        value_span = meta_div.find("span", class_="text-dark")

        if label_span and value_span:
            label = label_span.get_text(strip=True)
            value = value_span.get_text(" ", strip=True)

            if label.lower() == "experience" or "الخبرة" in label:
                if value and value != "Not Mentioned":
                    experience = value
                    break

    category = "غير محدد"
    field = "غير محدد"

    for meta_div in meta_divs:
        label_span = meta_div.find("span", class_="text-secondary")
        value_span = meta_div.find("span", class_="text-dark")
        if label_span and value_span:
            label = label_span.get_text(strip=True)
            value = value_span.get_text(strip=True)
            if "التصنيف" in label or "النوع" in label:
                if value and value != "Not Mentioned":
                    category = value
            elif "المجال" in label:
                if value and value != "Not Mentioned":
                    field = value

    if category == "غير محدد" or field == "غير محدد":
        dl_elements = soup.find_all("dl")
        for dl in dl_elements:
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                dt_text = dt.get_text(strip=True)
                dd_text = dd.get_text(strip=True)
                if "التصنيف" in dt_text or "النوع" in dt_text:
                    if dd_text and dd_text != "Not Mentioned":
                        category = dd_text
                elif "المجال" in dt_text:
                    if dd_text and dd_text != "Not Mentioned":
                        field = dd_text

    job_record = {
        "job_title": job_title,
        "company_name": company_name,
        "location": location,
        "posted_date": posted_date,
        "employment_type": employment_type,
        "salary": salary,
        "experience": experience,
        "education": education,
        "category": category,
        "field": field,
        "job_description": full_description,
        "job_url": job_url,
    }

    print(f"✅ تم بنجاح: {job_title} | {company_name}")
    return job_record


def scrape_tanqeeb_random_jobs():
    print("=" * 70)
    print("Tanqeeb Saudi - Tech Jobs Extractor (محسّن v3)")
    print("=" * 70)
    print(f"\n📁 مسارات الحفظ:")
    print(f"   📂 مجلد البيانات: {DATA_DIR}")
    print(f"   📄 ملف الوظائف: {JOBS_FILE}")
    print(f"   📋 ملف الروابط: {LINKS_CACHE_FILE}")

    existing_jobs = load_existing_jobs()
    print(f"\n📊 عدد الوظائف الموجودة بالفعل: {len(existing_jobs)}")
    
    if existing_jobs:
        print(f"   • أول وظيفة: {existing_jobs[0].get('job_title', 'غير محدد')}")
        print(f"   • من: {existing_jobs[0].get('company_name', 'غير محدد')}")

    new_job_links, all_extracted_links = get_job_links()

    if not new_job_links:
        print("❌ لم يتم العثور على روابط جديدة.")
        return

    random.shuffle(new_job_links)
    selected_links = new_job_links[:NUMBER_OF_JOBS]

    print(f"\n🎲 تم اختيار {len(selected_links)} وظيفة جديدة للتحميل...")

    new_jobs = []
    successfully_scraped = 0
    
    for index, job_url in enumerate(selected_links, start=1):
        print(f"\n[{index}/{len(selected_links)}]")
        
        if job_exists(existing_jobs, job_url):
            print(f"⏭️ هذه الوظيفة موجودة بالفعل، تجاهل...")
            continue
        
        job = scrape_job(job_url)
        if job:
            new_jobs.append(job)
            successfully_scraped += 1
        time.sleep(1.5)

    print(f"\n📊 إحصائيات الجمع:")
    print(f"   • الوظائف الموجودة: {len(existing_jobs)}")
    print(f"   • الوظائف الجديدة المستخرجة: {len(new_jobs)}")
    
    combined_jobs = existing_jobs + new_jobs
    
    unique_jobs = []
    seen_urls = set()
    for job in combined_jobs:
        if job.get("job_url") not in seen_urls:
            unique_jobs.append(job)
            seen_urls.add(job.get("job_url"))
    
    print(f"   • الإجمالي (بعد إزالة التكرارات): {len(unique_jobs)}")
    
    all_extracted_links.update(new_job_links)
    save_extracted_links(all_extracted_links)
    
    print(f"\n💾 جاري حفظ الوظائف...")
    save_jobs(unique_jobs)

    print("\n" + "=" * 70)
    print(f"✅ تم الانتهاء بنجاح!")
    print(f"   • وظائف مستخرجة جديدة: {successfully_scraped}")
    print(f"   • إجمالي الوظائف المحفوظة: {len(unique_jobs)}")
    print(f"   • المسار: {JOBS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    scrape_tanqeeb_random_jobs()