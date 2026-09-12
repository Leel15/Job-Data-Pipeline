import os
import pandas as pd
import snowflake.connector
import json

from dotenv import load_dotenv
load_dotenv()

from cleaning import (
    clean_html_text, extract_title_guess, extract_skills,
    normalize_skills_list, extract_experience_years,
    extract_salary_from_text, clean_jsearch_location,
    clean_employment_type, deduplicate_by_content,
    translate_arabic_terms, translate_to_english,
    merge_and_save_processed,
)


RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# الأعمدة الموحّدة المستهدفة لكل المصادر (يسهّل الدمج لاحقًا بمرحلة normalize)
UNIFIED_COLUMNS = [
    "title", "company", "location", "posted_date", "salary",
    "skills", "experience_required", "description", "employment_type",
    "url", "source", "repost_count",
]

def load_csv_to_snowflake(csv_path: str, table_name: str):
    """تقرأ ملف الـ CSV المحفوظ محلياً وترفعه إلى Snowflake."""
    if not os.path.exists(csv_path):
        print(f"⚠️ ملف الـ CSV غير موجود: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    conn = None
    cursor = None
    try:
        account_val = os.getenv("SNOWFLAKE_ACCOUNT") or os.getenv("SNOWFLAFE_ACCOUNT")
        
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=account_val,
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        cursor = conn.cursor()

        print(f"☁️ جاري إرسال {len(df)} سجل من ملف الـ CSV إلى جدول {table_name} في Snowflake...")
        insert_query = f"INSERT INTO {table_name} (RAW_PAYLOAD) SELECT PARSE_JSON(%s)"

        records = df.to_dict(orient="records")
        for record in records:
            # تنظيف قيم الـ NaN لكي لا تسبب مشاكل في تحويل الـ JSON
            clean_record = {k: (v if pd.notna(v) else None) for k, v in record.items()}
            json_str = json.dumps(clean_record, ensure_ascii=False)
            cursor.execute(insert_query, (json_str,))

        conn.commit()
        print(f"✅ تم رفع بيانات الـ CSV إلى جدول {table_name} في Snowflake بنجاح!")

    except Exception as e:
        print(f"❌ خطأ أثناء الرفع لـ Snowflake ({table_name}): {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def process_jooble() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "jooble_tech_jobs.json"))

    df["snippet"] = df["snippet"].apply(clean_html_text)
    df["skills"] = df["snippet"].apply(extract_skills)
    df["experience_required"] = df["snippet"].apply(extract_experience_years)
    df["salary"] = df.apply(
        lambda row: row["salary"] if row["salary"] else extract_salary_from_text(row["snippet"]),
        axis=1
    )
    df["employment_type"] = "Not Specified"  # jooble لا يوفر هذا الحقل

    df = df.rename(columns={"date": "posted_date", "snippet": "description"})

    before = len(df)
    # ⚠️ مهم: بعكس tapneo، snippet بـ jooble مقتطف قصير يتغيّر شكله بكل زحف
    # (نقطة اقتطاع مختلفة كل مرة)، فمطابقته حرفيًا تفشل باكتشاف التكرار الحقيقي.
    # المعيار الموثوق هنا: شركة + موقع + العنوان الحقيقي (title مستقر وثابت من Jooble)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "title"])
    print(f"🧹 jooble: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "jooble_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "title"])
    csv_output_path = os.path.join(PROCESSED_DIR, "csv", "jooble_tech_jobs_cleaned.csv")
    load_csv_to_snowflake(csv_output_path, "JOB_MARKET_DB.PROCESSED_SCHEMA.PROCESSED_JOOBLE_JOBS")
    print()
    return df


def process_jsearch() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "jsearch_tech_jobs.json"))

    df["location"] = df["location"].apply(clean_jsearch_location)
    df["employment_type"] = df["employment_type"].apply(clean_employment_type)

    df["snippet"] = df["snippet"].apply(clean_html_text)
    df["skills"] = df["snippet"].apply(extract_skills)
    df["experience_required"] = df["snippet"].apply(extract_experience_years)

    df = df.rename(columns={"date": "posted_date", "snippet": "description"})

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "title"])
    print(f"🧹 jsearch: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "jsearch_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "title"])
    csv_jsearch_path = os.path.join(PROCESSED_DIR, "csv", "jsearch_tech_jobs_cleaned.csv")
    load_csv_to_snowflake(csv_jsearch_path, "JOB_MARKET_DB.PROCESSED_SCHEMA.PROCESSED_JSEARCH_JOBS")
    print()
    return df


