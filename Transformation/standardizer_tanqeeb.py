import json
import re
import pandas as pd
import os
import sys
import time
from deep_translator import GoogleTranslator
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.skills_extractor import extract_tech_skills

def fetch_tanqeeb_data_from_bronze():
    load_dotenv()
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is missing from environment variables!")
        
    service_client = DataLakeServiceClient.from_connection_string(CONNECTION_STRING)
    bronze_client = service_client.get_file_system_client(file_system="bronze")
    
    paths = bronze_client.get_paths()
    all_data = []
    
    for path in paths:
        if not path.is_directory and "tanqeeb_saudi_jobs_tech.json" in path.name.lower():
            print(f"Fetching JSON file from Azure: {path.name}")
            file_client = bronze_client.get_file_client(path.name)
            download = file_client.download_file()
            file_content = download.readall()
            
            decoded_content = file_content.decode('utf-8', errors='replace')
            all_data = json.loads(decoded_content)
            break
            
    print(f"Successfully loaded {len(all_data)} records from Azure JSON file.")
    return all_data

def upload_to_silver_container(local_file_path, blob_name):
    load_dotenv()
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    service_client = DataLakeServiceClient.from_connection_string(CONNECTION_STRING)
    silver_client = service_client.get_file_system_client(file_system="silver")
    
    file_client = silver_client.get_file_client(blob_name)
    
    with open(local_file_path, "rb") as data:
        file_client.upload_data(data, overwrite=True)
        
    print(f"Successfully uploaded {blob_name} to Azure Silver container!")

def clean_company_name(company_str):
    if pd.isna(company_str) or not str(company_str).strip():
        return "Not Specified"
    cleaned = re.sub(r'^(client of\s+)', '', str(company_str).strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned)
    return cleaned.strip()

def clean_city(location_str, desc_str=""):
    city_mapping = {
        "الرياض": "Riyadh", "riyadh": "Riyadh",
        "جدة": "Jeddah", "jeddah": "Jeddah",
        "المدينة المنورة": "Medina", "medina": "Medina", "madinah": "Medina",
        "مكة المكرمة": "Mecca", "مكة": "Mecca", "makkah": "Mecca", "mecca": "Mecca",
        "الدمام": "Dammam", "dammam": "Dammam",
        "الخبر": "Al Khobar", "khobar": "Al Khobar", "al khobar": "Al Khobar",
        "الجبيل": "Al Jubail", "jubail": "Al Jubail",
        "القصيم": "Al Qasim", "qassim": "Al Qasim",
        "الشرقية": "Eastern Province", "eastern": "Eastern Province"
    }
    
    if desc_str and not pd.isna(desc_str):
        desc_lower = str(desc_str).lower()
        for key, val in city_mapping.items():
            if key in desc_lower or key.lower() in desc_lower:
                return val

    if pd.isna(location_str) or not str(location_str).strip():
        return None
        
    loc_lower = str(location_str).strip().lower()
    
    if loc_lower in {"saudi arabia", "ksa", "kingdom of saudi arabia", "السعودية"}:
        return None

    for key, val in city_mapping.items():
        if key in loc_lower:
            return val
            
    for key, val in city_mapping.items():
        if key in str(location_str):
            return val

    return None

def clean_employment_type(emp_type, desc_str=""):
    combined_text = f"{str(emp_type)} {str(desc_str)}".lower()
    
    if "part-time" in combined_text or "part time" in combined_text or "دوام جزئي" in combined_text:
        return "Part-time"
    elif "contract" in combined_text or "عقد" in combined_text or "freelance" in combined_text:
        return "Contract"
    elif "full-time" in combined_text or "full time" in combined_text or "دوام كامل" in combined_text:
        return "Full-time"
        
    return "Full-time"

def extract_education(desc_str):
    if pd.isna(desc_str) or not str(desc_str).strip():
        return None
        
    desc_lower = str(desc_str).lower()
    
    if any(term in desc_lower for term in ["bachelor", "bachelors", "bsc", "b.sc", "بكالوريوس", "b.tech", "البكالوريوس"]):
        return "Bachelor"
    elif any(term in desc_lower for term in ["master", "masters", "ماجستير", "mba"]):
        return "Master"
    elif any(term in desc_lower for term in ["phd", "ph.d", "دكتوراه", "doctorate"]):
        return "PhD"
    elif any(term in desc_lower for term in ["high school", "ثانوي", "دبلوم", "diploma"]):
        return "High School / Diploma"
        
    return None

