import json
import os
import re
import random
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import requests


SCRAPEOPS_API_KEY = "9277d0e7-b4e7-433a-b782-4864aa7a7a1b"

BASE_URL = "https://saudi.tanqeeb.com"
TARGET_URL = "https://saudi.tanqeeb.com/ar"

NUMBER_OF_JOBS = 50

# البحث عن تخصصات تقنية متعددة
TECH_KEYWORDS = [
    "python developer",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "devops engineer",
    "machine learning",
    "data scientist",
    "cloud engineer",
    "database administrator",
    "systems engineer",
    "software engineer",
]

SEARCH_PARAMS = {
    "country": "54",          
    "state": "0",
    "category": "-1",
    "workplace": "0",
    "search_period": "0",
    "lang": "all"
}


def get_scrapeops_url(url):
    payload = {
        "api_key": SCRAPEOPS_API_KEY,
        "url": url,
    }

    return "https://proxy.scrapeops.io/v1/?" + urlencode(payload)


def get_page(url):
    try:
        response = requests.get(
            get_scrapeops_url(url),
            timeout=60
        )

        if response.status_code == 200:
            return response.text

        print(
            f"❌ فشل تحميل الصفحة: "
            f"{response.status_code}"
        )

    except Exception as e:
        print(f"❌ خطأ أثناء تحميل الصفحة: {e}")

    return None


def get_job_links(keyword=None, search_params=None, page=1):
    """البحث عن روابط الوظائف في صفحة واحدة فقط"""
    if search_params is None:
        search_params = SEARCH_PARAMS
    
    if keyword:
        print(f"  🔍 {keyword}", end=" - ")
    else:
        print(f"  🔍 جاري البحث عن وظائف السعودية", end=" - ")

    job_links = set()

    # بناء رابط الصفحة مع المعاملات
    if page == 1:
        if keyword:
            query_string = urlencode({**search_params, "keywords": keyword})
            page_url = f"https://saudi.tanqeeb.com/ar/jobs/search?{query_string}"
        else:
            page_url = TARGET_URL
    else:
        if keyword:
            query_string = urlencode({**search_params, "keywords": keyword})
            page_url = f"https://saudi.tanqeeb.com/ar/jobs/search/page/{page}/?{query_string}"
        else:
            page_url = f"https://saudi.tanqeeb.com/ar/jobs/search/page/{page}/"

    html = get_page(page_url)

    if not html:
        print(f"❌ فشل التحميل")
        return job_links

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # البحث عن الروابط في الصفحة الحالية
    page_job_links = 0

    for a in soup.find_all("a", href=True):

        href = a.get("href", "").strip()

        if not href:
            continue

        full_url = urljoin(
            BASE_URL,
            href
        )

        if not full_url.startswith(
            "https://saudi.tanqeeb.com/"
        ):
            continue

        if re.search(
            r"/jobs-in-saudi/.*/jobs/\d+\.html",
            full_url
        ):

            if full_url not in job_links:
                job_links.add(full_url)
                page_job_links += 1

    print(f"✅ {page_job_links} وظيفة")

    job_links = list(job_links)

    return job_links


