================================================================================
PROMPT: CREATE THE "GMAIL INTELLIGENCE HUB" SKILL FOR SNOWFLAKE CORTEX CODE (COCO)
================================================================================
Use the following prompt with Cortex Code (COCO) in a Snowflake Workspace to
have it build the complete Gmail Intelligence Hub skill from scratch.
Copy everything between the START and END markers below and paste it as a
message to COCO.
================================================================================
--- START OF PROMPT ---
================================================================================
I want you to build a complete Cortex Code skill called "Gmail_Intelligence_Hub".
This skill automates the analysis of Gmail email data stored in Snowflake by
gathering evidence from core email tables and prebuilt analytics views,
correlating signals across activity, contacts, threads, labels, attachments,
security threats, sensitive data, and productivity patterns, and delivering
structured insights with actionable recommendations.

IMPORTANT PREREQUISITE: This skill assumes the GMAIL_ANALYTICS database already
exists with the CORE and ANALYTICS schemas populated. The CORE schema must
contain 6 base tables (EMAIL_MESSAGES, EMAIL_THREADS, EMAIL_CONTACTS,
EMAIL_LABELS, EMAIL_ATTACHMENTS, EMAIL_MESSAGE_LABEL_MAP) and the ANALYTICS
schema must contain 11 prebuilt views. If these do not exist, the setup SQL
(FILE 3) must be run first to create the foundation, followed by data loading.

Below are the EXACT requirements. Create all three files in the directory
`.snowflake/cortex/skills/Gmail_Intelligence_Hub/`.

------------------------------------------------------------------------
FILE 1: SKILL.md
------------------------------------------------------------------------
Create the SKILL.md file with this frontmatter:
```
---
name: Gmail_Intelligence_Hub
description: AI-powered email intelligence that automatically analyzes Gmail
  data stored in Snowflake — covering inbox activity, contact engagement,
  security threat detection, sensitive data exposure, attachment analytics,
  thread insights, alert monitoring, and availability patterns. Gathers
  evidence from core email tables and prebuilt analytics views, correlates
  signals, and synthesizes actionable insights.
---
```

The body must define a 7-phase analysis workflow. Each phase is described
below with its exact purpose and the SQL templates or output formats it must
contain.

### PHASE 1 - REQUEST INTERPRETATION
Parse the user's request to extract:
- Analysis Type: one of ACTIVITY, ENGAGEMENT, SECURITY, SENSITIVE_DATA,
  ATTACHMENTS, THREADS, ALERTS, AVAILABILITY, LABELS, SEARCH
- Object Identifier: contact name/email, domain, thread subject, label name,
  date range, or keyword
- Time Window: explicit or default to all available data
- Context: category filter, importance level, sender/domain filter

Include resolution rules:
- "today's emails" -> WHERE SENT_AT >= CURRENT_DATE()
- "this week" -> WHERE SENT_AT >= DATE_TRUNC('week', CURRENT_DATE())
- "last month" -> previous full calendar month
- "from [name]" -> JOIN EMAIL_CONTACTS WHERE DISPLAY_NAME ILIKE '%name%'
- "from [domain]" -> JOIN EMAIL_CONTACTS WHERE DOMAIN = 'domain'
- "suspicious" / "phishing" -> route to SECURITY analysis type
- "sensitive" / "PII" / "exposure" -> route to SENSITIVE_DATA analysis type
- "unanswered" / "follow up" -> route to VW_HIGH_IMPORTANCE_AND_UNANSWERED
- "alerts" / "notifications" -> route to ALERTS analysis
- "busy times" / "schedule" -> route to AVAILABILITY analysis

### PHASE 2 - EVIDENCE COLLECTION
Include 14 diagnostic SQL query templates that should be executed IN PARALLEL
where possible. Each query must have placeholders ({{variable}}) for dynamic
values. The 14 queries are:

1. Email Activity Summary - from GMAIL_ANALYTICS.ANALYTICS.VW_EMAIL_ACTIVITY_DAILY,
   filtering by date range. Include ACTIVITY_DATE, TOTAL_MESSAGES, SENT_COUNT,
   RECEIVED_COUNT, READ_COUNT, UNREAD_COUNT, STARRED_COUNT, WITH_ATTACHMENTS,
   SUSPICIOUS_COUNT, ACTIVE_THREADS, UNIQUE_SENDERS, CATEGORY, DAY_OF_WEEK,
   PEAK_HOUR.

2. Contact Engagement - from GMAIL_ANALYTICS.ANALYTICS.VW_CONTACT_ENGAGEMENT,
   with optional filters on DISPLAY_NAME and DOMAIN. Include CONTACT_ID,
   EMAIL, DISPLAY_NAME, DOMAIN, CONTACT_TYPE, IS_INTERNAL, MESSAGES_SENT,
   MESSAGES_READ, MESSAGES_WITH_ATTACHMENTS, THREADS_PARTICIPATED,
   FIRST_MESSAGE_AT, LAST_MESSAGE_AT, ACTIVE_SPAN_DAYS, AVG_SPAM_SCORE,
   SUSPICIOUS_MESSAGES. Order by MESSAGES_SENT DESC with LIMIT.

3. Suspicious Email Analysis - from
   GMAIL_ANALYTICS.ANALYTICS.VW_SUSPICIOUS_EMAIL_ANALYSIS. Include MESSAGE_ID,
   SUBJECT, SNIPPET, SENT_AT, SPAM_SCORE, CATEGORY, IS_SPAM, SENDER_EMAIL,
   SENDER_NAME, SENDER_DOMAIN, CONTACT_TYPE, PHISHING_FLAGS, HAS_URGENCY,
   HAS_SUSPICIOUS_LINKS, HAS_IMPERSONATION, REQUESTS_CREDENTIALS,
   THREAD_SUBJECT, THREAD_MESSAGE_COUNT. Order by SPAM_SCORE DESC.

4. Sensitive Data Detection - from
   GMAIL_ANALYTICS.ANALYTICS.VW_SENSITIVE_DATA_DETECTION, filtering where
   SENSITIVITY_LEVEL IN ('high', 'medium'). Include MESSAGE_ID, SUBJECT,
   SNIPPET, SENT_AT, CATEGORY, SENDER_NAME, SENDER_EMAIL, HAS_SSN_PATTERN,
   HAS_CREDIT_CARD_PATTERN, HAS_PASSWORD_MENTION, HAS_BANK_INFO,
   HAS_API_KEY_PATTERN, HAS_CONFIDENTIAL_MARKER, HAS_WIRE_TRANSFER,
   IS_SUSPICIOUS, SPAM_SCORE, SENSITIVITY_LEVEL.

5. Attachment Analytics - from
   GMAIL_ANALYTICS.ANALYTICS.VW_ATTACHMENT_ANALYTICS. Include ATTACHMENT_ID,
   FILENAME, CONTENT_TYPE, SIZE_BYTES, SIZE_MB, IS_INLINE, MESSAGE_ID,
   SUBJECT, CATEGORY, SENT_AT, SENDER_NAME, SENDER_DOMAIN, FILE_EXTENSION,
   FILE_TYPE_GROUP. Order by SIZE_BYTES DESC.

6. High Importance & Unanswered - from
   GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED, filtering
   WHERE IS_UNANSWERED = TRUE. Include MESSAGE_ID, THREAD_ID, SUBJECT,
   SNIPPET, SENT_AT, CATEGORY, IMPORTANCE, IS_READ, IS_STARRED, IS_SENT,
   SENDER_NAME, SENDER_EMAIL, THREAD_SUBJECT, HAS_MY_REPLY, MY_REPLY_COUNT,
   RECEIVED_COUNT, THREAD_MSG_COUNT, IS_HIGH_IMPORTANCE, IS_UNANSWERED,
   HOURS_WAITING. Order by HOURS_WAITING DESC.