def process_freehire() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "freehire_tech_jobs.json"))

    df["job_description"] = df["job_description"].apply(clean_html_text)
    df["skills"] = df["skills"].apply(normalize_skills_list)
    df["experience_required"] = df["job_description"].apply(extract_experience_years)
    df["salary"] = df["job_description"].apply(extract_salary_from_text)
    df["employment_type"] = "Not Specified"

    df = df.rename(columns={
        "job_title": "title",
        "company_name": "company",
        "job_description": "description",
        "source_url": "url",
    })
    df["source"] = "freehire"

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "title"])
    print(f"🧹 freehire: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "freehire_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "title"])
    csv_freehire_path = os.path.join(PROCESSED_DIR, "csv", "freehire_tech_jobs_cleaned.csv")
    load_csv_to_snowflake(csv_freehire_path, "JOB_MARKET_DB.PROCESSED_SCHEMA.PROCESSED_FREEHIRE_JOBS")
    print()
    return df


def process_tapneo() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "tapneo_tech_jobs.json"))

    df["title"] = df["JobDescription"].apply(extract_title_guess)
    df["skills"] = df["JobDescription"].apply(extract_skills)
    df["experience_required"] = df["JobDescription"].apply(extract_experience_years)
    df["employment_type"] = df.get("EmploymentType", "Not Specified")

    df = df.rename(columns={
        "CompanyName": "company",
        "Location": "location",
        "PostedAt": "posted_date",
        "JobDescription": "description"
    })

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "description"])
    print(f"🧹 tapneo: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    skills_found = (df["skills"] != "Not Specified").sum()
    print(f"🛠️ tapneo: عدد الوظائف بمهارات مستخرجة: {skills_found} من {len(df)}")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "tapneo_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "description"])
    
    csv_tapneo_path = os.path.join(PROCESSED_DIR, "csv", "tapneo_tech_jobs_cleaned.csv")
    load_csv_to_snowflake(csv_tapneo_path, "JOB_MARKET_DB.PROCESSED_SCHEMA.PROCESSED_TAPNEO_JOBS")
    print()
    return df


def process_tanqeeb() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "tanqeeb_tech_jobs.json"))

    print(f"📥 tanqeeb: إجمالي السجلات الخام: {len(df)}")
    print("🌐 جاري ترجمة العناوين والأوصاف العربية...")

    # إعادة التسمية في البداية لتتطابق الأعمدة مع باقي الكود
    df = df.rename(columns={
        "job_title": "title",
        "job_description": "description",
        "company_name": "company",
        "job_url": "url"
    })

    df["title"] = df["title"].apply(translate_to_english)
    df["description"] = df["description"].apply(translate_to_english)
    
    if "category" in df.columns:
        df["category"] = df["category"].apply(translate_arabic_terms)
        
    df["location"] = df["location"].apply(translate_arabic_terms)
    df["employment_type"] = df["employment_type"].apply(clean_employment_type)

    df["skills"] = df["description"].apply(extract_skills)

    df["experience_required"] = df.apply(
        lambda row: extract_experience_years(row["description"])
        if row.get("experience", "Not Specified") == "Not Specified" else row["experience"],
        axis=1
    )
    df["salary"] = df.apply(
        lambda row: extract_salary_from_text(row["description"])
        if row.get("salary", "Not Specified") == "Not Specified" else row["salary"],
        axis=1
    )

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "description"])
    print(f"🧹 tanqeeb: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "tanqeeb_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "description"])
    
    csv_tanqeeb_path = os.path.join(PROCESSED_DIR, "csv", "tanqeeb_tech_jobs_cleaned.csv")
    load_csv_to_snowflake(csv_tanqeeb_path, "JOB_MARKET_DB.PROCESSED_SCHEMA.PROCESSED_TANQEEB_JOBS")
    print()
    return df

if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("=" * 50)
    print("🔄 بدء تنظيف جميع المصادر")
    print("=" * 50 + "\n")

    jooble_df = process_jooble()
    jsearch_df = process_jsearch()
    freehire_df = process_freehire()
    tapneo_df = process_tapneo()
    tanqeeb_df = process_tanqeeb()

    print("=" * 50)
    print("✅ اكتمل تنظيف جميع المصادر")
    print(f"📊 jooble: {len(jooble_df)} | jsearch: {len(jsearch_df)} | "
          f"freehire: {len(freehire_df)} | tapneo: {len(tapneo_df)} | "
          f"tanqeeb: {len(tanqeeb_df)}")
    print("=" * 50)