def clean_description(desc):
    if pd.isna(desc):
        return ""
    clean_text = re.sub(r'<[^<]+?>', '', str(desc))
    clean_text = re.sub(r'[\r\n\t]+', ' ', clean_text)
    clean_text = re.sub(r'[\*\•\-\❖\✔\[\]\?\!\#]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def check_if_tech_job(job_title, description, skills):
    title_lower = str(job_title).lower()
    desc_lower = str(description).lower()

    infra_keywords = [
        "نظم تشغيل", "systems specialist", "system specialist", "backup", 
        "disaster recovery", "سيرفرات", "network", 
        "sysadmin", "system administrator", "cloud", "devops", "systems"
    ]
    
    if any(keyword in title_lower or keyword in desc_lower for keyword in infra_keywords):
        return True

    tech_degrees = [
        "علوم الحاسب", "تقنية المعلومات", "هندسة البرمجيات", "هندسة الحاسب", 
        "نظم المعلومات", "الأمن السيبراني", "الذكاء الاصطناعي", "علم البيانات", 
        "computer science", "information technology", "software engineering", 
        "computer engineering", "information systems", "cybersecurity", 
        "artificial intelligence", "data science"
    ]
    
    if any(deg in desc_lower for deg in tech_degrees):
        return True

    title_blocklist = [
        "محاسب", "أمين مستودع", "مشتريات", "علاقات عامة", "تجزئة", 
        "مستودع", "مدير منطقة", "لوجستيات", "عقود", "تسويق", "حسابات", 
        "صانع محتوى", "مدير العمليات", "أخصائي نمو", "تطوير أعمال",
        "رئيس تعلم", "مدير تطوير", "استشاري لوجستيات", "خدمات صيانة", 
        "مساعد مدير", "موردين", "مكتب مساعدة", "سلاسل الإمداد",
        "مبيعات", "مدير حساب", "مدير مبيعات",
        "sales", "account manager", "business development", "marketing", 
        "content", "logistics", "supply chain", "procurement", "hr", 
        "recruitment", "real estate", "housekeeping", "soft services", 
        "loyalty", "hospitality", "cleaning", "facility", "facilities",
        "finance", "accounting", "market risk", "treasury", 
        "instructional design", "recruiter", "retail", "district manager",
        "maps evaluator", "vendor", "supplier", "helpdesk",
        "global mqa", "manufacturing quality", "quality assurance engineer"
    ]
    
    for word in title_blocklist:
        if word in title_lower:
            return False

    heavy_blocklist = [
        "icaap", "stress testing", "basel", "enterprise risk management",
        "مخاطر مصرفية", "مخاطر السوق", "مخاطر الائتمان", "مخاطر التشغيل",
        "odm", "ems", "smts", "assembly line", "manufacturing operations"
    ]

    is_cyber_risk = "أمن" in desc_lower or "cyber" in desc_lower or "سيبراني" in desc_lower or "أمن المعلومات" in desc_lower

    if not is_cyber_risk:
        for term in heavy_blocklist:
            if term in title_lower or term in desc_lower:
                return False

    if skills and len(skills) > 0:
        return True

    return False

def translate_to_english_if_arabic(text):
    if not text or pd.isna(text):
        return text
    
    text_str = str(text)
    
    max_total_retries = 3
    for global_attempt in range(max_total_retries):
        if not re.search(r'[\u0600-\u06FF]', text_str):
            break 
            
        try:
            translator = GoogleTranslator(source='ar', target='en')
            chunks = [text_str[i:i+1500] for i in range(0, len(text_str), 1500)]
            translated_chunks = []
            
            for chunk in chunks:
                if re.search(r'[\u0600-\u06FF]', chunk):
                    success = False
                    for attempt in range(3):
                        try:
                            res = translator.translate(chunk)
                            if res and not re.search(r'[\u0600-\u06FF]', res):
                                translated_chunks.append(res)
                                success = True
                                time.sleep(1.5) 
                                break
                            else:
                                time.sleep(2)
                        except:
                            time.sleep(3)
                    
                    if not success:
                        translated_chunks.append(chunk) 
                else:
                    translated_chunks.append(chunk)
            
            translated_text = " ".join(translated_chunks)
            if not re.search(r'[\u0600-\u06FF]', translated_text):
                return translated_text
            else:
                text_str = translated_text 
                time.sleep(3)
        except Exception as e:
            time.sleep(4)
            
    return text_str
def process_tanqeeb_deep_cleaning(output_json_path):
    raw_data = fetch_tanqeeb_data_from_bronze()

    standardized_jobs = []
    print(f"Deep cleaning and filtering {len(raw_data)} records from Tanqeeb...")

    non_tech_count = 0
    for item in raw_data:
        company_name = clean_company_name(item.get('company_name'))
        job_title = item.get('job_title', 'Technical Professional').strip()
        job_title = re.sub(r'[^\w\s\/\-\(\)\.\,\+]', '', job_title).strip()
        
        raw_desc = item.get('job_description', '')
        job_description = clean_description(raw_desc)
        
        city = clean_city(item.get('location'), raw_desc)
        country = "Saudi Arabia"
        posted_date = item.get('posted_date')
        employment_type = clean_employment_type(item.get('employment_type'), raw_desc)
        education = extract_education(raw_desc)
        
        skills = extract_tech_skills(job_description)
        
        is_tech = check_if_tech_job(job_title, job_description, skills)

        if not is_tech:
            non_tech_count += 1
            continue
        
        job_url = item.get('job_url')

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

    df_temp = pd.DataFrame(standardized_jobs)
    print(f"Total non-tech jobs excluded: {non_tech_count}")

    duplicates = df_temp[df_temp.duplicated(subset=['company_name', 'job_title', 'job_description'], keep=False)]
    if not duplicates.empty:
        print("--- الوظائف المتكررة التي سيتم حذفها ---")
        print(duplicates[['company_name', 'job_title']])

    df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
    df_temp = df_temp.where(pd.notnull(df_temp), None)

    print("Checking and translating Arabic fields to English...")
    df_temp['job_title'] = df_temp['job_title'].apply(translate_to_english_if_arabic)
    df_temp['job_title'] = df_temp['job_title'].apply(lambda x: ' '.join(dict.fromkeys(x.split())) if pd.notna(x) else x)
    df_temp['job_description'] = df_temp['job_description'].apply(translate_to_english_if_arabic)
    print("Re-extracting tech skills from translated descriptions...")
    df_temp['skills'] = df_temp['job_description'].apply(lambda desc: extract_tech_skills(str(desc)))

    print(f"Total final unique tech jobs saved: {len(df_temp)}")

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    
    cleaned_records = df_temp.to_dict(orient='records')
    class SkillsEncoder(json.JSONEncoder):
        def encode(self, o):
            if isinstance(o, list):
                return '[' + ', '.join(json.dumps(item, ensure_ascii=False) for item in o) + ']'
            return super().encode(o)

    def custom_dumps(data):
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        json_str = re.sub(r'"skills":\s*\[\s*(.*?)\s*\]', lambda m: f'"skills": [{", ".join(s.strip() for s in re.findall(r"\"[^\"]+\"", m.group(1)))}]', json_str, flags=re.DOTALL)
        return json_str

    json_string = custom_dumps(cleaned_records)

    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(json_string)

    print(f"Successfully saved clean standardized JSON file to: {output_json_path}")

    output_parquet_path = output_json_path.replace('.json', '.parquet')
    df_temp.to_parquet(output_parquet_path, index=False, engine='pyarrow')
    print(f"Successfully saved clean standardized Parquet file to: {output_parquet_path}")

    return output_parquet_path

if __name__ == "__main__":
    OUTPUT_JSON = "data/Silver/standardized_tanqeeb_jobs.json"
    
    parquet_path = process_tanqeeb_deep_cleaning(OUTPUT_JSON)
    
    upload_to_silver_container(parquet_path, "standardized_tanqeeb_jobs.parquet")