7. Thread Summary - from GMAIL_ANALYTICS.ANALYTICS.VW_THREAD_SUMMARY with
   optional SUBJECT ILIKE filter. Include THREAD_ID, SUBJECT, CATEGORY,
   MESSAGE_COUNT, STARTED_AT, LAST_MESSAGE_AT, THREAD_DURATION_MINUTES,
   PARTICIPANT_COUNT, ATTACHMENT_COUNT, UNREAD_IN_THREAD,
   SUSPICIOUS_IN_THREAD, MAX_IMPORTANCE, PARTICIPANTS.

8. Alerts & Notifications - from
   GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS with optional
   ALERT_SOURCE filter. Include MESSAGE_ID, SUBJECT, SNIPPET, SENT_AT,
   CATEGORY, IMPORTANCE, SENDER_NAME, SENDER_EMAIL, CONTACT_TYPE,
   ALERT_SOURCE, ALERT_CATEGORY, ALERT_DATE, ALERT_WEEK, ALERT_MONTH,
   IS_READ.

9. Snowflake-Specific Alerts - from
   GMAIL_ANALYTICS.ANALYTICS.VW_SNOWFLAKE_ALERTS. Include MESSAGE_ID,
   SUBJECT, BODY_TEXT, SENT_AT, IMPORTANCE, ALERT_SOURCE, ALERT_EMAIL,
   ALERT_TYPE, ALERT_WEEK, ALERT_MONTH.

10. Label Distribution - from GMAIL_ANALYTICS.ANALYTICS.VW_LABEL_DISTRIBUTION.
    Include LABEL_ID, LABEL_NAME, LABEL_TYPE, COLOR, MESSAGE_COUNT,
    THREAD_COUNT, FIRST_APPLIED, LAST_APPLIED, PCT_OF_ALL_MESSAGES.

11. Availability & Scheduling Patterns - from
    GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS. Include MESSAGE_ID,
    SUBJECT, SNIPPET, SENT_AT, EMAIL_DATE, DAY_OF_WEEK, HOUR_OF_DAY,
    CATEGORY, SENDER_NAME, ACTIVITY_TYPE, TIME_BUCKET.

12. Raw Message Search (fallback) - JOIN EMAIL_MESSAGES with EMAIL_CONTACTS
    and EMAIL_THREADS for free-text search on SUBJECT/SNIPPET. Include
    sender details, thread context. Order by SENT_AT DESC with LIMIT.

13. Contact Lookup - from GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS filtered by
    EMAIL, DISPLAY_NAME, or DOMAIN ILIKE search.

14. Labels for a Message - JOIN EMAIL_MESSAGE_LABEL_MAP with EMAIL_LABELS
    filtered by MESSAGE_ID. Include LABEL_NAME, LABEL_TYPE, COLOR,
    APPLIED_AT.

### PHASE 3 - INSIGHT SYNTHESIS
After evidence collection, build a structured insight report using box-drawing
characters. The report must include:
- Header with analysis type and date period
- KEY METRICS section: Total Messages, Sent/Received, Unread, Suspicious,
  Active Threads, Unique Contacts
- TOP FINDINGS section: numbered list of 3 key findings
- RISK INDICATORS section: Phishing Attempts, Sensitive Exposure, High Spam

Also include sections for:
- TREND ANALYSIS: day-over-day or week-over-week changes
- ENGAGEMENT HOTSPOTS: top contacts/domains by frequency
- SECURITY POSTURE: phishing indicator breakdown, suspicious domains
- ACTION ITEMS: unanswered high-importance emails with hours waiting

### PHASE 4 - CATEGORIZED ANALYSIS
Classify analysis into exactly ONE of 8 categories:

