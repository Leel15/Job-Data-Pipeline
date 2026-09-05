import re

# (Technical Hard Skills Only)
TECH_TAXONOMY = {
    "python": [r"\bpython\b", r"\bبايثون\b"],
    "java": [r"\bjava\b"],
    "c#": [r"\bc#\b", r"\bcsharp\b", r"\bc\s*#\b"],
    "c++": [r"\bc\+\+\b"],
    "c": [r"\b(?<!\w)c(?!\w|\+|\#)"],  # C language boundary
    "javascript": [r"\bjavascript\b", r"\bjs\b"],
    "typescript": [r"\btypescript\b", r"\bts\b"],
    "sql": [r"\bsql\b"],
    "php": [r"\bphp\b"],
    "kotlin": [r"\bkotlin\b"],
    "swift": [r"\bswift\b"],
    "go": [r"\bgolang\b", r"\bgo\s+language\b"],
    "rust": [r"\brust\b"],
    "r": [r"\br\s+language\b", r"\bprogramming\s+in\s+r\b"],
    "bash": [r"\bbash\b", r"\bshell\s*script(ing)?\b"],
    "powershell": [r"\bpowershell\b"],
    "html": [r"\bhtml5?\b"],
    "css": [r"\bcss3?\b"],
    "xml": [r"\bxml\b"],
    "json": [r"\bjson\b"],


    "react": [r"\breact(\.js)?\b"],
    "react native": [r"\breact\s*native\b"],
    "angular": [r"\bangular(\.js)?\b"],
    "vue": [r"\bvue(\.js)?\b"],
    "next.js": [r"\bnext(\.js)?\b"],
    "node.js": [r"\bnode(\.js)?\b"],
    ".net": [r"\b\.net\b", r"\basp\.net\b", r"\bdotnet\b", r"\b\.net\s*core\b"],
    "django": [r"\bdjango\b"],
    "fastapi": [r"\bfastapi\b"],
    "flask": [r"\bflask\b"],
    "spring boot": [r"\bspring\s*boot\b", r"\bspring\s*framework\b"],
    "laravel": [r"\blaravel\b"],
    "flutter": [r"\bflutter\b"],
    "android": [r"\bandroid\b", r"\bأندرويد\b"],
    "ios": [r"\bios\b"],
    "bootstrap": [r"\bbootstrap\b"],
    "tailwind": [r"\btailwind(\s*css)?\b"],
    "graphql": [r"\bgraphql\b"],
    "rest api": [r"\brest(ful)?\s*apis?\b", r"\bapi\s*integration\b", r"\brest\b"],
    "microservices": [r"\bmicroservices?\b"],
    "outsystems": [r"\boutsystems\b"],
    "sharepoint": [r"\bsharepoint\b"],


    "postgresql": [r"\bpostgres(ql)?\b"],
    "mysql": [r"\bmysql\b"],
    "sql server": [r"\bsql\s*server\b", r"\bmssql\b"],
    "oracle": [r"\boracle(\s*database)?\b", r"\boracle\s*adf\b"],
    "mongodb": [r"\bmongodb\b", r"\bmongo\b"],
    "redis": [r"\bredis\b"],
    "snowflake": [r"\bsnowflake\b"],
    "databricks": [r"\bdatabricks\b"],
    "bigquery": [r"\bbigquery\b"],
    "redshift": [r"\bredshift\b"],
    "microsoft fabric": [r"\b(microsoft\s*)?fabric\b"],
    "hadoop": [r"\bhadoop\b"],
    "spark": [r"\b(apache\s*)?spark\b", r"\bpyspark\b"],
    "kafka": [r"\b(apache\s*)?kafka\b"],
    "airflow": [r"\b(apache\s*)?airflow\b"],
    "dbt": [r"\bdbt\b"],
    "etl": [r"\betl\b", r"\belt\b"],
    "power bi": [r"\bpower\s*bi\b", r"\bpowerbi\b"],
    "tableau": [r"\btableau\b"],
    "data warehouse": [r"\bdata\s*warehous(e|ing)\b", r"\bdwh\b"],
    "data lake": [r"\bdata\s*lake\b"],
    "data governance": [r"\bdata\s*governance\b", r"\bحوكمة\s*البيانات\b"],

    "aws": [r"\baws\b", r"\bamazon\s*web\s*services\b"],
    "azure": [r"\bazure\b", r"\bأزور\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle\s*cloud(\s*platform)?\b"],
    "docker": [r"\bdocker\b", r"\bدوكر\b"],
    "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "terraform": [r"\bterraform\b"],
    "ansible": [r"\bansible\b"],
    "ci/cd": [r"\bci[/-]?cd\b"],
    "jenkins": [r"\bjenkins\b"],
    "github actions": [r"\bgithub\s*actions\b"],
    "gitlab": [r"\bgitlab(\s*ci)?\b"],
    "argocd": [r"\bargo\s*cd\b"],
    "linux": [r"\blinux\b", r"\bلينكس\b", r"\bubuntu\b", r"\bredhat\b"],
    "git": [r"\bgit\b", r"\bgithub\b"],
    "grafana": [r"\bgrafana\b"],
    "prometheus": [r"\bprometheus\b"],
    "datadog": [r"\bdatadog\b"],
    "splunk": [r"\bsplunk\b"],
    "elk": [r"\belk(\s*stack)?\b", r"\belasticsearch\b"],
    "vault": [r"\bhashicorp\s*vault\b", r"\bvault\b"],

    "machine learning": [r"\bmachine\s*learning\b", r"\bتعلم\s*الآلة\b", r"\bml\b"],
    "deep learning": [r"\bdeep\s*learning\b", r"\bالتعلم\s*العميق\b"],
    "ai": [r"\bai\b", r"\bartificial\s*intelligence\b", r"\bذكاء\s*اصطناعي\b"],
    "nlp": [r"\bnlp\b", r"\bnatural\s*language\s*processing\b"],
    "computer vision": [r"\bcomputer\s*vision\b", r"\bopencv\b"],
    "pytorch": [r"\bpytorch\b"],
    "tensorflow": [r"\btensorflow\b"],
    "llm": [r"\bllms?\b", r"\blarge\s*language\s*models?\b"],
    "chatgpt": [r"\bchatgpt\b"],
    "langchain": [r"\blangchain\b"],

    "cybersecurity": [r"\bcybersecurity\b", r"\bأمن\s*سيبراني\b", r"\bأمن\s*المعلومات\b", r"\binformation\s*security\b"],
    "networking": [r"\bnetworking\b", r"\bشبكات\b"],
    "firewall": [r"\bfirewalls?\b", r"\bجدار\s*ناري\b", r"\bpalo\s*alto\b", r"\bfortigate\b"],
    "ccna": [r"\bccna\b"],
    "ccnp": [r"\bccnp\b"],
    "siem": [r"\bsiem\b"],
    "iam": [r"\biam\b", r"\bidentity\s*(and\s*)?access\s*management\b"],
    "vpn": [r"\bvpn\b"],

    "sap": [r"\bsap\b", r"\bsap\s*ariba\b"],
    "microsoft dynamics": [r"\b(microsoft\s*)?dynamics(\s*365)?\b", r"\bd365\b"],
    "power apps": [r"\bpower\s*apps\b"],
    "power automate": [r"\bpower\s*automate\b"],
    "dataverse": [r"\bdataverse\b"],
    "servicenow": [r"\bservicenow\b"],
    "salesforce": [r"\bsalesforce\b"],
    "jira": [r"\bjira\b"],
    "selenium": [r"\bselenium\b"],
    "appium": [r"\bappium\b"]
}

def extract_tech_skills(text):

    if not text:
        return []

    text_lower = str(text).lower()
    found_skills = set()

    for skill, patterns in TECH_TAXONOMY.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, flags=re.IGNORECASE):
                found_skills.add(skill)
                break

    return sorted(list(found_skills))