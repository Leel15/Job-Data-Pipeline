import os
import pandas as pd
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


def process_jooble() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "jooble_tech_jobs.json"))

    df["snippet"] = df["snippet"].apply(clean_html_text)
    df["skills"] = df["snippet"].apply(extract_skills)
    df["experience_required"] = df["snippet"].apply(extract_experience_years)
    df["salary"] = df.apply(
        lambda row: row["salary"] if row["salary"] else extract_salary_from_text(row["snippet"]),
        axis=1
    )
    df["employment_type"] = "غير محدد"  # jooble لا يوفر هذا الحقل

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
    print()
    return df


def process_freehire() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "freehire_tech_jobs.json"))

    df["job_description"] = df["job_description"].apply(clean_html_text)
    df["skills"] = df["skills"].apply(normalize_skills_list)
    df["experience_required"] = df["job_description"].apply(extract_experience_years)
    df["salary"] = df["job_description"].apply(extract_salary_from_text)
    df["employment_type"] = "غير محدد"

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
    print()
    return df


def process_tapneo() -> pd.DataFrame:
    df = pd.read_json(os.path.join(RAW_DIR, "tapneo_tech_jobs.json"))

    df["title"] = df["full_description"].apply(extract_title_guess)
    df["skills"] = df["full_description"].apply(extract_skills)
    df["experience_required"] = df["full_description"].apply(extract_experience_years)
    df["employment_type"] = df.get("employment_type", "غير محدد")

    df = df.rename(columns={"date": "posted_date", "full_description": "description"})

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "description"])
    print(f"🧹 tapneo: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    skills_found = (df["skills"] != "غير محدد").sum()
    print(f"🛠️ tapneo: عدد الوظائف بمهارات مستخرجة: {skills_found} من {len(df)}")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "tapneo_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "description"])
    print()
    return df


def process_tanqeeb() -> pd.DataFrame:
    """
    يعالج بيانات tanqeeb: ترجمة كاملة (title + description + category)
    من العربية للإنجليزية عبر translate_to_english (لا تُترجم النصوص
    الإنجليزية أصلاً)، ثم استخراج مهارات وخبرة من النص بعد الترجمة.
    """
    df = pd.read_json(os.path.join(RAW_DIR, "tanqeeb_tech_jobs.json"))

    print(f"📥 tanqeeb: إجمالي السجلات الخام: {len(df)}")
    print("🌐 جاري ترجمة العناوين والأوصاف العربية... (قد يستغرق وقتًا حسب عدد السجلات)")

    df["title"] = df["job_title"].apply(translate_to_english)
    df["description"] = df["job_description"].apply(translate_to_english)
    df["category"] = df["category"].apply(translate_arabic_terms)
    df["location"] = df["location"].apply(translate_arabic_terms)
    df["employment_type"] = df["employment_type"].apply(clean_employment_type)

    df["skills"] = df["description"].apply(extract_skills)

    df["experience_required"] = df.apply(
        lambda row: extract_experience_years(row["description"])
        if row.get("experience", "غير محدد") == "غير محدد" else row["experience"],
        axis=1
    )
    df["salary"] = df.apply(
        lambda row: extract_salary_from_text(row["description"])
        if row.get("salary", "غير محدد") == "غير محدد" else row["salary"],
        axis=1
    )

    df = df.rename(columns={"company_name": "company", "job_url": "url"})

    before = len(df)
    df = deduplicate_by_content(df, subset_cols=["company", "location", "description"])
    print(f"🧹 tanqeeb: بعد إزالة التكرار: {len(df)} (أُزيل {before - len(df)})")

    skills_found = (df["skills"] != "غير محدد").sum()
    print(f"🛠️ tanqeeb: عدد الوظائف بمهارات مستخرجة: {skills_found} من {len(df)}")

    df = df[[c for c in UNIFIED_COLUMNS if c in df.columns]]

    output_path = os.path.join(PROCESSED_DIR, "tanqeeb_tech_jobs_cleaned.json")
    merge_and_save_processed(df, output_path, key_cols=["company", "location", "description"])
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