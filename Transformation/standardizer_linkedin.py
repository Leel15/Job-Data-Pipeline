import json
import re
from datetime import datetime
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.skills_extractor import extract_tech_skills

def clean_company_name(company_str):
    if pd.isna(company_str) or not str(company_str).strip():
        return "Not Specified"
    cleaned = re.sub(r'^(client of\s+)', '', str(company_str).strip(), flags=re.IGNORECASE)
    return cleaned.strip()

import pandas as pd
import re

def clean_job_title(job_description="", company_name=""):
    if pd.isna(job_description) or not str(job_description).strip():
        return "Technical Professional"

    desc_str = str(job_description).strip()
    desc_lower = desc_str.lower()
    comp_lower = str(company_name).lower()

    non_tech_titles = [
        "pmc electrical engineer", "pmc mechanical engineer", "pmc process engineer",
        "pmc piping engineer", "pmc civil structural engineer", "pmc instrumentation control engineer","Sales Engineer",
        "estimation design engineer","production engineer", "survey engineer", "data collector","Data Center Mechanical Engineer"
    ]

    for title in non_tech_titles:
        if title in desc_lower:
            return "Technical Professional"

    if "schneider" in comp_lower and "telecom" in desc_lower:
            return "Telecom Security System Field Service Engineer"

    if "enterprise data classification" in desc_lower or "fortra titus" in desc_lower or ("data protection" in desc_lower and "dlp" in desc_lower):
        return "Solutions Engineer"

    if "staff cloud support engineer" in desc_lower:
        return "Staff Cloud Support Engineer"

    if "mllers solut" in comp_lower.lower() and "talend" in desc_lower:
        return "Data Engineer"
        
    if "master works" in comp_lower.lower() and "architectures such as databases and largescale processing systems" in desc_lower:
        return "Data Engineer"


    if "technohandz" in comp_lower.lower():
        return "Data Warehouse Engineer"

    if "salla" in comp_lower.lower() and "medallion architecture" in desc_lower and "senior data engineer" in desc_lower:
        return "Senior Data Engineer"

    if "foodics" in comp_lower.lower():
        return "Data Engineer"

    if "mllers solut" in comp_lower.lower() and "big data engineer" in desc_lower:
        return "Big Data Engineer"

    if "devsinc" in comp_lower and "data migration" in desc_lower:
        return "Data Migration Engineer"

    if "nhc" in comp_lower and ("supervisor" in desc_lower or "data ai" in desc_lower):
        return "Data & AI Supervisor"

    if "rize" in comp_lower and "responsive web applications" in desc_lower:
        return "Web Developer"

    if "asmo" in comp_lower and "data quality guidelines" in desc_lower:
        return "Data Quality"

    if "discovered mena" in comp_lower and "staff data scientist" in desc_lower:
        return "Staff Data Scientist – Business Analytics"

    if "albawani" in comp_lower and "reporting engineer i" in desc_lower:
        return "Reporting Engineer I"

    if "master works" in comp_lower and "linguistic" in desc_lower:
        return "Linguistic Data Analyst"

    if "master works" in comp_lower and "realtime and batch data pipelines" in desc_lower:
        return "Data Engineer"

    if "mllers solut" in comp_lower and "oracle data modeler" in desc_lower:
        return "Oracle Data Modeler"

    if "airbus" in comp_lower and "system integration of a large security system" in desc_lower:
        return "Systems Integration Engineer"

    if "mllers solut" in comp_lower and "google cloud ai specialist" in desc_lower:
        return "Google Cloud AI Specialist"

    if "primegate" in comp_lower and "madinaty superapp" in desc_lower:
        return "Data Analyst"

    if "takamol holding" in comp_lower and "senior data scientist specialist" in desc_lower:
        return "Senior Data Scientist"

    if "mllers solut" in comp_lower and "talend" in desc_lower:
        return "Data Engineer"
        
    if "master works" in comp_lower and "architectures such as databases and largescale processing systems" in desc_lower:
        return "Data Engineer"

    if "tarmeez capital" in comp_lower:
        return "Data Analyst"
    
    if "technohandz" in comp_lower:
        return "Data Warehouse Engineer"

    if "salla" in comp_lower and "medallion architecture" in desc_lower and "senior data engineer" in desc_lower:
        return "Senior Data Engineer"

    if "foodics" in comp_lower:
        return "Data Engineer"

    if "mllers solut" in comp_lower and "big data engineer" in desc_lower:
        return "Big Data Engineer"

    if "salla" in comp_lower and "staff data scientist business analytics" in desc_lower:
        return "Staff Data Scientist"

    if "ge vernova" in comp_lower and "power system engineer" in desc_lower:
        return "Power Systems Engineer"

    if "aramco digital" in comp_lower and "system integration presales engineer" in desc_lower:
        return "Senior System Integration Presales Engineer"

    if "salla" in comp_lower and "design and develop machine learning ml models" in desc_lower:
        return "Data Scientist"

    if "master works" in comp_lower and "semantic layer designer" in desc_lower:
        return "Semantic Layer Designer"

    if "salla" in comp_lower and "recommendation systems pod" in desc_lower:
        return "Data Science Manager"

    if "maaden" in comp_lower and "senior specialist data science and artificial intelligence" in desc_lower:
        return "Senior Specialist Data Science"


    if "bupa arabia" in comp_lower and "designs builds and operationalizes ai and machine learning" in desc_lower:
        return "AI Engineer"

    if "cyberhaven" in comp_lower and "solutions engineer for the meta region" in desc_lower:
        return "Solutions Engineer"

    if "qiddiya" in comp_lower and "senior specialist in business intelligence" in desc_lower:
        return "Senior Specialist Business Intelligence"

    if "salla" in comp_lower and "we are looking for a data scientist to design and develop machine learning" in desc_lower:
        return "Data Scientist"


    if any(keyword in desc_lower for keyword in ["swift transfers", "payment systems", "ipstfers"]):
        return "Payment Systems Engineer"

    if "hiredge solutions" in comp_lower and "genai" in desc_lower:
        return "AI Engineer"

    if "duruper" in comp_lower and ("control systems" in desc_lower or "project engineer" in desc_lower):
        return "Senior Project Engineer – Control Systems"

    if "buro" in comp_lower and ("ai" in desc_lower or "data science" in desc_lower):
        return "AI / Data Science Expert"

    if "denodo" in comp_lower and "as a sales engineer you will play a crucial role" in desc_lower:
        return "Sales Engineer"

    if "asmo" in comp_lower and "supporting the product analyst in driving successful technology" in desc_lower:
        return "Product Analyst"

    if "confidential" in comp_lower and "product sr specialist" in desc_lower:
        return "Product Specialist / Senior Product Specialist"



    if "enterprise architecture" in desc_lower:
        return "Enterprise Architect"

    if "collecting automotive data" in desc_lower or ("automotive market" in desc_lower and "pricing specifications" in desc_lower):
        return "Automotive Data Analyst"

    if "manage and execute system testing" in desc_lower or "user acceptance testing uat" in desc_lower:
        return "QA Engineer"

    if "hands on senior security engineer" in desc_lower or "cloud security or platform engineer" in desc_lower:
        return "Senior Security Engineer"
    
    if "toloka annotators" in desc_lower or "ai annotator" in desc_lower:
        return "AI Data Annotator"

    
    if "performance measurement" in desc_lower or "corporate performance management" in desc_lower:
        return "Performance Management Specialist"
    
    if "data reporting execution" in desc_lower or "emplifi" in desc_lower:
        return "Data Reporting Specialist"

    if "product analytics" in desc_lower:
        return "Product Analyst"

    if "storyteller presentation specialist" in desc_lower or "presentation specialist" in desc_lower:
        return "Presentation Specialist"

    if "lucidya" in desc_lower or "microservice ecosystem" in desc_lower:
        return "Distributed Systems Engineer"

    if "senior specialist reporting" in desc_lower or ("reporting" in desc_lower and "power bi" in desc_lower and "qiddiya" in desc_lower):
        return "Senior Specialist Reporting"

    if "database application security specialist" in desc_lower or ("imperva" in desc_lower and "file integrity monitoring" in desc_lower):
        return "Database Application Security Specialist"
    
    if "operations" in desc_lower and "data associate" in desc_lower:
            return "Operations Data Associate"

    common_roles_list = [
        "senior specialist reporting", "Senior Forward Deploy Engineer", "database application security specialist", "data strategist", "enterprise architect",
        "Specialist Reporting", "technical support engineer", "The Lead Engineer System Integration", "AI Data Collection", "Develop and maintain responsive web applications","Business Analytics",
        "Software Quality Engineer", "Personal Data Protection", "Senior Business Intelligence Specialist","Mining Technology Engineer",
        "developer intern", "system admin engineer", "senior system engineer", "senior data engineer", "AWS Infrastructure Services",
        "staff data engineer", "principal data engineer", "data engineer ii", "data engineer", "Senior Security Engineer", "Shopper Insights Manager",
        "senior data analyst", "business data analyst", "data analyst", "senior data scientist", "data scientist","Operations Engineer",
        "machine learning engineer", "machine learning scientist", "ai engineer", "ai specialist", "analytics engineer",
        "business intelligence analyst", "business intelligence developer", "senior software engineer", "software engineer", "Media Search Analyst",
        "software developer", "full stack developer", "full stack engineer", "frontend developer", "frontend engineer", "Identity Security Engineer",
        "backend developer", "backend engineer", "mobile developer", "application developer", "cloud engineer", 
        "cloud architect", "devops engineer", "platform engineer", "solutions architect", 
        "cybersecurity engineer", "data security engineer", "security engineer", "cybersecurity analyst", "security analyst","Systems Engineer",
        "information security analyst", "soc analyst", "product manager", "project manager", "technical project manager",
        "program manager", "engineering manager", "business analyst", "systems analyst", "systems administrator", "Payment Systems Engineer",
        "integration specialist", "sap consultant", "sap ec consultant", "sap successfactors consultant", "Data Collector", "Software Support Engineer",
        "flight data monitoring analyst", "data platform engineer", "observability engineer", "Business Intelligence Engineer", "Analyze RFPs RFQs", "Data Center Engineering Operations Engineer",
        "qa engineer", "software quality assurance engineer", "sales engineer", "solutions engineer", "Business Intelligence Senior Specialist", "Source Code Management", "CT System Engineer", "Junior Engineer"
    ]

    for role in sorted(set(common_roles_list), key=len, reverse=True):
        if role.lower() in desc_lower:
            return role.title()

    inline_title_match = re.search(r'job\s*title[:\s\-]*([A-Za-z0-9/&,\-\s]{3,45})(?=location|position|about|summary|requirements|$)', desc_str, re.IGNORECASE)
    if inline_title_match:
        t = inline_title_match.group(1).strip()
        t = re.sub(r'\b(location|position|about|summary|requirements|onsite|remote)\b.*$', '', t, flags=re.IGNORECASE).strip()
        if len(t.split()) <= 6:
            return t.title()

    explicit_hiring_patterns = [
        r'(?:we\s+are\s+looking\s+for|is\s+hiring|hiring|seeking|seeks|seek|looking\s+for)\s+(?:an?|the)?\s+(?:talented|experienced|qualified|expert|skilled|versatile)?\s*([A-Za-z0-9/&,\-\s]{3,55})(?=\s+(?:with|to\s+join|to\s+build|to\s+design|for\s+our|as\s+a|who|that|to|in|with|and|on|to\s+strengthen|to\s+support)\b|[.,;:]|$)',
        r'(?:position\s+is\s+for|role\s+is|title\s*:)\s*([A-Za-z0-9/&,\-\s]{3,45})(?=[.,;:\n]|$)'
    ]

    bad_words = {
        "talented", "experienced", "qualified", "expert", "passionate", "resourceful", 
        "dedicated", "central", "responsible", "motivated", "skilled", "proactive", 
        "technically", "highly", "continuously", "most", "brilliant", "minds",
        "hands", "hand", "on"
    }
    
    for pattern in explicit_hiring_patterns:
        match = re.search(pattern, desc_str, re.IGNORECASE)
        if match:
            t = match.group(1).strip()
            words = t.split()
            while words and words[0].lower() in bad_words:
                words.pop(0)
            t = " ".join(words)
            t = re.sub(r'\b(to|who|that|for|in|with|and|on|to\s+join|to\s+strengthen|to\s+support)\b.*$', '', t, flags=re.IGNORECASE).strip()
            if len(t) > 2 and len(t.split()) <= 6 and not any(w in t.lower() for w in ["ai company", "enterprise", "team"]):
                return t.title()

    return "Technical Professional"

