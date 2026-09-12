import re
import os
import json
import time
import pandas as pd

from datetime import datetime, timezone
from bs4 import BeautifulSoup

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_AVAILABLE = True
except ImportError:
    _TRANSLATOR_AVAILABLE = False


STOP_PHRASES = [
    "we are", "we're", "you will", "your role", "the ideal candidate",
    "job description", "about us", "responsibilities", "requirements",
    "qualifications", "overview", "our mission", "as a", "join our",
    "we offer", "key responsibilities", "job summary", "company description"
]

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "php",
    "ruby", "go", "golang", "swift", "kotlin", "scala", "r ", "sql",
    "react", "angular", "vue", "node.js", "nodejs", "django", "flask",
    "spring", "spring boot", ".net", "laravel", "express.js",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn", "nlp", "computer vision",
    "power bi", "tableau", "etl", "airflow", "spark", "hadoop",
    "mysql", "postgresql", "mongodb", "oracle", "redis", "elasticsearch",
    "sql server", "cassandra", "dynamodb",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "ci/cd", "linux", "devops",
    "penetration testing", "cybersecurity", "siem", "firewall",
    "vulnerability assessment", "ai/ml", "artificial intelligence",
    "agentic", "llm", "genai", "enterprise security",
    "git", "github", "jira", "agile", "scrum", "rest api", "graphql",
    "microservices", "html", "css", "kafka", "dbt", "snowflake",
    "bigquery", "hive", "hbase", "nifi", "pyspark",
]

# قاموس ترجمة أساسي للمدن والمصطلحات العربية الشائعة بمصادر مثل jsearch وtanqeeb
AR_EN_DICTIONARY = {
    "السعودية": "Saudi Arabia",
    "الرياض": "Riyadh",
    "جدة": "Jeddah",
    "الدمام": "Dammam",
    "الخبر": "Khobar",
    "مكة": "Mecca",
    "المدينة": "Medina",
    "الظهران": "Dhahran",
    "الجبيل": "Jubail",
    "الطائف": "Taif",
    "أبها": "Abha",
    "دوام كامل": "Full-time",
    "دوام جزئي": "Part-time",
    "عن بعد": "Remote",
    "عن بُعد": "Remote",
    "عقد": "Contract",
    "تدريب": "Internship",
    "عبر": "via",
}


# ============ تنظيف نصي عام (لكل المصادر) ============

