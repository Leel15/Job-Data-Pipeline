import re
from typing import List, Set

TECHNICAL_SKILLS = {
    'python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'sql',
    'html', 'css', 'php', 'ruby', 'golang', 'go', 'rust', 'swift', 'kotlin',
    'scala', 'r', 'matlab', 'perl', 'groovy', 'bash', 'shell', 'powershell',
    
    'react', 'vue', 'angular', 'angularjs', 'next.js', 'nuxt', 'svelte',
    'ember', 'backbone', 'jquery', 'bootstrap', 'tailwind', 'webpack',
    'babel', 'gulp', 'grunt', 'npm', 'yarn', 'pnpm', 'rest api', 'graphql',
    'websocket', 'http', 'ajax', 'json', 'xml', 'soap', 'wsdl',
    
    'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot',
    'hibernate', 'sqlalchemy', 'mongodb', 'mysql', 'postgresql', 'oracle',
    'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'couchdb', 'firestore',
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'ci/cd',
    
    'sql server', 'mariadb', 'sqlite', 'neo4j', 'memcached', 'rabbitmq',
    'kafka', 'activemq', 'apachespark', 'hadoop', 'hive', 'pig',
    
    'git', 'svn', 'jenkins', 'gitlab', 'github', 'bitbucket', 'terraform',
    'ansible', 'puppet', 'chef', 'vagrant', 'docker-compose', 'helm',
    'prometheus', 'grafana', 'elasticsearch', 'logstash', 'kibana', 'elk',
    
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
    'scikit-learn', 'sklearn', 'pandas', 'numpy', 'scipy', 'matplotlib',
    'seaborn', 'nlp', 'natural language processing', 'computer vision',
    'opencv', 'cv', 'cvat', 'yolo', 'rcnn', 'lstm', 'rnn', 'cnn',
    'xgboost', 'lightgbm', 'catboost', 'reinforcement learning', 'rl',
    'llm', 'large language model', 'gpt', 'bert', 'transformer',
    
    'cybersecurity', 'information security', 'network security', 'firewall',
    'ccna', 'ccnp', 'ccna collaboration', 'networking', 'vpn', 'ssl', 'tls',
    'ssh', 'https', 'dns', 'dhcp', 'ldap', 'kerberos', 'oauth', 'saml',
    'encryption', 'cryptography', 'penetration testing', 'vulnerability',
    
    'aws', 'amazon web services', 's3', 'ec2', 'lambda', 'rds', 'dynamodb',
    'sqs', 'sns', 'cloudformation', 'azure', 'microsoft azure', 'app service',
    'sql database', 'cosmos db', 'gcp', 'google cloud platform', 'app engine',
    'cloud functions', 'cloud storage', 'bigquery', 'dataflow',
    
    'android', 'ios', 'swift', 'kotlin', 'flutter', 'react native', 'ionic',
    'xamarin', 'native development', 'mobile development', 'appium',
    
    'scrum', 'kanban', 'agile', 'safe', 'prince2', 'pmp', 'jira', 'confluence',
    'trello', 'asana', 'monday.com', 'notion', 'slack', 'teams',
    
    'sap', 'sap ariba', 'sap s/4hana', 'sap successfactors', 'sap analytics',
    'oracle fusion', 'oracle erp', 'salesforce', 'crm', 'odoo', 'primavera',
    'erp', 'enterprise resource planning', 'business intelligence', 'bi',
    'data warehouse', 'dwh', 'etl', 'elt',
    
    'power bi', 'tableau', 'looker', 'qlik', 'microstrategy', 'cognos',
    'sisense', 'google analytics', 'ga4', 'google tag manager', 'gtm',
    'adobe analytics', 'mixpanel', 'amplitude', 'segment', 'analytics',
    
    'autocad', 'bim', 'gis', 'arcgis', 'revit', 'sketchup', 'cad',
    'unreal engine', 'unity', 'blender', '3ds max', 'maya',
    
    'microsoft dynamics', 'power apps', 'power automate', 'power query',
    'dataverse', 'fhir', 'hl7', 'health information exchange',
    
    'articulate 360', 'adobe captivate', 'addie', 'instructional design',
    'e-learning', 'lms', 'learning management system',
    
    'wordpress', 'drupal', 'joomla', 'shopify', 'magento', 'woocommerce',
    'adobe commerce', 'cms', 'content management system', 'headless cms',
    
    'microservices', 'serverless', 'iam', 'identity access management',
    'saml', 'oauth2', 'jwt', 'api gateway', 'service mesh', 'istio',
    'envoy', 'circuit breaker', 'load balancing', 'cdn', 'content delivery',
    'message queue', 'event streaming', 'event-driven', 'cqrs', 'saga',
    'outsystems', 'low-code', 'no-code', 'rpa', 'robotic process automation',
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'llm', 'gen ai', 'generative ai', 'prompt engineering',
    'algolia', 'elasticsearch', 'solr', 'search engine', 'full-text search',
}