def clean_city(location_str):
    if pd.isna(location_str) or not str(location_str).strip():
        return None

    city_mapping = {
        "الرياض": "Riyadh",
        "riyadh": "Riyadh",

        "جدة": "Jeddah",
        "jeddah": "Jeddah",

        "المدينة المنورة": "Medina",
        "medina": "Medina",
        "madinah": "Medina",

        "مكة المكرمة": "Mecca",
        "مكة": "Mecca",
        "makkah": "Mecca",
        "mecca": "Mecca",

        "الدمام": "Dammam",
        "dammam": "Dammam",

        "الخبر": "Al Khobar",
        "khobar": "Al Khobar",
        "al khobar": "Al Khobar",

        "الجبيل": "Al Jubail",
        "jubail": "Al Jubail",
        "al jubail": "Al Jubail",

        "ينبع": "Yanbu",
        "yanbu": "Yanbu",

        "القصيم": "Al Qasim",
        "qassim": "Al Qasim",
        "al qasim": "Al Qasim",

        "القريات": "Al Qurayyat",
        "qurayat": "Al Qurayyat",
        "al qurayat": "Al Qurayyat",

        "الظهران": "Dhahran",
        "dhahran": "Dhahran",
    }

    loc_lower = str(location_str).strip().lower()

    for key, val in city_mapping.items():
        if key in loc_lower:
            return val

    # Known regions — don't store them as cities
    if "eastern province" in loc_lower or "eastern" == loc_lower:
        return None

    # If the location is only Saudi Arabia / KSA
    if loc_lower in {
        "saudi arabia",
        "ksa",
        "kingdom of saudi arabia"
    }:
        return None

    cleaned = re.sub(r'[^a-zA-Z\s]', '', loc_lower).strip()

    return cleaned.title() if cleaned else None