| Category              | Code            | When to Use                                    |
|-----------------------|-----------------|------------------------------------------------|
| Inbox Overview        | INBOX_OVERVIEW  | General activity, volume, read/unread stats    |
| Contact Intelligence  | CONTACT_INTEL   | Engagement scores, top senders, domains        |
| Security Threat       | SECURITY_THREAT | Phishing, spam, suspicious, impersonation      |
| Data Exposure         | DATA_EXPOSURE   | PII detection, sensitive patterns, credentials |
| Attachment Risk       | ATTACHMENT_RISK | Large files, risky file types, trends          |
| Thread Analytics      | THREAD_ANALYTICS| Conversation depth, response patterns          |
| Operational Alerts    | OPS_ALERTS      | Snowflake/AWS/GitHub alert patterns            |
| Productivity Insight  | PRODUCTIVITY    | Availability, peak hours, unanswered backlog   |

Output a formatted analysis box with: Category, Period, Confidence
(HIGH/MEDIUM/LOW with percentage), Summary (2-3 sentences), Evidence
(numbered list with source), Related Signals (with probability percentages).

Confidence scoring rules:
- HIGH (80-100%): 3+ data points converge, clear pattern
- MEDIUM (50-79%): 2 data points, partial pattern
- LOW (0-49%): Single indicator, circumstantial

### PHASE 5 - RECOMMENDATIONS
Provide category-specific recommendation SQL templates:
- SECURITY_THREAT: Query phishing attempts with credential requests; list
  suspicious domains with counts and avg spam score
- DATA_EXPOSURE: Identify high-sensitivity emails with SSN, credit card,
  API key patterns
- PRODUCTIVITY: List urgent unanswered emails ordered by HOURS_WAITING
- OPS_ALERTS: Snowflake alert trend by type and week
- ATTACHMENT_RISK: Large or risky attachments (>10MB or Archive/Other types)
- CONTACT_INTEL: Contacts with high spam/suspicious signals

CRITICAL RULES:
- NEVER execute UPDATE, DELETE, or DROP on core tables without explicit
  user confirmation
- Always explain what each query returns before executing
- Warn about PII exposure when displaying BODY_TEXT content
- Mask sensitive patterns (SSN, credit card numbers) in any output

### PHASE 6 - INSIGHT LOGGING
First check if the EMAIL_ANALYSIS_LOG table exists in GMAIL_ANALYTICS.ANALYTICS.
If yes, INSERT the analysis results with all fields including:
ANALYSIS_TYPE, CATEGORY_CODE, QUERY_TEXT, TIME_WINDOW_START/END,
CONFIDENCE_LEVEL, CONFIDENCE_PERCENTAGE, KEY_FINDINGS (VARIANT),
METRICS_SNAPSHOT (VARIANT), RECOMMENDATIONS (VARIANT),
CONTACTS_ANALYZED, MESSAGES_ANALYZED.

### PHASE 7 - FOLLOW-UP & DRILL-DOWN
Include a follow-up questions table mapping user questions to actions:
- "Show me all emails from [contact]" -> Query 12 + Query 13
- "What labels does this have?" -> Query 14
- "Is this contact suspicious?" -> Query 2 + Query 3
- "Show the full thread" -> Query 7 then Query 12
- "What are my busiest hours?" -> Query 11 aggregated by HOUR_OF_DAY
- "Show Snowflake alerts this month" -> Query 9 filtered
- "Any sensitive data from [domain]?" -> Query 4 + Query 13
- "Biggest attachments?" -> Query 5 ordered by SIZE_BYTES DESC
- "Unanswered emails older than 48h?" -> Query 6 WHERE HOURS_WAITING > 48
- "Label breakdown" -> Query 10
- "Log this analysis" -> Trigger Phase 6
- "Compare this week vs last week" -> Query 1 for both periods, compute deltas

Include a 30-day trend analysis query grouping daily totals from
VW_EMAIL_ACTIVITY_DAILY.

