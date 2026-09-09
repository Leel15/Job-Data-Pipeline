import json
import re
import pandas as pd
import os
import sys
import io
from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.skills_extractor import extract_tech_skills

def clean_company_name(company_str):
    if pd.isna(company_str) or not str(company_str).strip() or "غير معلنة" in str(company_str):
        return None
    cleaned = re.sub(r'[^\w\s\-\.]', '', str(company_str))
    return cleaned.strip()

def clean_description(desc, job_title=""):
    if pd.isna(desc):
        return ""
    
    clean_text = re.sub(r'<[^<]+?>', '', str(desc))
    
    if job_title:
        clean_text = re.sub(rf'^(?:job title:|وصف الوظيفة:?)\s*{re.escape(job_title)}\s*', '', clean_text, flags=re.IGNORECASE)
    
    intro_phrases = [
        r'وصف الوظيفة', r'Job Summary', r'About the Role', r'About the job', 
        r'Job Purpose', r'Position Overview', r'Job Description', r'متطلبات الوظيفة', 
        r'المهارات المطلوبة', r'Required Qualifications'
    ]
    
    for phrase in intro_phrases:
        pattern = rf'^(?:[\s\-\:\•\📍\|]*{phrase})[\s\-\:\•\📍\|]*'
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
    clean_text = re.sub(r'^(?:Location|Type|Job Title)[:\s\w\,\|\–\-]+[\r\n]+', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'^Location\s*[A-Za-z\,\s]+(?:Saudi Arabia|KSA|الرياض|جدة|الدمام|الخبر|الظهران)?', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\s*\([^)]*\)', '', clean_text)
    clean_text = re.sub(r'[\#\*\•\-\❖\✔\[\]\?\!\\]', ' ', clean_text)
    clean_text = re.sub(r'View email address on click\.appcast\.io', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'#J-\d+-[a-zA-Z]+', '', clean_text)
    clean_text = re.sub(r'[\r\n\t]+', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def clean_city(location_str, desc_str="", title_str=""):
    city_mapping = {
        "الرياض": "Riyadh", "riyadh": "Riyadh",
        "جدة": "Jeddah", "jeddah": "Jeddah",
        "مكة المكرمة": "Mecca", "مكة": "Mecca", "makkah": "Mecca", "mecca": "Mecca",
        "المدينة المنورة": "Medina", "المدينة": "Medina", "medina": "Medina", "madinah": "Medina",
        "الدمام": "Dammam", "dammam": "Dammam",
        "الخبر": "Al Khobar", "khobar": "Al Khobar", "al khobar": "Al Khobar",
        "الظهران": "Dhahran", "dhahran": "Dhahran",
        "الجبيل": "Al Jubail", "jubail": "Al Jubail", "al jubail": "Al Jubail",
        "القصيم": "Al Qassim", "qassim": "Al Qassim", "al qassim": "Al Qassim", "بريدة": "Buraydah", "buraydah": "Buraydah", "عنيزة": "Unaizah", "unaizah": "Unaizah",
        "الشرقية": "Eastern Province", "eastern": "Eastern Province", "القطيف": "Qatif", "qatif": "Qatif", "رأس تنورة": "Ras Tanura", "ras tanura": "Ras Tanura", "البقيق": "Abqaiq", "abqaiq": "Abqaiq",
        "تبوك": "Tabuk", "tabuk": "Tabuk",
        "أبها": "Abha", "abha": "Abha", "خميس مشيط": "Khamis Mushait", "khamis mushait": "Khamis Mushait",
        "حائل": "Hail", "hail": "Hail",
        "نجران": "Najran", "najran": "Najran",
        "جيزان": "Jazan", "جازان": "Jazan", "jazan": "Jazan", "jivz": "Jazan",
        "الباحة": "Al Bahah", "al bahah": "Al Bahah", "bahah": "Al Bahah",
        "سكاكا": "Sakakah", "sakakah": "Sakakah", "الجوف": "Al Jouf", "al jouf": "Al Jouf", "الجو ف": "Al Jouf",
        "عرعر": "Arar", "arar": "Arar", "الحدود الشمالية": "Northern Borders",
        "حفر الباطن": "Hafar Al Batin", "hafar al batin": "Hafar Al Batin", "hafar albatin": "Hafar Al Batin",
        "الطائف": "Taif", "taif": "Taif",
        "ينبع": "Yanbu", "yanbu": "Yanbu",
        "الخفجي": "Khafji", "khafji": "Khafji",
        "رابغ": "Rabigh", "rabigh": "Rabigh",
        "الدرعية": "Diriyah", "diriyah": "Diriyah",
        "المجمعة": "Majmaah", "majmaah": "Majmaah",
    }
    
    if desc_str and not pd.isna(desc_str):
        desc_lower = str(desc_str).lower()
        for key, val in city_mapping.items():
            if key.lower() in desc_lower:
                return val

    if title_str and not pd.isna(title_str):
        title_lower = str(title_str).lower()
        for key, val in city_mapping.items():
            if key.lower() in title_lower:
                return val

    if location_str and not pd.isna(location_str):
        loc_lower = str(location_str).strip().lower()
        if loc_lower not in {"saudi arabia", "ksa", "kingdom of saudi arabia", "السعودية"}:
            for key, val in city_mapping.items():
                if key.lower() in loc_lower:
                    return val

    return None

def clean_employment_type(emp_type, title_str="", desc_str=""):
    title_lower = str(title_str).lower()
    emp_lower = str(emp_type).lower()
    desc_lower = str(desc_str).lower()
    
    if any(term in title_lower or term in emp_lower for term in ["intern", "تدريب"]) or any(term in desc_lower for term in ["internship", "تدريب تعاوني", "co-op", "summer intern"]):
        return "Internship"
        
    if any(term in title_lower or term in emp_lower for term in ["part time", "part-time", "جزئي"]) or "part-time" in desc_lower:
        return "Part-time"
        
    if any(term in title_lower or term in emp_lower for term in ["contract", "عقد"]) or "contract role" in desc_lower:
        return "Contract"
        
    return "Full-time"

def extract_education(desc_str):
    if pd.isna(desc_str) or not str(desc_str).strip():
        return None
    desc_lower = str(desc_str).lower()
    
    if any(term in desc_lower for term in ["undergraduate", "bachelor", "bachelors", "bsc", "b.sc", "بكالوريوس", "b.tech", "b.s."]):
        return "Bachelor"
    elif any(term in desc_lower for term in ["master's", "masters degree", "master degree", "ماجستير", "mba"]):
        return "Master"
    elif "master" in desc_lower and not any(f in desc_lower for f in ["master the", "mastering", "master class"]):
        return "Master"
    elif any(term in desc_lower for term in ["phd", "دكتوراه", "doctorate"]):
        return "PhD"
    elif any(term in desc_lower for term in ["diploma", "دبلوم", "high school", "ثانوي"]):
        return "High School / Diploma"
        
    return None

def parse_relative_date(posted_str):
    if not posted_str or pd.isna(posted_str):
        return datetime.now().strftime('%Y-%m-%d')
    
    posted_str = str(posted_str).strip()
    today = datetime.now()
    
    numbers = re.findall(r'\d+', posted_str)
    if numbers:
        days_ago = int(numbers[0])
        approx_date = today - timedelta(days=days_ago)
        return approx_date.strftime('%Y-%m-%d')
        
    return today.strftime('%Y-%m-%d')

def clean_job_title_from_location(job_title):
    if not job_title or not isinstance(job_title, str):
        return job_title
    
    locations = ["الرياض", "جدة", "الدمام", "الخبر", "الجبيل", "Riyadh", "Jeddah", "Dammam", "Al Khobar", "Al Jubail", "Tabuk", "Abha", "Buraydah", "Al Qassim", "Qassim", "Saudi Arabia", "KSA", "Saudi National", "Saudi"]
    
    cleaned = job_title
    cleaned = re.sub(r'\s*[\-\–\,]?\s*(?:posted|منذ)\s+.*$', '', cleaned, flags=re.IGNORECASE)
    
    loc_pattern_start = r'^(?:' + '|'.join(re.escape(loc) for loc in locations) + r')[\s\,\-\•\–]+'
    for _ in range(3):
        cleaned = re.sub(loc_pattern_start, '', cleaned, flags=re.IGNORECASE)

    loc_pattern_end = r'\s*[\-\–,]\s*(?:' + '|'.join(re.escape(loc) for loc in locations) + r')(?:\s*[\-\–,]\s*(?:' + '|'.join(re.escape(loc) for loc in locations) + r'))*$'
    cleaned = re.sub(loc_pattern_end, '', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r'\s*\([^)]*(?:' + '|'.join(re.escape(loc) for loc in locations) + r'|Part Time|Without Accommodation)[^)]*\)$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^[,\-\s]+|[,\-\s]+$', '', cleaned).strip()
    
    return cleaned if cleaned else job_title

def fetch_data_from_bronze():
    load_dotenv()
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is missing from environment variables!")
        
    service_client = DataLakeServiceClient.from_connection_string(CONNECTION_STRING)
    bronze_client = service_client.get_file_system_client(file_system="bronze")
    
    paths = bronze_client.get_paths()
    all_data = []
    
    for path in paths:
        if not path.is_directory and "saudi_technical_jobs.json" in path.name.lower():
            print(f"Fetching JSON file from Azure Bronze: {path.name}")
            file_client = bronze_client.get_file_client(path.name)
            download = file_client.download_file()
            file_content = download.readall()
            
            all_data = json.loads(file_content.decode('utf-8'))
            break
            
    print(f"Successfully loaded {len(all_data)} records from Azure JSON file.")
    return all_data

def upload_to_silver_azure(df_data, silver_file_name):
    load_dotenv()
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is missing from environment variables!")
        
    service_client = DataLakeServiceClient.from_connection_string(CONNECTION_STRING)
    silver_client = service_client.get_file_system_client(file_system="silver")
    
    file_client = silver_client.get_file_client(silver_file_name)
    
    parquet_buffer = io.BytesIO()
    df_data.to_parquet(parquet_buffer, index=False, engine='pyarrow')
    parquet_buffer.seek(0)
    
    file_client.upload_data(parquet_buffer.read(), overwrite=True)
    print(f"Successfully uploaded DataFrame to 'silver' container as '{silver_file_name}'!")

def process_jsearch_azure_cleaning(output_json_path):
    raw_data = fetch_data_from_bronze()

    standardized_jobs = []
    print(f"Processing {len(raw_data)} records from Bronze container...")

    skipped_us = 0
    skipped_short_desc = 0
    skipped_bad_url = 0

    for item in raw_data:
        desc_check = str(item.get('job_description', '')).lower()
        loc_check = str(item.get('job_location', '')).lower()
        if "united states" in desc_check or "united states" in loc_check or "u.s. citizen" in desc_check or "us citizen" in desc_check:
            skipped_us += 1
            continue

        company_name = clean_company_name(item.get('employer_name'))
        raw_title = item.get('job_title', '')
        job_title = clean_job_title_from_location(raw_title)
        
        raw_desc = item.get('job_description', '')
        job_description = clean_description(raw_desc, job_title)
        
        if len(job_description) < 50:
            skipped_short_desc += 1
            continue
            
        job_url = item.get('job_apply_link')
        if not job_url or not str(job_url).strip().lower().startswith('http'):
            skipped_bad_url += 1
            continue
        
        city = clean_city(item.get('job_city'), job_description, raw_title)
        country = "Saudi Arabia"
        posted_date = parse_relative_date(item.get('job_posted_at'))
        
        employment_type = clean_employment_type(item.get('job_employment_type'), raw_title, job_description)
        education = extract_education(job_description)
        skills = extract_tech_skills(job_description)

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": skills,
            "job_url": job_url
        }

        standardized_jobs.append(common_schema_item)

    print(f"Skipped {skipped_us} US/Foreign jobs.")
    print(f"Skipped {skipped_short_desc} jobs with descriptions under 50 characters.")
    print(f"Skipped {skipped_bad_url} jobs with invalid or missing URLs.")

    df_temp = pd.DataFrame(standardized_jobs)
    
    total_before_dedup = len(df_temp)
    duplicates = df_temp[df_temp.duplicated(subset=['company_name', 'job_title', 'job_description'], keep=False)]
    print(f"Total rows before duplicate removal: {total_before_dedup}")
    print(f"Total duplicate rows detected: {len(duplicates)}")
    
    if not duplicates.empty:
        print("Sample of duplicated jobs found:")
        print(duplicates[['company_name', 'job_title']].drop_duplicates().head(5))
        
    df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
    print(f"Total rows after duplicate removal: {len(df_temp)}")
    
    df_temp = df_temp.where(pd.notnull(df_temp), None)
    print(f"Total clean JSearch jobs processed: {len(df_temp)}")

    # 1. حفظ ملف الـ JSON محلياً
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    cleaned_records = df_temp.to_dict(orient='records')
    
    def custom_dumps(data):
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        json_str = re.sub(
            r'"skills":\s*\[\s*(.*?)\s*\]', 
            lambda m: f'"skills": [{", ".join(s.strip() for s in re.findall(r"\"[^\"]+\"", m.group(1)))}]', 
            json_str, 
            flags=re.DOTALL
        )
        return json_str

    json_string = custom_dumps(cleaned_records)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(json_string)
    print(f"Successfully saved local JSON file to: {output_json_path}")

    # 2. رفع ملف الـ Parquet إلى Azure Silver
    silver_filename = "standardized_jsearch_jobs.parquet"
    upload_to_silver_azure(df_temp, silver_filename)

if __name__ == "__main__":
    OUTPUT_JSON = "data/Processed/standardized_jsearch_jobs.json"
    process_jsearch_azure_cleaning(OUTPUT_JSON)