def clean_employment_type(emp_type, desc_str=""):

    combined_text = f"{str(emp_type)} {str(desc_str)}".lower()
   
    if "part-time" in combined_text or "part time" in combined_text or "parttime" in combined_text or "جزئي" in combined_text:
        return "Part-time"
    elif "contract" in combined_text or "عقد" in combined_text:
        return "Contract"
    elif "full-time" in combined_text or "full time" in combined_text or "fulltime" in combined_text or "دائم" in combined_text or "كامل" in combined_text:
        return "Full-time"
        
    return None

import re

def extract_education(desc_str):
    if pd.isna(desc_str) or not str(desc_str).strip():
        return None
        
    desc_lower = str(desc_str).lower()
    
    bachelor_patterns = [
        r"\bbs\b", r"\bbs in\b", "bachelor", "bachelors", "bachelor's", 
        "bsc", "b.sc", "b.tech", "b.e", "undergraduate", "b.eng"
    ]
    for pattern in bachelor_patterns:
        if pattern.startswith(r"\b") or pattern.endswith(r"\b"):
            if re.search(pattern, desc_lower):
                return "Bachelor"
        else:
            if pattern in desc_lower:
                return "Bachelor"
                
    master_patterns = [
        r"\bms\b", r"\bmsc\b", r"\bm.sc\b", r"\bmba\b", 
        "master's", "masters", "master degree", "master degree", 
        "master of science", "master of arts", "master of engineering"
    ]
    for pattern in master_patterns:
        if pattern.startswith(r"\b") or pattern.endswith(r"\b"):
            if re.search(pattern, desc_lower):
                return "Master"
        else:
            if pattern in desc_lower:
                return "Master"
                
    phd_patterns = [r"\bphd\b", r"\bph.d\b", "doctorate", "doctoral"]
    for pattern in phd_patterns:
        if pattern.startswith(r"\b") or pattern.endswith(r"\b"):
            if re.search(pattern, desc_lower):
                return "PhD"
        else:
            if pattern in desc_lower:
                return "PhD"
                
    school_terms = ["high school", "diploma", "vocational"]
    if any(term in desc_lower for term in school_terms):
        return "High School"
        
    return None
