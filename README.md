# Job Data Pipeline (Saudi Arabia Tech Market Analytics)

A modular, scalable, and collaborative data pipeline designed to collect, aggregate, and structure tech job market data across Saudi Arabia.
---

## 🏗️ Directory Structure

```
Job-Data-Pipeline/
├── Ingestion/                          <-- Scraper scripts and API fetchers for raw job boards
│   ├── Tanqeeb.py                      <-- Tanqeeb job board scraper
│   ├── freehire.py                     <-- FreeHire API data ingestion script
│   ├── jooble_api.py                   <-- Jooble API integration script
│   └── jsearch.py                      <-- JSearch API job scraper
├── Transformation/                     <-- Standardization and cleaning pipelines for each source
│   ├── standardizer_jsearch.py         <-- Cleans and formats JSearch raw records
│   ├── standardizer_linkedin.py        <-- Cleans and formats LinkedIn data
│   └── standardizer_tanqeeb.py         <-- Cleans and formats Tanqeeb raw records
├── data/                               <-- Data storage layers (Bronze, Silver, and local staging)
│   ├── Processed/                      <-- Silver/Processed layer for cleaned JSON and Parquet files
│   └── raw/                            <-- Bronze layer for raw, untransformed JSON and Excel files
├── utils/                              <-- Shared helper modules and libraries
│   └── skills_extractor.py             <-- Regex-based technical skills taxonomy and extraction engine
├── .env.example                        <-- Template file outlining required environment variables
├── .gitignore                          <-- Configuration to exclude sensitive data, caches, and secrets
└── README.md                           <-- Project documentation and setup guide     
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