### SECURITY REQUIREMENTS
Add these rules at the end of SKILL.md:
1. PII Protection: Never display full BODY_TEXT without user consent. Mask
   SSN patterns, credit card numbers, and API keys in output.
2. No Data Modification: NEVER execute INSERT, UPDATE, DELETE, DROP on core
   tables unless explicitly requested and confirmed by the user.
3. Sensitive Content Warning: When results contain SENSITIVITY_LEVEL = 'high',
   prepend output with a warning banner.
4. Minimal Exposure: Return SNIPPET over BODY_TEXT where possible.
5. Audit Readiness: Log analysis runs to EMAIL_ANALYSIS_LOG when available.

### ERROR HANDLING
If evidence queries fail, show a warning with possible causes:
1. Insufficient privileges on GMAIL_ANALYTICS database
2. View may not exist (check ANALYTICS schema)
3. No data matching the filter criteria
Then proceed with available evidence (partial analysis).

### CORE TABLE REFERENCE
Include a compact reference for all 6 core tables with column names, types,
PKs, and FK relationships:

EMAIL_MESSAGES (PK: MESSAGE_ID) - 30 columns including THREAD_ID (FK),
SENDER_CONTACT_ID (FK), TO/CC/BCC_CONTACT_IDS (JSON arrays), SUBJECT,
SNIPPET, BODY_TEXT, BODY_HTML, SENT_AT, RECEIVED_AT, boolean flags
(IS_READ, IS_STARRED, IS_DRAFT, IS_SENT, IS_TRASH, IS_SPAM,
HAS_ATTACHMENTS, IS_SUSPICIOUS), CATEGORY, IMPORTANCE, SPAM_SCORE,
PHISHING_INDICATORS (JSON), HEADERS (JSON), RAW_SIZE_BYTES.

EMAIL_THREADS (PK: THREAD_ID) - SUBJECT, CATEGORY (business|work|personal|
alerts|promotions|support|finance), STARTED_AT, LAST_MESSAGE_AT,
MESSAGE_COUNT, IS_MUTED.

EMAIL_CONTACTS (PK: CONTACT_ID) - EMAIL, DISPLAY_NAME, DOMAIN,
CONTACT_TYPE (personal|business|alert|promotion|support|finance|suspicious),
IS_INTERNAL.

EMAIL_LABELS (PK: LABEL_ID) - LABEL_NAME, LABEL_TYPE (system|user), COLOR,
VISIBILITY, GMAIL_LABEL_ID.

EMAIL_ATTACHMENTS (PK: ATTACHMENT_ID) - MESSAGE_ID (FK), FILENAME,
CONTENT_TYPE, SIZE_BYTES, IS_INLINE, GMAIL_ATTACHMENT_ID.

EMAIL_MESSAGE_LABEL_MAP (PK: MESSAGE_ID + LABEL_ID) - APPLIED_AT.

### KEY RELATIONSHIPS
- EMAIL_MESSAGES.THREAD_ID -> EMAIL_THREADS.THREAD_ID
- EMAIL_MESSAGES.SENDER_CONTACT_ID -> EMAIL_CONTACTS.CONTACT_ID
- EMAIL_MESSAGES.TO_CONTACT_IDS -> JSON array of EMAIL_CONTACTS.CONTACT_ID
- EMAIL_ATTACHMENTS.MESSAGE_ID -> EMAIL_MESSAGES.MESSAGE_ID
- EMAIL_MESSAGE_LABEL_MAP.MESSAGE_ID -> EMAIL_MESSAGES.MESSAGE_ID
- EMAIL_MESSAGE_LABEL_MAP.LABEL_ID -> EMAIL_LABELS.LABEL_ID

------------------------------------------------------------------------
FILE 2: AGENTS.md
------------------------------------------------------------------------
Create an AGENTS.md file with:
- A header "# Gmail Intelligence Hub - Agent Configuration"
- Description of the skill as an AI-powered Gmail intelligence agent
- Supported analysis types table (8 types): INBOX_OVERVIEW, CONTACT_INTEL,
  SECURITY_THREAT, DATA_EXPOSURE, ATTACHMENT_RISK, THREAD_ANALYTICS,
  OPS_ALERTS, PRODUCTIVITY
