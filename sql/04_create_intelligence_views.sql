-- =============================================================================
-- Step 6: 6 intelligence views for 6 use cases
-- =============================================================================

-- Use Case 1: Alerts & Notifications
CREATE OR REPLACE VIEW GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS AS
SELECT
    m.MESSAGE_ID, m.SUBJECT, m.SNIPPET, m.SENT_AT, m.CATEGORY,
    m.IMPORTANCE, c.DISPLAY_NAME AS SENDER_NAME, c.EMAIL AS SENDER_EMAIL,
    CASE
        WHEN m.SUBJECT LIKE '%[Snowflake]%' OR c.EMAIL LIKE '%@snowflakecomputing.com' THEN 'Snowflake'
        WHEN m.SUBJECT LIKE '%[AWS]%' OR c.EMAIL LIKE '%@sns.amazonaws.com' THEN 'AWS'
        WHEN m.SUBJECT LIKE '%[GitHub]%' OR c.EMAIL LIKE '%@github.com' THEN 'GitHub'
        WHEN m.SUBJECT LIKE '%[Datadog]%' OR c.EMAIL LIKE '%@dtdg.co' THEN 'Datadog'
        WHEN m.SUBJECT LIKE '%[PagerDuty]%' OR c.EMAIL LIKE '%@pagerduty.com' THEN 'PagerDuty'
        WHEN c.EMAIL LIKE '%@google.com' THEN 'Google'
        WHEN c.EMAIL LIKE '%@atlassian.com' THEN 'Atlassian'
        WHEN c.EMAIL LIKE '%@slack.com' THEN 'Slack'
        WHEN c.EMAIL LIKE '%@grafana.net' THEN 'Grafana'
        WHEN c.CONTACT_TYPE = 'alert' THEN 'Other Alert'
        ELSE 'Notification'
    END AS ALERT_SOURCE,
    CASE
        WHEN m.SUBJECT LIKE '%credit%' OR m.SUBJECT LIKE '%quota%' THEN 'Billing/Credits'
        WHEN m.SUBJECT LIKE '%fail%' OR m.SUBJECT LIKE '%error%' THEN 'Failure'
        WHEN m.SUBJECT LIKE '%security%' OR m.SUBJECT LIKE '%login%' THEN 'Security'
        WHEN m.SUBJECT LIKE '%storage%' THEN 'Storage'
        WHEN m.SUBJECT LIKE '%performance%' THEN 'Performance'
        WHEN m.SUBJECT LIKE '%monitor%' THEN 'Resource Monitor'
        ELSE 'General'
    END AS ALERT_CATEGORY,
    SENT_AT::DATE AS ALERT_DATE,
    DATE_TRUNC('week', SENT_AT)::DATE AS ALERT_WEEK,
    DATE_TRUNC('month', SENT_AT)::DATE AS ALERT_MONTH,
    m.IS_READ
FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
WHERE m.CATEGORY = 'alerts' OR c.CONTACT_TYPE = 'alert'
   OR m.SUBJECT LIKE '%alert%' OR m.SUBJECT LIKE '%[%]%';

-- Use Case 2: High Importance + Unanswered
CREATE OR REPLACE VIEW GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED AS
WITH thread_responses AS (
    SELECT THREAD_ID,
        MAX(CASE WHEN IS_SENT THEN 1 ELSE 0 END) AS HAS_MY_REPLY,
        COUNT(CASE WHEN IS_SENT THEN 1 END) AS MY_REPLY_COUNT,
        COUNT(CASE WHEN NOT IS_SENT THEN 1 END) AS RECEIVED_COUNT,
        COUNT(*) AS THREAD_MSG_COUNT
    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES GROUP BY THREAD_ID
)
SELECT
    m.MESSAGE_ID, m.THREAD_ID, m.SUBJECT, m.SNIPPET, m.SENT_AT,
    m.CATEGORY, m.IMPORTANCE, m.IS_READ, m.IS_STARRED, m.IS_SENT,
    c.DISPLAY_NAME AS SENDER_NAME, c.EMAIL AS SENDER_EMAIL,
    tr.HAS_MY_REPLY, tr.MY_REPLY_COUNT, tr.RECEIVED_COUNT,
    CASE WHEN m.IMPORTANCE = 'high' OR m.IS_STARRED THEN TRUE ELSE FALSE END AS IS_HIGH_IMPORTANCE,
    CASE WHEN NOT m.IS_SENT AND tr.HAS_MY_REPLY = 0 THEN TRUE ELSE FALSE END AS IS_UNANSWERED,
    CASE WHEN NOT m.IS_SENT AND tr.HAS_MY_REPLY = 0 THEN
        DATEDIFF('hour', m.SENT_AT, CURRENT_TIMESTAMP()) ELSE NULL END AS HOURS_WAITING
FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
JOIN GMAIL_ANALYTICS.CORE.EMAIL_THREADS t ON m.THREAD_ID = t.THREAD_ID
JOIN thread_responses tr ON m.THREAD_ID = tr.THREAD_ID
WHERE m.IMPORTANCE = 'high' OR m.IS_STARRED = TRUE
   OR (NOT m.IS_SENT AND tr.HAS_MY_REPLY = 0);

-- Use Case 3: Sensitive Data Detection
CREATE OR REPLACE VIEW GMAIL_ANALYTICS.ANALYTICS.VW_SENSITIVE_DATA_DETECTION AS
SELECT
    m.MESSAGE_ID, m.SUBJECT, m.SNIPPET, m.SENT_AT, m.CATEGORY,
    c.DISPLAY_NAME AS SENDER_NAME, c.EMAIL AS SENDER_EMAIL,
    CASE WHEN m.BODY_TEXT ILIKE '%social security%' OR m.BODY_TEXT ILIKE '%SSN%' THEN TRUE ELSE FALSE END AS HAS_SSN_PATTERN,
    CASE WHEN REGEXP_LIKE(m.BODY_TEXT, '\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}') THEN TRUE ELSE FALSE END AS HAS_CREDIT_CARD_PATTERN,
    CASE WHEN m.BODY_TEXT ILIKE '%password%' OR m.BODY_TEXT ILIKE '%passwd%' THEN TRUE ELSE FALSE END AS HAS_PASSWORD_MENTION,
    CASE WHEN m.BODY_TEXT ILIKE '%bank account%' OR m.BODY_TEXT ILIKE '%IBAN%' THEN TRUE ELSE FALSE END AS HAS_BANK_INFO,
    CASE WHEN m.BODY_TEXT ILIKE '%api key%' OR m.BODY_TEXT ILIKE '%secret key%' OR m.BODY_TEXT ILIKE '%access token%' THEN TRUE ELSE FALSE END AS HAS_API_KEY_PATTERN,
    CASE WHEN m.BODY_TEXT ILIKE '%confidential%' OR m.BODY_TEXT ILIKE '%proprietary%' THEN TRUE ELSE FALSE END AS HAS_CONFIDENTIAL_MARKER,
    CASE WHEN m.BODY_TEXT ILIKE '%wire transfer%' THEN TRUE ELSE FALSE END AS HAS_WIRE_TRANSFER,
    m.IS_SUSPICIOUS, m.SPAM_SCORE,
    CASE
        WHEN m.BODY_TEXT ILIKE '%social security%' OR m.BODY_TEXT ILIKE '%bank account%' OR m.BODY_TEXT ILIKE '%wire transfer%' THEN 'Critical'
        WHEN m.BODY_TEXT ILIKE '%password%' OR m.BODY_TEXT ILIKE '%api key%' THEN 'High'
        WHEN m.BODY_TEXT ILIKE '%confidential%' THEN 'Medium'
        ELSE 'Low'
    END AS SENSITIVITY_LEVEL
FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
WHERE m.BODY_TEXT ILIKE '%social security%' OR m.BODY_TEXT ILIKE '%SSN%'
   OR m.BODY_TEXT ILIKE '%password%' OR m.BODY_TEXT ILIKE '%bank account%'
   OR m.BODY_TEXT ILIKE '%api key%' OR m.BODY_TEXT ILIKE '%secret key%'
   OR m.BODY_TEXT ILIKE '%confidential%' OR m.BODY_TEXT ILIKE '%wire transfer%';

