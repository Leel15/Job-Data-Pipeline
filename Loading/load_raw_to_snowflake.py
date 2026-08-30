import json
import os
import snowflake.connector

ACCOUNT = 'mqvmvtk-mu79882'
USER = 'Mohammed' 
PASSWORD = 'User@Pass2026!'
WAREHOUSE = 'COMPUTE_WH'
DATABASE = 'JOB_MARKET_DB'
SCHEMA = 'RAW_SCHEMA'
ROLE = 'SYSADMIN'

conn = snowflake.connector.connect(
    account=ACCOUNT,
    user=USER,
    password=PASSWORD,
    role=ROLE,
    warehouse=WAREHOUSE,
    database=DATABASE,
    schema=SCHEMA,
)
cursor = conn.cursor()

file_path = os.path.join("data", "raw", "tanqeeb_saudi_jobs_tech.json")
if not os.path.exists(file_path):
    file_path = "tanqeeb_saudi_jobs_tech.json"

if not os.path.exists(file_path):
    file_path = os.path.join("data", "raw", "tanqeeb_saudi_jobs.json")
if not os.path.exists(file_path):
    file_path = "tanqeeb_saudi_jobs.json"

print(f"قراءة الملف من: {file_path}")
with open(file_path, "r", encoding="utf-8") as f:
    jobs_data = json.load(f)

insert_query = """
    INSERT INTO JOB_MARKET_DB.RAW_SCHEMA.RAW_TANQEEB_JOBS (RAW_PAYLOAD) 
    SELECT PARSE_JSON(%s)
"""

print(f"جاري رفع {len(jobs_data)} سجل إلى Snowflake...")
for job in jobs_data:
    cursor.execute(insert_query, (json.dumps(job, ensure_ascii=False),))

conn.commit()
cursor.close()
conn.close()

print("✅ تم رفع البيانات الخام بنجاح إلى جدول RAW_TANQEEB_JOBS!")