- List of Snowflake objects used:
  Core Tables (6): EMAIL_MESSAGES, EMAIL_THREADS, EMAIL_CONTACTS,
  EMAIL_LABELS, EMAIL_ATTACHMENTS, EMAIL_MESSAGE_LABEL_MAP
  Analytics Views (11): VW_EMAIL_ACTIVITY_DAILY, VW_CONTACT_ENGAGEMENT,
  VW_SUSPICIOUS_EMAIL_ANALYSIS, VW_SENSITIVE_DATA_DETECTION,
  VW_ATTACHMENT_ANALYTICS, VW_HIGH_IMPORTANCE_AND_UNANSWERED,
  VW_THREAD_SUMMARY, VW_ALERTS_AND_NOTIFICATIONS, VW_SNOWFLAKE_ALERTS,
  VW_LABEL_DISTRIBUTION, VW_AVAILABILITY_ANALYSIS
  Supporting Objects (9): EMAIL_ANALYSIS_LOG, ANALYSIS_CATEGORIES,
  V_SECURITY_DASHBOARD, V_PRODUCTIVITY_DASHBOARD, V_ENGAGEMENT_SCORED,
  CLASSIFY_SENSITIVITY, CALCULATE_ENGAGEMENT_SCORE, LOG_ANALYSIS,
  GET_INBOX_SUMMARY
- Prerequisites: Access to GMAIL_ANALYTICS database, a warehouse
- Example invocations:
  "Show me my inbox summary for this week"
  "Who are my top contacts by email volume?"
  "Are there any phishing or suspicious emails?"
  "Show sensitive data exposure in my inbox"
  "What Snowflake alerts did I get this month?"
  "Show unanswered high-priority emails"
  "Analyze my busiest email hours"
  "What are the biggest attachments I received?"
  "Show the thread with the most participants"
  "Label distribution breakdown"
  "Compare this week vs last week email volume"
  "Any suspicious emails from external domains?"
- Section on supporting database objects (reference gmail_intelligence_hub_setup.sql)

------------------------------------------------------------------------
FILE 3: gmail_intelligence_hub_setup.sql
------------------------------------------------------------------------
Create a SQL setup script that creates these Snowflake objects inside the
GMAIL_ANALYTICS.ANALYTICS schema:

1. SCHEMA GMAIL_ANALYTICS.ANALYTICS (IF NOT EXISTS)

2. EMAIL_ANALYSIS_LOG table with columns:
   - ANALYSIS_ID (VARCHAR(36) DEFAULT UUID_STRING()), CREATED_AT,
     ANALYZED_BY (DEFAULT CURRENT_USER()), ANALYZING_ROLE (DEFAULT
     CURRENT_ROLE())
   - ANALYSIS_TYPE, CATEGORY_CODE, QUERY_TEXT (VARCHAR(16777216))
   - TIME_WINDOW_START, TIME_WINDOW_END (TIMESTAMP_NTZ)
   - CONFIDENCE_LEVEL, CONFIDENCE_PERCENTAGE (NUMBER(5,2))
   - KEY_FINDINGS (VARIANT), METRICS_SNAPSHOT (VARIANT),
     RECOMMENDATIONS (VARIANT)
   - CONTACTS_ANALYZED, MESSAGES_ANALYZED, THREADS_ANALYZED (NUMBER)
   - SECURITY_SIGNALS (VARIANT), SENSITIVE_DATA_FLAGS (VARIANT)
   - EXECUTION_TIME_MS (NUMBER), RAW_EVIDENCE (VARIANT)

