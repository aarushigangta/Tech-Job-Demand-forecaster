# Tech Job Demand Forecaster

> A data pipeline that forecasts which tech roles will see increased hiring demand and surfaces the skills most associated with those high-growth roles. It is built to help freshers make smarter upskilling decisions before entering the job market.

---

## 🎯 What This Project Does

1. Collects real job postings from **Internshala** (scraper) and **LinkedIn** (Kaggle dataset)
2. Cleans and unifies them into a single time-stamped dataset
3. Analyzes demand trends per role over time
4. Trains a regression model to forecast which roles are growing
5. Maps the top skills associated with high-growth roles
6. Visualizes everything — trends, forecasts, and skill heatmaps

---

## 🗂️ Project Structure
```
job-demand-forecaster/
│
├── data/
│   ├── raw/                        # Raw scraped & downloaded CSVs
│   │   ├── internshala_jobs.csv    # Scraped from Internshala
│   │   └── linkedin_jobs.csv       # Downloaded from Kaggle
│   └── processed/                  # Cleaned & merged data 
│
├── Internshala_scraper.py   # Internshala BeautifulSoup scraper
├── Clean_merge.py           # Data cleaning & feature engineering 
├── Trend_analysis.py        # Role demand trend analysis           
├── ml_model.py              # Regression forecasting model        
├── Skill_mapping.py         # Skill frequency per high-growth role
├── Visualizations.py        # All charts and heatmaps             
│
├── requirements.txt
└── README.md


---

## 📦 Phase 1 — Data Collection

### Internshala Scraper

Scrapes tech job listings from [Internshala](https://internshala.com) across 10 role categories.

**Roles scraped:** Python, Data Science, Machine Learning, Web Development, Data Analyst, Java, React, Cloud Computing, DevOps, Android Development

**Fields extracted:**

| Field | Description |
|-------|-------------|
| `title` | Job title |
| `company` | Company name |
| `location` | City / Work from home |
| `stipend` | Salary or stipend range |
| `skills` | Required skills (comma-separated) |
| `date_posted` | Converted to `YYYY-MM-DD` |
| `search_role` | Role slug used to find the listing |
| `source` | `internshala` |

**Current dataset stats:**
- 830 deduplicated listings
- Fill rates: title 100%, company 100%, location 100%, date 100%, skills ~80%+

**Run the scraper:**
```bash
pip install requests beautifulsoup4 pandas lxml

# Normal run
python phase1_internshala_scraper.py

# Debug mode — inspect raw HTML of one card
python phase1_internshala_scraper.py --debug
```

### Kaggle Dataset

**Dataset used:** [LinkedIn Job Postings 2023–2024](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) by arshkon

Downloaded manually from Kaggle. Key columns used: `title`, `original_listed_time`, `skills_desc`, `location`.

---

## ⚙️ Setup
```bash
# Clone the repo
git clone https://github.com/your-username/job-demand-forecaster.git
cd job-demand-forecaster

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt**
```
requests
beautifulsoup4
lxml
pandas
numpy
scikit-learn
matplotlib
seaborn
```

---