def scrape_job(job_url):

    print("\n" + "-" * 70)
    print("جاري استخراج الوظيفة:")
    print(job_url)

    html = get_page(job_url)

    if not html:
        return None

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # التحقق من أن الصفحة تم تحميلها بشكل صحيح
    if "JavaScript is disabled" in html or not soup.find("h3", class_="job-title-text"):
        print(f"⚠️ الصفحة لم يتم تحميلها بشكل صحيح (JavaScript)")
        return None

    json_ld = soup.find(
        "script",
        type="application/ld+json"
    )

    ld_data = {}

    if json_ld:

        try:

            raw_json = json.loads(
                json_ld.string
            )

            if isinstance(
                raw_json,
                list
            ):

                for item in raw_json:

                    if isinstance(
                        item,
                        dict
                    ):

                        if item.get(
                            "@type"
                        ) == "JobPosting":

                            ld_data = item
                            break

            elif isinstance(
                raw_json,
                dict
            ):

                if raw_json.get(
                    "@type"
                ) == "JobPosting":

                    ld_data = raw_json

        except Exception:
            pass

    title_elem = (
        soup.find(
            "h3",
            class_="job-title-text"
        )
        or soup.find("h1")
    )

    job_title = (
        ld_data.get("title")
        or (
            title_elem.get_text(
                strip=True
            )
            if title_elem
            else None
        )
        or "غير محدد"
    )

    comp_elem = soup.find(
        "a",
        class_="job-meta-company"
    )

    hiring_org = ld_data.get(
        "hiringOrganization",
        {}
    )

    if isinstance(
        hiring_org,
        dict
    ):

        ld_company = hiring_org.get(
            "name"
        )

    else:

        ld_company = None

    company_name = (
        ld_company
        or (
            comp_elem.get_text(
                strip=True
            )
            if comp_elem
            else None
        )
        or "غير محدد"
    )

    location = "السعودية"

    loc_elem = soup.find(
        "div",
        class_="job-meta-item"
    )

    if loc_elem:

        extracted_location = (
            loc_elem.get_text(
                " ",
                strip=True
            )
        )

        if extracted_location:

            location = extracted_location

    location_lower = location.lower()

    saudi_keywords = [
        "السعودية",
        "السعوديه",
        "saudi",
        "riyadh",
        "الرياض",
        "jeddah",
        "جدة",
        "dammam",
        "الدمام",
        "khobar",
        "الخبر",
        "qassim",
        "Al Qasim",
        "القصيم",
        "mecca",
        "مكة",
        "medina",
        "المدينة",
        "tabuk",
        "تبوك",
        "abha",
        "أبها",
    ]

    is_saudi = any(
        keyword.lower()
        in location_lower
        for keyword in saudi_keywords
    )

    if not is_saudi:

        print(
            f"⚠️ تم تجاهل الوظيفة لأن الموقع "
            f"غير سعودي: {location}"
        )

        return None

    posted_date = ld_data.get(
        "datePosted",
        "غير محدد"
    )

    if posted_date and "T" in posted_date:
        posted_date = (
            posted_date.split("T")[0]
        )
    
    # البحث عن التاريخ في HTML إذا لم يتم العثور عليه
    if posted_date == "غير محدد" or posted_date == "--":
        date_elem = soup.find("div", class_="job-date")
        if date_elem and date_elem.get("data-datetime"):
            datetime_str = date_elem.get("data-datetime")
            if "T" in datetime_str:
                posted_date = datetime_str.split("T")[0]
            else:
                posted_date = datetime_str
        else:
            for elem in soup.find_all(["span", "div", "p"]):
                text = elem.get_text(strip=True)
                if text and len(text) < 50:
                    if any(keyword in text for keyword in ["2026", "2025", "2024", "-0", "/"]):
                        posted_date = text
                        break

    desc_body = (
        soup.find(
            "div",
            id="jobDescriptionBody"
        )
        or soup.find(
            "div",
            {
                "data-jb-field":
                "description"
            }
        )
    )

    if desc_body:

        full_description = (
            desc_body.get_text(
                separator="\n",
                strip=True
            )
        )

    else:

        raw_desc = ld_data.get(
            "description",
            ""
        )

        full_description = (
            BeautifulSoup(
                raw_desc,
                "html.parser"
            ).get_text(
                separator="\n",
                strip=True
            )
        )

    full_description = re.sub(
        r"\n\s*\n",
        "\n",
        full_description
    )

    employment_type = ld_data.get(
        "employmentType",
        "غير محدد"
    )

    employment_type_map = {
        "FULL_TIME": "دوام كامل",
        "PART_TIME": "دوام جزئي",
        "CONTRACTOR": "عقد",
        "TEMPORARY": "مؤقت",
        "INTERN": "تدريب",
        "VOLUNTEER": "تطوعي",
        "PER_DIEM": "حسب اليوم",
        "OTHER": "أخرى"
    }

    employment_type = employment_type_map.get(
        employment_type,
        employment_type
    )

    salary_data = ld_data.get(
        "baseSalary",
        {}
    )

    salary = "غير محدد"

    if isinstance(salary_data, dict):

        salary_value = salary_data.get(
            "value",
            {}
        )

        if isinstance(salary_value, dict):

            salary = salary_value.get(
                "value",
                "غير محدد"
            )

            salary_unit = salary_value.get(
                "unitText",
                ""
            )

            if salary_unit:
                salary = f"{salary} ({salary_unit})"

        elif salary_value:
            salary = salary_value
    
    # تعريف meta_divs هنا لاستخدامه لاحقاً
    meta_divs = soup.find_all("div", class_="meta")
    
    # البحث عن الراتب في HTML باستخدام meta-data
    if salary == "غير محدد":
        for meta_div in meta_divs:
            label_span = meta_div.find("span", class_="text-secondary")
            value_span = meta_div.find("span", class_="text-dark")
            
            if label_span and value_span:
                label = label_span.get_text(strip=True)
                value = value_span.get_text(strip=True)
                
                if any(keyword in label for keyword in ["الراتب", "الراتب الشهري", "salary"]):
                    if value and value != "Not Mentioned":
                        salary = value

    education = "غير محدد"

    description_lower = full_description.lower()

    if (
        "bachelor" in description_lower
        or "bachelor's" in description_lower
        or "بكالوريوس" in full_description
    ):
        education = "بكالوريوس"

    elif (
        "master" in description_lower
        or "master's" in description_lower
        or "ماجستير" in full_description
    ):
        education = "ماجستير"

    elif (
        "phd" in description_lower
        or "doctorate" in description_lower
        or "دكتوراه" in full_description
    ):
        education = "دكتوراه"

    elif (
        "high school" in description_lower
        or "secondary school" in description_lower
        or "secondary education" in description_lower
        or "ثانوي" in full_description
        or "الثانوية" in full_description
        or "شهادة الثانوية" in full_description
    ):
        education = "ثانوي"

    experience = "غير محدد"

    experience_match = re.search(
        r"(?:minimum|min|at least|خبرة لا تقل عن|خبرة)\s*"
        r"(\d+(?:-\d+)?)\s*(?:years?|سنوات?|سنة)",
        full_description,
        re.IGNORECASE
    )

    if experience_match:
        experience = experience_match.group(0)

    # ===== استخراج التصنيف والمجال من HTML =====
    category = "غير محدد"
    field = "غير محدد"

    # الطريقة 1: البحث عن عناصر meta-data بـ class="meta" (meta_divs تم تعريفه مسبقاً)
    
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
    
    # الطريقة 2: البحث عن dl/dt/dd elements
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
    
    # الطريقة 3: البحث عن meta-data-title و meta-data-value
    if category == "غير محدد" or field == "غير محدد":
        metadata_items = soup.find_all("div", class_="meta-data-item")
        for item in metadata_items:
            title = item.find(class_="meta-data-title")
            value = item.find(class_="meta-data-value")
            
            if title and value:
                title_text = title.get_text(strip=True)
                value_text = value.get_text(strip=True)
                
                if "التصنيف" in title_text:
                    if value_text and value_text != "Not Mentioned":
                        category = value_text
                elif "المجال" in title_text:
                    if value_text and value_text != "Not Mentioned":
                        field = value_text

    # التحقق من أن الوظيفة لم تكن صفحة "JavaScript is disabled"
    if job_title == "JavaScript is disabled" or not full_description:
        print(f"⚠️ تم تجاهل الوظيفة - الصفحة لم يتم تحميلها بشكل صحيح")
        return None
 
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

    print("✅ تم استخراج الوظيفة")
    print(f"المسمى: {job_title}")
    print(f"الشركة: {company_name}")
    print(f"الموقع: {location}")
    print(f"التاريخ: {posted_date}")
    print(f"الراتب: {salary}")
    print(f"التصنيف: {category}")
    print(f"المجال: {field}")

    return job_record