3. ANALYSIS_CATEGORIES reference table with 8 categories:
   INBOX_OVERVIEW, CONTACT_INTEL, SECURITY_THREAT, DATA_EXPOSURE,
   ATTACHMENT_RISK, THREAD_ANALYTICS, OPS_ALERTS, PRODUCTIVITY.
   Each with CATEGORY_CODE (PK), CATEGORY_NAME, DESCRIPTION,
   DEFAULT_SEVERITY, REQUIRES_PII_MASK (BOOLEAN), NOTIFICATION_TIER.
   Use MERGE for idempotency.

4. V_SECURITY_DASHBOARD view - joins VW_SUSPICIOUS_EMAIL_ANALYSIS with
   VW_SENSITIVE_DATA_DETECTION on MESSAGE_ID. Include all phishing
   indicators, sensitivity patterns, computed THREAT_LEVEL (CRITICAL/HIGH/
   MEDIUM/LOW based on REQUESTS_CREDENTIALS + SPAM_SCORE > 0.7, impersonation,
   suspicious links, spam score thresholds), and DATA_RISK_LEVEL.

5. V_PRODUCTIVITY_DASHBOARD view - joins VW_HIGH_IMPORTANCE_AND_UNANSWERED
   with VW_AVAILABILITY_ANALYSIS on MESSAGE_ID. Include importance flags,
   unanswered status, HOURS_WAITING, DAY_OF_WEEK, HOUR_OF_DAY,
   ACTIVITY_TYPE, TIME_BUCKET.

6. CLASSIFY_SENSITIVITY UDF (SQL) - takes 7 BOOLEAN parameters (HAS_SSN,
   HAS_CC, HAS_PASSWORD, HAS_BANK, HAS_API_KEY, HAS_CONFIDENTIAL,
   HAS_WIRE). Returns 'high' if SSN/CC/API_KEY, 'medium' if
   PASSWORD/BANK/WIRE, 'low' if CONFIDENTIAL, else 'none'.

7. CALCULATE_ENGAGEMENT_SCORE UDF (SQL) - takes MESSAGES_SENT, MESSAGES_READ,
   THREADS_PARTICIPATED, ACTIVE_SPAN_DAYS, SUSPICIOUS_MESSAGES (all NUMBER).
   Returns NUMBER(5,2) score 0-100 using weighted formula:
   (LEAST(MESSAGES_SENT,100)*0.3) + (read_rate*30) +
   (LEAST(THREADS,50)*0.4) + (span_bonus) - (SUSPICIOUS*10).
   Clamped with GREATEST(0, LEAST(100, ...)).

8. LOG_ANALYSIS stored procedure - takes 12 parameters (ANALYSIS_TYPE,
   CATEGORY_CODE, QUERY_TEXT, TIME_WINDOW_START/END, CONFIDENCE_LEVEL,
   CONFIDENCE_PERCENTAGE, KEY_FINDINGS, METRICS_SNAPSHOT, RECOMMENDATIONS,
   CONTACTS_ANALYZED, MESSAGES_ANALYZED). Generates UUID, inserts into
   EMAIL_ANALYSIS_LOG, returns the ANALYSIS_ID.

9. GET_INBOX_SUMMARY stored procedure - takes P_DAYS_BACK NUMBER (default 7).
   Returns VARIANT with OBJECT_CONSTRUCT containing period_days,
   total_messages, total_sent, total_received, total_unread,
   total_suspicious, total_starred, total_with_attachments, active_threads,
   unique_senders, busiest_day, busiest_day_count. Queries
   VW_EMAIL_ACTIVITY_DAILY.

10. V_ENGAGEMENT_SCORED view - wraps VW_CONTACT_ENGAGEMENT and adds
    computed ENGAGEMENT_SCORE column using CALCULATE_ENGAGEMENT_SCORE UDF.

Include commented-out GRANT examples for a DATA_ANALYST role and a
verification query at the end.

------------------------------------------------------------------------
IMPORTANT NOTES FOR THE BUILDER
------------------------------------------------------------------------
- The SKILL.md file is the core intelligence. It must be comprehensive
  enough that COCO can follow it autonomously during an analysis.