-- Use Case 4: Availability Analysis
CREATE OR REPLACE VIEW GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS AS
SELECT
    m.MESSAGE_ID, m.SUBJECT, m.SENT_AT,
    m.SENT_AT::DATE AS EMAIL_DATE,
    DAYNAME(m.SENT_AT) AS DAY_OF_WEEK,
    HOUR(m.SENT_AT) AS HOUR_OF_DAY,
    m.CATEGORY,
    c.DISPLAY_NAME AS SENDER_NAME,
    CASE
        WHEN LOWER(m.SUBJECT) LIKE '%meeting%' OR LOWER(m.SUBJECT) LIKE '%1:1%' OR LOWER(m.SUBJECT) LIKE '%standup%' THEN 'Meeting'
        WHEN LOWER(m.SUBJECT) LIKE '%calendar%' OR LOWER(m.SUBJECT) LIKE '%invite%' THEN 'Calendar Event'
        WHEN LOWER(m.SUBJECT) LIKE '%deadline%' OR LOWER(m.SUBJECT) LIKE '%review%' THEN 'Deadline/Review'
        WHEN LOWER(m.SUBJECT) LIKE '%deploy%' OR LOWER(m.SUBJECT) LIKE '%on-call%' THEN 'Ops Commitment'
        ELSE 'General Activity'
    END AS ACTIVITY_TYPE,
    CASE
        WHEN m.SENT_AT::DATE = CURRENT_DATE() THEN 'Today'
        WHEN m.SENT_AT::DATE BETWEEN DATE_TRUNC('week', CURRENT_DATE()) AND DATEADD('day', 6, DATE_TRUNC('week', CURRENT_DATE())) THEN 'This Week'
        WHEN m.SENT_AT::DATE BETWEEN DATE_TRUNC('month', CURRENT_DATE()) AND LAST_DAY(CURRENT_DATE()) THEN 'This Month'
        ELSE 'Past'
    END AS TIME_BUCKET
FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID;


-- Use Case 5: -- Executive Summary generation
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(
    (SELECT LISTAGG(
        'Subject: ' || SUBJECT || '\nFrom: ' || c.DISPLAY_NAME
        || '\nSnippet: ' || LEFT(m.BODY_TEXT, 300), '\n---\n'
    ) WITHIN GROUP (ORDER BY m.SENT_AT DESC)
    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
    WHERE m.SENT_AT >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    AND m.CATEGORY IN ('business', 'work')
    LIMIT 50)
) AS EXECUTIVE_SUMMARY;

-- Action Item extraction using LLM
SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
    'Extract all action items, deadlines, and decisions as a numbered list:\n\n'
    || (SELECT LISTAGG(
        'Subject: ' || SUBJECT || '\nBody: ' || LEFT(m.BODY_TEXT, 300), '\n---\n'
    ) WITHIN GROUP (ORDER BY m.SENT_AT DESC)
    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
    WHERE m.SENT_AT >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    AND m.CATEGORY IN ('business', 'work')
    LIMIT 30)
) AS ACTION_ITEMS;


-- Use Case 6: Q&A on Past Discussions (Cortex AI)

-- Example: Ask about past decisions on a topic
SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
    'You are an email assistant. Answer based ONLY on the email context.
     Question: What were the key decisions about Data Pipeline Optimization?

     Email Context:
     ' || (SELECT LISTAGG(
        'Subject: ' || SUBJECT || '\nFrom: ' || c.DISPLAY_NAME
        || '\nDate: ' || TO_CHAR(m.SENT_AT, 'YYYY-MM-DD')
        || '\nBody: ' || LEFT(m.BODY_TEXT, 500), '\n---\n'
    ) WITHIN GROUP (ORDER BY m.SENT_AT DESC)
    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
    WHERE m.BODY_TEXT ILIKE '%pipeline%' OR m.SUBJECT ILIKE '%pipeline%'
    LIMIT 20)
) AS ANSWER;