STOP_WORDS = {
    'and', 'or', 'the', 'a', 'an', 'with', 'without', 'for', 'to', 'of', 'in',
    'experience', 'knowledge', 'skill', 'skills', 'required', 'preferred',
    'ability', 'strong', 'expertise', 'proficiency', 'advanced', 'basic',
    'understanding', 'hands-on', 'proven', 'excellent', 'good', 'very',
    'must', 'should', 'can', 'will', 'would', 'could', 'have', 'has',
    'working', 'work', 'project', 'projects', 'team', 'teams', 'management',
    'key', 'main', 'primary', 'secondary', 'support', 'supporting',
}

def normalize_skill(skill: str) -> str:
    if not skill:
        return ""
    
    skill = skill.lower().strip()
    
    skill = re.sub(r'[\(\)\[\]\{\}<>]', '', skill)
    
    skill = re.sub(r'\.+', '', skill)
    
    skill = re.sub(r'\s+', ' ', skill).strip()
    
    corrections = {
        'c # ': 'c#',
        '.net core': '.net',
        'node .js': 'node.js',
        'asp .net': 'asp.net',
        'machine_learning': 'machine learning',
        'deep_learning': 'deep learning',
        'natural_language_processing': 'nlp',
        'computer_vision': 'computer vision',
    }
    
    for wrong, correct in corrections.items():
        if wrong in skill:
            skill = skill.replace(wrong, correct)
    
    return skill


def extract_tech_skills(text: str) -> List[str]:
   
    if not text:
        return []
    
    text = text.lower()
    
    text = re.sub(r'[^\w\s\-\.\/\+#]', ' ', text)
    
    text = re.sub(r'\s+', ' ', text)
    
    found_skills: Set[str] = set()
    
    for skill in sorted(TECHNICAL_SKILLS, key=len, reverse=True):
        pattern = r'\b' + re.escape(skill) + r'\b'
        
        if re.search(pattern, text):
            found_skills.add(normalize_skill(skill))
    
    compound_skills = [
        r'machine\s+learning',
        r'deep\s+learning',
        r'natural\s+language\s+processing',
        r'computer\s+vision',
        r'reinforcement\s+learning',
        r'feature\s+engineering',
        r'data\s+science',
        r'data\s+analysis',
        r'api\s+gateway',
        r'service\s+mesh',
        r'api\s+integration',
        r'cloud\s+computing',
        r'edge\s+computing',
        r'quantum\s+computing',
        r'blockchain\s+technology',
        r'iot\s+development',
        r'web\s+development',
        r'mobile\s+development',
        r'full[\s\-]?stack',
        r'front[\s\-]?end',
        r'back[\s\-]?end',
        r'devops',
        r'dev\s+ops',
        r'mlops',
        r'ml\s+ops',
        r'enterprise\s+resource\s+planning',
        r'business\s+intelligence',
        r'content\s+management',
        r'learning\s+management',
        r'relationship\s+management',
        r'identity\s+and\s+access',
        r'risk\s+management',
        r'project\s+management',
        r'information\s+security',
        r'network\s+security',
        r'cyber\s+security',
        r'penetration\s+testing',
        r'vulnerability\s+assessment',
        r'incident\s+response',
        r'disaster\s+recovery',
        r'business\s+continuity',
    ]
    
    for pattern in compound_skills:
        if re.search(pattern, text):
            match = re.search(pattern, text)
            if match:
                skill_text = normalize_skill(match.group())
                if skill_text and skill_text not in STOP_WORDS:
                    found_skills.add(skill_text)
    
    version_patterns = [
        r'(python|java|node|javascript)\s*\d+(?:\.\d+)*',
        r'(spring|spring\s+boot)\s+\d+(?:\.\d+)*',
        r'(django|flask)\s+\d+(?:\.\d+)*',
        r'(react|vue|angular)\s+\d+(?:\.\d+)*',
        r'(.net|\.net)\s+core\s+\d+(?:\.\d+)*',
        r'(elasticsearch|kibana|logstash)\s+\d+(?:\.\d+)*',
    ]
    
    for pattern in version_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                skill_text = normalize_skill(match[0])
            else:
                skill_text = normalize_skill(match)
            
            if skill_text and len(skill_text) > 1:
                found_skills.add(skill_text)
    
   
    final_skills = []
    for skill in found_skills:
        if (skill and 
            len(skill) > 1 and 
            skill not in STOP_WORDS and
            not skill.isdigit()):
            final_skills.append(skill)
    
    return sorted(list(set(final_skills)))


def extract_skills_with_context(text: str, context_window: int = 50) -> dict:
   
    skills = extract_tech_skills(text)
    skills_with_context = {}
    
    text_lower = text.lower()
    
    for skill in skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        matches = list(re.finditer(pattern, text_lower))
        
        contexts = []
        for match in matches:
            start = max(0, match.start() - context_window)
            end = min(len(text), match.end() + context_window)
            context = text[start:end].strip()
            contexts.append(context)
        
        if contexts:
            skills_with_context[skill] = contexts
    
    return skills_with_context