def clean_description(desc):
    if pd.isna(desc):
        return ""
    clean_text = re.sub(r'<[^<]+?>', '', str(desc))
    clean_text = re.sub(r'[\*\•\❖\✔]\s*', '', clean_text)
    headers_pattern = r'\b(?:About\s+[A-Za-z0-9\s&,.-]{1,30}|Job\s*Description|Job\s*Summary|Job\s*Purpose|Overview)[:\s\-]*'
    clean_text = re.sub(headers_pattern, '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def format_date(date_val):
    if pd.isna(date_val):
        return None
    try:
        parsed_date = pd.to_datetime(date_val)
        current_date = pd.to_datetime("2026-09-08") 
        
        if parsed_date > current_date or parsed_date.year < 2020:
            return None
            
        return parsed_date.strftime("%Y-%m-%d")
    except Exception:
        return None
    
def process_linkedin_excel(excel_path, output_json_path):
    try:
        xls = pd.ExcelFile(excel_path)
        sheet_name = xls.sheet_names[0]
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    standardized_jobs = []
    print(f"Processing {len(df)} rows from LinkedIn Excel...")

    for index, row in df.iterrows():
        company_raw = row.get('CompanyName', '') or row.get('company_name', '')
        company_name = clean_company_name(company_raw)
        
        raw_desc_content = row.get('JobDescription', '') or row.get('job_description', '')

        job_description = clean_description(raw_desc_content)
        
        job_title = clean_job_title(raw_desc_content,company_name)
        if job_title == "Technical Professional":
            continue

        if job_title == "Project Manager":
            if company_name == "AtkinsR":
                continue


        city = clean_city(row.get('city') or row.get('Location'))
        country = "Saudi Arabia"
        posted_date = format_date(row.get('posted_date') or row.get('PostedAt'))
        employment_type = clean_employment_type(row.get('employment_type') or row.get('EmploymentType'), raw_desc_content)        
        skills = extract_tech_skills(job_description)
        education = extract_education(raw_desc_content)
        
        job_url = None
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


    print(f"Total jobs before removing duplicates: {len(standardized_jobs)}")
    df_temp = pd.DataFrame(standardized_jobs)
    df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
    df_temp = df_temp.where(pd.notnull(df_temp), None)

    print("Null values count per column:\n", df_temp.isnull().sum())
    standardized_jobs = df_temp.to_dict(orient='records')

    print(f"Total unique jobs remaining after removing duplicates: {len(standardized_jobs)}")
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(standardized_jobs, f, ensure_ascii=False, indent=4)

    with open(output_json_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    file_content = re.sub(
        r'("skills":\s*)\[\s*([^\]]+?)\s*\]', 
        lambda m: m.group(1) + '[' + ', '.join([s.strip() for s in m.group(2).replace('\n', '').split(',') if s.strip()]) + ']', 
        file_content, 
        flags=re.DOTALL
    )

    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    print(f"Successfully processed {len(standardized_jobs)} LinkedIn jobs and saved to {output_json_path}")

if __name__ == "__main__":
    EXCEL_FILE = "raw/linkedin-saudi-jobs.xlsx" 
    OUTPUT_FILE = "data/raw/standardized_linkedin_jobs.json"
    
    process_linkedin_excel(EXCEL_FILE, OUTPUT_FILE)