def scrape_tanqeeb_random_jobs():

    print("=" * 70)
    print("Tanqeeb Saudi - Tech Jobs - Multiple Pages & Keywords (تنويع الوظائف)")
    print("=" * 70)

    all_job_links = set()
    page = 1
    max_pages = 5  # حد أقصى للصفحات للبحث
    
    # حلقة على الصفحات
    while len(all_job_links) < NUMBER_OF_JOBS and page <= max_pages:
        print(f"\n📄 الصفحة {page}")
        print("-" * 70)
        
        # حلقة على كل تخصص في الصفحة الحالية
        for keyword in TECH_KEYWORDS:
            links = get_job_links(keyword=keyword, search_params=SEARCH_PARAMS, page=page)
            all_job_links.update(links)
            
            # إذا وصلنا للعدد المطلوب، توقف
            if len(all_job_links) >= NUMBER_OF_JOBS:
                break
        
        print(f"📊 الإجمالي حتى الآن: {len(all_job_links)} وظيفة")
        page += 1
    
    all_job_links = list(all_job_links)

    if not all_job_links:

        print(
            "❌ لم يتم العثور على أي وظائف."
        )

        return

   
    random.shuffle(all_job_links)

    selected_links = all_job_links[
        :NUMBER_OF_JOBS
    ]

    print(
        f"\n🎲 تم اختيار "
        f"{len(selected_links)} وظائف عشوائية."
    )

  
    jobs = []

    for index, job_url in enumerate(
        selected_links,
        start=1
    ):

        print(
            f"\n[{index}/{len(selected_links)}]"
        )

        job = scrape_job(job_url)

        if job:

            jobs.append(job)

 
    if len(jobs) < NUMBER_OF_JOBS:

        print(
            f"\n⚠️ تم استخراج "
            f"{len(jobs)} فقط من أصل "
            f"{NUMBER_OF_JOBS}."
        )

  
    os.makedirs(
        "data/raw",
        exist_ok=True
    )

    output_path = (
        "data/raw/tanqeeb_saudi_jobs_tech2.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=2
        )

  
    print("\n")
    print("=" * 70)
    print("✅ تم الانتهاء بنجاح")
    print("=" * 70)

    print(
        f"عدد الوظائف المستخرجة: {len(jobs)} من {NUMBER_OF_JOBS}"
    )

    print(
        f"📁 تم الحفظ في:"
        f" {output_path}"
    )

    print("\n🔍 التخصصات المبحوث عنها:")
    for i, keyword in enumerate(TECH_KEYWORDS[:len(TECH_KEYWORDS)], 1):
        print(f"  {i}. {keyword}")

    print("\n📋 الوظائف المستخرجة:")

    for index, job in enumerate(
        jobs,
        start=1
    ):

        print(
            f"{index}. "
            f"{job['job_title']} "
            f"- {job['company_name']} "
            f"- {job['location']}"
        )


if __name__ == "__main__":

    scrape_tanqeeb_random_jobs()