<<<<<<< HEAD
# Job Data Pipeline (Saudi Arabia Tech Market Analytics)

A modular, scalable, and collaborative data pipeline designed to collect, aggregate, and structure tech job market data across Saudi Arabia.
---

## 🏗️ Directory Structure

```
Job-Data-Pipeline/
├── Ingestion/                      <-- Scraper scripts for various job sources
│   ├── Tanqeeb.py                  <-- Tanqeeb job board scraper
│   ├── freehire.py                 <-- FreeHire API data ingestion
│   └── jsearch.py              <--  JSearch API scraper
├── utils/                          <-- Shared utilities and helper scripts
│   └── skills_extractor.py         <-- Regex-based technical skills taxonomy extractor
├── data/                           
│   └── raw/                        <-- Storage layer for raw JSON and spreadsheet files
├── .env                            <-- Secret API keys (local only, never committed)
├── .env.example                    <-- Template file for required environment variables
├── .gitignore                      <-- Config to protect sensitive files and local caches
└── requirements.txt                <-- Python package dependencies       
```

---

## 🚀 Getting Started

### **1. Clone the Repository**

Clone the project repository to your local machine:

```bash
git clone https://github.com/Leel15/Job-Data-Pipeline.git
cd Job-Data-Pipeline
```

### **2. Install Dependencies**

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### **3. Configure Environment Variables**

Create a file named `.env` in the root project directory (`Job-Data-Pipeline/`).

Add your private API keys in the following format:

```
SCRAPEOPS_API_KEY=your_scrapeops_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

---

## 🛡️ Deduplication Strategy

The scrapers are configured to automatically read existing records from the Raw Data JSON files (`_tech.json`) pushed exclusively to GitHub.

When team members pull the latest updates and run a scraper, the system automatically detects previously saved links and skips them, completely preventing duplicate data without requiring local cache files to be committed.

---


## ⚙️ Configuration


### Git Ignore Rules

The `.gitignore` file protects:
- `.env` (local secrets)
- Local cache and temporary files
- System-specific files


---

## ⚠️ Important Notes

- **Never commit `.env`** — it contains sensitive API keys
- **Pull before pushing** to avoid merge conflicts
- **Keep scrapers modular** for easy maintenance and scaling

=======
# Job Data Pipeline
>>>>>>> a6e8688746c66d79f9095b4cf28a67dc257ac6cc