- All SQL templates in SKILL.md use {{placeholder}} syntax for dynamic values.
- The setup SQL must be idempotent (IF NOT EXISTS, MERGE, CREATE OR REPLACE).
- The skill directory structure must be:
  .snowflake/cortex/skills/Gmail_Intelligence_Hub/
    SKILL.md
    AGENTS.md
    gmail_intelligence_hub_setup.sql
- All output formatting in SKILL.md uses box-drawing characters for
  professional presentation.
- The skill must handle partial evidence gracefully (some queries may fail
  due to permissions or missing views).
- Core tables are READ-ONLY. Never modify EMAIL_MESSAGES, EMAIL_THREADS,
  EMAIL_CONTACTS, EMAIL_LABELS, EMAIL_ATTACHMENTS, or
  EMAIL_MESSAGE_LABEL_MAP without explicit user confirmation.

================================================================================
--- END OF PROMPT ---
================================================================================

WHAT THIS PROMPT PRODUCES:
--------------------------
When you paste the prompt above into Cortex Code, it will create:

1. SKILL.md        - The AI instruction set (7-phase analysis workflow
                      with 14 diagnostic SQL templates, insight synthesis
                      formatting, 8-category classification framework,
                      recommendation playbooks, insight logging, and
                      follow-up routing)

2. AGENTS.md       - Agent metadata (supported analysis types, prerequisites,
                      example invocations, system objects used)

3. Setup SQL       - 10 Snowflake objects (2 tables, 1 ref table with MERGE,
                      3 views, 2 UDFs, 2 stored procedures) in the
                      GMAIL_ANALYTICS.ANALYTICS schema

HOW TO USE AFTER CREATION:
--------------------------
1. Ensure the GMAIL_ANALYTICS database exists with CORE tables populated
   and ANALYTICS views created.
2. Run the setup SQL in a Snowflake worksheet to create supporting objects
   (logging table, reference data, dashboard views, UDFs, procedures).
3. In any Snowflake Workspace, invoke the skill with:
   @Gmail_Intelligence_Hub show me my inbox summary
   @Gmail_Intelligence_Hub any phishing emails this week?
   @Gmail_Intelligence_Hub who are my top contacts?
   @Gmail_Intelligence_Hub show sensitive data exposure
   @Gmail_Intelligence_Hub what Snowflake alerts did I get?
4. The skill will automatically gather evidence, synthesize insights,
   classify the analysis, and suggest recommendations.

CUSTOMIZATION TIPS:
-------------------
- Add more alert sources in VW_ALERTS_AND_NOTIFICATIONS for your environment
- Configure ANALYSIS_CATEGORIES severity levels for your team's priorities
- Adjust the engagement score formula in CALCULATE_ENGAGEMENT_SCORE UDF
- Add custom file type groups in VW_ATTACHMENT_ANALYTICS
- Extend the phishing indicators JSON structure for new threat patterns
- Customize the sensitivity detection regex in VW_SENSITIVE_DATA_DETECTION

DATABASE PREREQUISITES:
-----------------------
The GMAIL_ANALYTICS database must exist with:
- GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES (30 columns, PK: MESSAGE_ID)
- GMAIL_ANALYTICS.CORE.EMAIL_THREADS (8 columns, PK: THREAD_ID)
- GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS (8 columns, PK: CONTACT_ID)
- GMAIL_ANALYTICS.CORE.EMAIL_LABELS (7 columns, PK: LABEL_ID)
- GMAIL_ANALYTICS.CORE.EMAIL_ATTACHMENTS (8 columns, PK: ATTACHMENT_ID)
- GMAIL_ANALYTICS.CORE.EMAIL_MESSAGE_LABEL_MAP (3 columns, PK: MESSAGE_ID+LABEL_ID)
- 11 analytics views in GMAIL_ANALYTICS.ANALYTICS schema