def clean_html_text(raw_text: str) -> str:
    """ينظف أي نص من وسوم HTML (jooble, freehire, tapneo عند الحاجة)."""
    if not raw_text:
        return ""
    soup = BeautifulSoup(raw_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def translate_arabic_terms(text: str) -> str:
    """
    ترجمة قائمة على قاموس للمصطلحات العربية الشائعة (مدن، نوع الدوام).
    مناسبة لحقول قصيرة ومحددة (location, employment_type)، وليست
    ترجمة عامة لنصوص حرة طويلة (لهذا نستخدم translate_to_english أدناه لتلك الحالة).
    """
    if not text:
        return text

    result = text
    for ar_term, en_term in AR_EN_DICTIONARY.items():
        result = result.replace(ar_term, en_term)

    return result.strip()


def clean_jsearch_location(raw_location) -> str:
    """
    ينظف ويترجم حقل location الخاص بـ jsearch من الشكل:
    'الرياض     •  عبر LinkedIn' → 'Riyadh - via LinkedIn'
    """
    if not raw_location or not isinstance(raw_location, str):
        return "Not Specified"

    translated = translate_arabic_terms(raw_location)
    translated = re.sub(r"\s{2,}", " ", translated).strip()
    translated = translated.replace("•", "-")
    translated = re.sub(r"\s*-\s*", " - ", translated)
    return translated


def clean_employment_type(raw_type) -> str:
    """يترجم نوع الدوام من العربية إن وُجد، ويوحّد صيغة enum-style مثل FULL_TIME."""
    if not raw_type or not isinstance(raw_type, str) or raw_type == "Not Specified":
        return "Not Specified"

    enum_map = {
        "FULL_TIME": "Full-time",
        "PART_TIME": "Part-time",
        "CONTRACTOR": "Contract",
        "INTERN": "Internship",
        "TEMPORARY": "Temporary",
    }
    if raw_type.upper() in enum_map:
        return enum_map[raw_type.upper()]

    return translate_arabic_terms(raw_type)


# ============ ترجمة نصوص كاملة (محتوى مختلط عربي/إنجليزي مثل tanqeeb) ============

ARABIC_CHAR_PATTERN = re.compile(r"[\u0600-\u06FF]")


def contains_arabic(text: str) -> bool:
    """يتحقق هل النص يحتوي على حروف عربية فعلية."""
    if not text:
        return False
    return bool(ARABIC_CHAR_PATTERN.search(text))


def translate_to_english(text: str, chunk_size: int = 1500) -> str:
    """
    دالة الترجمة المحسّنة: تفحص وجود العربية، تقسم النص لأجزاء آمنة،
    وتجري محاولات إعادة محاولة (Retries) لضمان دقة الترجمة بدون توقف.
    """
    if not text or pd.isna(text):
        return text or ""
    
    text_str = str(text)
    
    max_total_retries = 3
    for global_attempt in range(max_total_retries):
        if not re.search(r'[\u0600-\u06FF]', text_str):
            break 
            
        try:
            translator = GoogleTranslator(source='ar', target='en')
            chunks = [text_str[i:i+chunk_size] for i in range(0, len(text_str), chunk_size)]
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

# ============ استخراج المهارات (لكل المصادر) ============

def extract_skills(text: str) -> str:
    """يستخرج المهارات من أي نص وصفي عبر مطابقة كلمات مفتاحية بحدود كلمة."""
    if not text:
        return "Not Specified"

    text_lower = text.lower()
    found_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.strip()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found_skills.append(skill.strip())

    found_skills = list(dict.fromkeys(found_skills))
    return ", ".join(found_skills) if found_skills else "Not Specified"


def normalize_skills_list(skills) -> str:
    """
    يوحّد عمود skills بغض النظر عن شكله الأصلي:
    - لو list (مثل freehire) → يحوّلها لنص مفصول بفاصلة
    - لو نص جاهز (jooble/jsearch/tapneo بعد extract_skills) → يُرجع كما هو
    """
    if isinstance(skills, list):
        return ", ".join(skills) if skills else "Not Specified"
    if isinstance(skills, str) and skills.strip():
        return skills
    return "Not Specified"


# ============ استخراج الخبرة والراتب (نصوص حرة) ============

def extract_title_guess(description: str) -> str:
    """يخمّن عنوان الوظيفة من نص الوصف (لمصادر بدون عنوان صريح مثل tapneo)."""
    if not description:
        return "Not Specified"

    text = description.strip()
    marker_match = re.search(r"job description", text, flags=re.IGNORECASE)
    if marker_match:
        text = text[marker_match.end():].strip()

    segments = re.split(r"\s{2,}", text)
    title_parts = []
    for seg in segments:
        seg_lower = seg.lower().strip()
        if any(seg_lower.startswith(stop) for stop in STOP_PHRASES):
            break
        if seg.strip():
            title_parts.append(seg.strip())
        if len(title_parts) >= 2:
            break

    title = " - ".join(title_parts) if title_parts else text[:60]
    return title[:100].strip()


def extract_experience_years(text: str) -> str:
    """يستخرج سنوات الخبرة المطلوبة من أي نص وصفي."""
    if not text:
        return "Not Specified"

    text_lower = text.lower()
    patterns = [
        r"(\d+)\s*\+\s*years?",
        r"(\d+)\s*-\s*(\d+)\s*years?",
        r"minimum\s*(?:of\s*)?(\d+)\s*years?",
        r"at least\s*(\d+)\s*years?",
        r"(\d+)\s*years?\s*(?:of\s*)?experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(0).strip()

    return "Not Specified"


def extract_salary_from_text(text: str) -> str:
    """يستخرج راتبًا مذكورًا صراحة داخل النص، مع تجاهل المزايا (stipend، budget...)."""
    if not text:
        return "Not Specified"

    exclude_context = ["stipend", "budget", "credit", "bonus of", "per week for lunch"]
    patterns = [
        r"(?:sar|riyal|ريال)\s*[\d,]+(?:\s*-\s*[\d,]+)?",
        r"\$\s*[\d,]+(?:\s*-\s*\$?\s*[\d,]+)?(?:k)?",
        r"salary\s*(?:range)?\s*:?\s*[\d,]+(?:\s*-\s*[\d,]+)?",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            context_window = text[max(0, match.start() - 30):match.start()].lower()
            if not any(excl in context_window for excl in exclude_context):
                return match.group(0).strip()

    return "Not Specified"


# ============ إزالة التكرار الحقيقي بالمحتوى ============

def deduplicate_by_content(df, subset_cols: list, date_col: str = "posted_date"):
    """
    دالة تكرار عامة لكل المصادر: تعتبر (شركة + موقع + وصف/عنوان مطابق تمامًا)
    تكرارًا حقيقيًا فقط، وتحتفظ بأحدث نسخة (أو أعلى repost_count).

    مهم: وظيفة بنفس الوصف لكن بمدينة مختلفة = وظيفة منفصلة (subset يشمل location).
    وظيفة بنفس الوصف بنفس المدينة لكن بتاريخ مختلف = إعادة نشر حقيقية (تُدمج، يُحسب تكرارها).
    """
    df = df.copy()
    df["repost_count"] = df.groupby(subset_cols)[subset_cols[-1]].transform("count")
    df = df.sort_values(date_col, na_position="last").drop_duplicates(
        subset=subset_cols, keep="last"
    ).reset_index(drop=True)
    return df


# ============ حفظ تراكمي (upsert) لمرحلة processed — تتبّع تاريخي ============

def _build_record_key(record: dict, key_cols: list) -> str:
    """يبني معرّفًا فريدًا مركّبًا من نفس أعمدة معيار التكرار (وليس url،
    لأن الرابط يتغيّر بكل إعادة نشر، بعكس هوية الوظيفة الفعلية)."""
    return "||".join(str(record.get(col, "")) for col in key_cols)


def load_existing_processed(json_path: str, key_cols: list) -> dict:
    """يقرأ ملف processed السابق ويفهرسه بنفس مفتاح التكرار المستخدم بالتنظيف."""
    if not os.path.exists(json_path):
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing_list = json.load(f)
        return {_build_record_key(rec, key_cols): rec for rec in existing_list}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ تعذّرت قراءة processed السابق ({e})، سيتم البدء بقائمة فاضية")
        return {}


def merge_and_save_processed(new_df, json_path: str, key_cols: list):
    """
    يدمج نتيجة التنظيف الجديدة مع ملف processed السابق (upsert)،
    ويحفظ نسخة JSON (مع دعم default=str لتفادي أخطاء التواريخ) ونسخة CSV في مجلد مستقل.
    """
    now = datetime.now(timezone.utc).isoformat()

    # تحديد مسارات المجلدات المستقلة (json و csv)
    base_dir = os.path.dirname(json_path)
    json_dir = os.path.join(base_dir, "json")
    csv_dir = os.path.join(base_dir, "csv")
    
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    
    filename = os.path.basename(json_path)
    actual_json_path = os.path.join(json_dir, filename)
    
    csv_filename = filename.rsplit(".", 1)[0] + ".csv"
    actual_csv_path = os.path.join(csv_dir, csv_filename)

    existing = load_existing_processed(actual_json_path, key_cols)
    print(f"📂 عدد السجلات الموجودة مسبقًا بـ processed: {len(existing)}")

    added_count = 0
    updated_count = 0

    for record in new_df.to_dict(orient="records"):
        key = _build_record_key(record, key_cols)

        if key in existing:
            record["first_seen"] = existing[key].get("first_seen", now)
            record["last_seen"] = now
            updated_count += 1
        else:
            record["first_seen"] = now
            record["last_seen"] = now
            added_count += 1

        existing[key] = record

    print(f"➕ وظائف جديدة (بعد التنظيف): {added_count}")
    print(f"🔄 وظائف محدَّثة (موجودة سابقًا): {updated_count}")
    print(f"📊 إجمالي السجلات بعد الدمج: {len(existing)}")

    final_list = list(existing.values())
    final_df = pd.DataFrame(final_list)

    # 1. حفظ ملف الـ JSON مع default=str لحل أي مشكلة تواريخ تلقائياً
    with open(actual_json_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 تم حفظ JSON في: {actual_json_path}")

    # 2. حفظ ملف الـ CSV في مجلد الـ csv الخاص به
    final_df.to_csv(actual_csv_path, index=False, encoding="utf-8-sig")
    print(f"💾 تم حفظ CSV في: {actual_csv_path}")