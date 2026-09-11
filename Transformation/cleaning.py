import re
import os
import json
import time
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
        return "غير محدد"

    translated = translate_arabic_terms(raw_location)
    translated = re.sub(r"\s{2,}", " ", translated).strip()
    translated = translated.replace("•", "-")
    translated = re.sub(r"\s*-\s*", " - ", translated)
    return translated


def clean_employment_type(raw_type) -> str:
    """يترجم نوع الدوام من العربية إن وُجد، ويوحّد صيغة enum-style مثل FULL_TIME."""
    if not raw_type or not isinstance(raw_type, str) or raw_type == "غير محدد":
        return "غير محدد"

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


def translate_to_english(text: str, chunk_size: int = 4500) -> str:
    """
    يترجم نصًا عربيًا كاملاً للإنجليزية عبر GoogleTranslator (مكتبة deep-translator).
    - لو النص لا يحتوي عربية أصلاً، يُرجَع كما هو بدون استدعاء API (توفير وقت وطلبات).
    - النصوص الطويلة تُقسَّم لأجزاء (chunk_size) لتفادي حدود حجم الطلب بمزود الترجمة.
    - عند فشل الترجمة (لا اتصال، لا مكتبة مثبتة)، يُرجَع النص الأصلي كما هو
      بدل رفع استثناء يوقف كامل خط الأنابيب.

    يتطلب: pip install deep-translator
    """
    if not text or not contains_arabic(text):
        return text or ""

    if not _TRANSLATOR_AVAILABLE:
        print("⚠️ مكتبة deep-translator غير مثبتة — النص سيبقى بلغته الأصلية. "
              "ثبّتها عبر: pip install deep-translator")
        return text

    translator = GoogleTranslator(source="ar", target="en")

    try:
        if len(text) <= chunk_size:
            return translator.translate(text)

        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        translated_chunks = []
        for chunk in chunks:
            translated_chunks.append(translator.translate(chunk))
            time.sleep(0.3)

        return " ".join(translated_chunks)

    except Exception as e:
        print(f"⚠️ فشلت الترجمة لجزء من النص ({e}) — سيبقى بلغته الأصلية")
        return text


# ============ استخراج المهارات (لكل المصادر) ============

def extract_skills(text: str) -> str:
    """يستخرج المهارات من أي نص وصفي عبر مطابقة كلمات مفتاحية بحدود كلمة."""
    if not text:
        return "غير محدد"

    text_lower = text.lower()
    found_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.strip()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found_skills.append(skill.strip())

    found_skills = list(dict.fromkeys(found_skills))
    return ", ".join(found_skills) if found_skills else "غير محدد"


def normalize_skills_list(skills) -> str:
    """
    يوحّد عمود skills بغض النظر عن شكله الأصلي:
    - لو list (مثل freehire) → يحوّلها لنص مفصول بفاصلة
    - لو نص جاهز (jooble/jsearch/tapneo بعد extract_skills) → يُرجع كما هو
    """
    if isinstance(skills, list):
        return ", ".join(skills) if skills else "غير محدد"
    if isinstance(skills, str) and skills.strip():
        return skills
    return "غير محدد"


# ============ استخراج الخبرة والراتب (نصوص حرة) ============

def extract_title_guess(description: str) -> str:
    """يخمّن عنوان الوظيفة من نص الوصف (لمصادر بدون عنوان صريح مثل tapneo)."""
    if not description:
        return "غير محدد"

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
        return "غير محدد"

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

    return "غير محدد"


def extract_salary_from_text(text: str) -> str:
    """يستخرج راتبًا مذكورًا صراحة داخل النص، مع تجاهل المزايا (stipend، budget...)."""
    if not text:
        return "غير محدد"

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

    return "غير محدد"


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
    يدمج نتيجة التنظيف الجديدة مع ملف processed السابق (upsert)، بحيث:
    - وظيفة ظهرت سابقًا تحتفظ بـ first_seen الأصلي، ويُحدَّث last_seen فقط
    - وظيفة جديدة تمامًا تُضاف بـ first_seen = الآن
    المعرّف المستخدم هو نفس معيار التكرار (key_cols)، وليس url،
    لأنه يمثّل هوية الوظيفة الفعلية بثبات عبر إعادة النشر.
    """
    now = datetime.now(timezone.utc).isoformat()

    existing = load_existing_processed(json_path, key_cols)
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

    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2, default=str)

    print(f"💾 تم حفظ processed (تراكمي) في: {json_path}")