import os
import pandas as pd


def get_tapneo_jobs(csv_path: str) -> pd.DataFrame:
    """
    يقرأ ملف LinkedIn الخام ويعيد تسميته/هيكلته لتوحيد الأعمدة فقط،
    بدون أي تنظيف عميق (المهارات، الخبرة، التكرار تُعالج لاحقًا في Transformation/cleaning.py).
    """
    df_raw = pd.read_csv(csv_path)
    print(f"📥 إجمالي السجلات الخام في الملف: {len(df_raw)}")

    duplicate_ids = df_raw["JOB_ID"].duplicated().sum()
    print(f"🔍 عدد JOB_ID المكررة بالملف الخام: {duplicate_ids}")

    structured = pd.DataFrame({
        "job_id": df_raw["JOB_ID"],
        "title": None,  # يُستخرج لاحقًا من full_description عبر extract_title_guess
        "company": df_raw["CompanyName"],
        "location": df_raw["Location"],
        "date": df_raw["PostedAt"],
        "salary": None,
        "snippet": df_raw["JobDescription"].str[:300],
        "url": None,
        "source": "tapneo",
        "job_function": df_raw["JobFunction"],
        "industry": df_raw["Industries"],
        "employment_type": df_raw["EmploymentType"],
        "skills": None,  # يُستخرج لاحقًا عبر extract_skills
        "full_description": df_raw["JobDescription"],
    })

    print(f"📊 إجمالي السجلات (بدون تنظيف عميق): {len(structured)}")
    return structured


if __name__ == "__main__":
    input_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw", "linkedin-saudi-jobs.csv"
    )
    df = get_tapneo_jobs(input_path)

    print(df[["company", "location", "job_function"]].head(15))

    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw", "tapneo_tech_jobs.csv"
    )
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"💾 تم حفظ CSV في: {csv_path}")

    json_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw", "tapneo_tech_jobs.json"
    )
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"💾 تم حفظ JSON في: {json_path}")