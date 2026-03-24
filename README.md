# Gmail Analytics Platform on Snowflake

End-to-end email intelligence platform built on Snowflake with Cortex AI, solving 6 key business problems through automated email analysis.

## Overview

| Component | Details |
|-----------|---------|
| **Database** | `GMAIL_ANALYTICS` |
| **Tables** | 6 normalized, Gmail API-compatible |
| **Views** | 11 analytics views |
| **Dashboards** | 2 Streamlit apps (12 tabs total) |
| **AI** | Snowflake Cortex (SUMMARIZE + COMPLETE) |
| **Data** | 1,100+ synthetic + live Gmail ingestion |

## 6 Business Problems Solved

| # | Problem | Solution |
|---|---------|----------|
| 1 | Alert & notification tracking | SQL view with source/category classification |
| 2 | High priority + unanswered emails | Thread-level response analysis |
| 3 | Sensitive data in emails | 7-pattern detection (SSN, credit cards, passwords, etc.) |
| 4 | Availability today/weekly/monthly | Meeting & schedule extraction from email subjects |
| 5 | Executive task summaries | Cortex AI SUMMARIZE + COMPLETE |
| 6 | Q&A on past discussions | Cortex AI RAG-style question answering |

## Architecture

```
   Gmail API (OAuth2, read-only)
              │
              ▼
   Python Ingestion Script ──────────────────┐
              │                               │
              ▼                               ▼
   ┌──────────────────────────────────────────────┐
   │              SNOWFLAKE PLATFORM               │
   │                                               │
   │  GMAIL_ANALYTICS.CORE     Security Layer      │
   │  ├─ 6 Tables              ├─ OAuth2 Secret    │
   │  ├─ 3 Procedures          ├─ Network Rule     │
   │  └─ 1 Stage               └─ Security Integ.  │
   │         │                                      │
   │  GMAIL_ANALYTICS.ANALYTICS                     │
   │  └─ 11 Views (7 base + 4 intelligence)        │
   │         │                                      │
   │  Cortex AI (mistral-large2)                    │
   │  ├─ SUMMARIZE → Executive briefings            │
   │  └─ COMPLETE  → Q&A + Action extraction        │
   │         │                                      │
   │  2 Streamlit Dashboards (12 tabs)              │
   └──────────────────────────────────────────────┘
```

## Quick Start

### Step 1: Set up the database
```sql
-- Run in order
sql/01_setup_database.sql
sql/02_create_tables.sql
```

### Step 2: Generate synthetic data
```sql
-- Create and execute the data generator
procedures/generate_synthetic_data.sql
CALL GMAIL_ANALYTICS.CORE.GENERATE_SYNTHETIC_GMAIL_DATA();
```

### Step 3: Create analytics views
```sql
sql/03_create_analytics_views.sql
sql/04_create_intelligence_views.sql
```

### Step 4: Deploy dashboards
```sql
procedures/deploy_analytics_dashboard.sql
CALL GMAIL_ANALYTICS.CORE.DEPLOY_STREAMLIT_DASHBOARD();

procedures/deploy_intelligence_hub.sql
CALL GMAIL_ANALYTICS.CORE.DEPLOY_INSIGHTS_DASHBOARD();
```

### Step 5: (Optional) Connect real Gmail
```bash
cd python/
pip install -r requirements.txt
# Edit gmail_to_snowflake.py with your Snowflake credentials
python gmail_to_snowflake.py
```

## Gmail API Setup (for live data)

1. Create project at [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Gmail API**
3. Configure **OAuth consent screen** (External, add test users)
4. Create **Desktop app** OAuth2 credentials
5. Download `credentials.json` into `python/` directory
6. Run `python gmail_to_snowflake.py` (opens browser for consent)

## Data Model

```
EMAIL_CONTACTS (1)────(N) EMAIL_MESSAGES (N)────(1) EMAIL_THREADS
                              │
                         (1)  │  (N)
                              │
                    EMAIL_ATTACHMENTS
                              │
                    EMAIL_MESSAGE_LABEL_MAP
                              │
                         (N)  │  (1)
                              │
                        EMAIL_LABELS
```

## Snowflake Objects

| Schema | Object | Type |
|--------|--------|------|
| CORE | EMAIL_CONTACTS | Table |
| CORE | EMAIL_THREADS | Table |
| CORE | EMAIL_MESSAGES | Table |
| CORE | EMAIL_ATTACHMENTS | Table |
| CORE | EMAIL_LABELS | Table |
| CORE | EMAIL_MESSAGE_LABEL_MAP | Table |
| CORE | GENERATE_SYNTHETIC_GMAIL_DATA() | Procedure |
| CORE | DEPLOY_STREAMLIT_DASHBOARD() | Procedure |
| CORE | DEPLOY_INSIGHTS_DASHBOARD() | Procedure |
| CORE | GMAIL_ANALYTICS_DASHBOARD | Streamlit |
| CORE | GMAIL_INTELLIGENCE_HUB | Streamlit |
| ANALYTICS | VW_EMAIL_ACTIVITY_DAILY | View |
| ANALYTICS | VW_THREAD_SUMMARY | View |
| ANALYTICS | VW_CONTACT_ENGAGEMENT | View |
| ANALYTICS | VW_LABEL_DISTRIBUTION | View |
| ANALYTICS | VW_SUSPICIOUS_EMAIL_ANALYSIS | View |
| ANALYTICS | VW_ATTACHMENT_ANALYTICS | View |
| ANALYTICS | VW_SNOWFLAKE_ALERTS | View |
| ANALYTICS | VW_ALERTS_AND_NOTIFICATIONS | View |
| ANALYTICS | VW_HIGH_IMPORTANCE_AND_UNANSWERED | View |
| ANALYTICS | VW_SENSITIVE_DATA_DETECTION | View |
| ANALYTICS | VW_AVAILABILITY_ANALYSIS | View |

## Security

- Gmail access is **read-only** (`gmail.readonly` scope)
- OAuth tokens stored as encrypted Snowflake SECRETs
- Network egress restricted to Google APIs only
- All Cortex AI processing stays within Snowflake
- Sensitive data auto-flagged (7 detection patterns)
- Never commit `credentials.json` or `token.json`

## Tech Stack

Snowflake SQL | Snowpark Python | Streamlit in Snowflake | Cortex AI (mistral-large2) | Gmail API v1 | OAuth2

## License

MIT
