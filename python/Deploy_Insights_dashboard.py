CREATE OR REPLACE PROCEDURE GMAIL_ANALYTICS.CORE.DEPLOY_INSIGHTS_DASHBOARD()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
EXECUTE AS CALLER
AS '
def main(session):
    code = """from snowflake.snowpark.context import get_active_session
import streamlit as st
import altair as alt
import pandas as pd

session = get_active_session()

st.title("Gmail Intelligence Hub")
st.caption("AI-powered email analytics solving 6 key business problems")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Alerts & Notifications",
    "2. High Priority & Unanswered",
    "3. Sensitive Data",
    "4. Availability",
    "5. Executive Summary (AI)",
    "6. Ask Your Emails (AI)"
])

with tab1:
    st.subheader("Alerts & Notifications Overview")

    summary = session.sql(''''''
        SELECT COUNT(*) AS TOTAL_ALERTS,
            COUNT(CASE WHEN NOT IS_READ THEN 1 END) AS UNREAD_ALERTS,
            COUNT(DISTINCT ALERT_SOURCE) AS SOURCES,
            COUNT(DISTINCT ALERT_CATEGORY) AS CATEGORIES
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS
    '''''').to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Alerts", f"{summary[''TOTAL_ALERTS''][0]:,}")
    c2.metric("Unread", f"{summary[''UNREAD_ALERTS''][0]:,}")
    c3.metric("Sources", f"{summary[''SOURCES''][0]}")
    c4.metric("Categories", f"{summary[''CATEGORIES''][0]}")

    left, right = st.columns(2)
    with left:
        st.subheader("By Source")
        src = session.sql(''''''
            SELECT ALERT_SOURCE, COUNT(*) AS COUNT
            FROM GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS
            GROUP BY ALERT_SOURCE ORDER BY COUNT DESC
        '''''').to_pandas()
        st.bar_chart(src, x="ALERT_SOURCE", y="COUNT")

    with right:
        st.subheader("By Category")
        cat = session.sql(''''''
            SELECT ALERT_CATEGORY, COUNT(*) AS COUNT
            FROM GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS
            GROUP BY ALERT_CATEGORY ORDER BY COUNT DESC
        '''''').to_pandas()
        st.bar_chart(cat, x="ALERT_CATEGORY", y="COUNT")

    st.subheader("Alert Timeline")
    trend = session.sql(''''''
        SELECT ALERT_MONTH AS MONTH, ALERT_SOURCE, COUNT(*) AS ALERTS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS
        GROUP BY MONTH, ALERT_SOURCE ORDER BY MONTH
    '''''').to_pandas()
    line = alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X(''MONTH:T'', title=''Month''),
        y=alt.Y(''ALERTS:Q'', title=''Count''),
        color=''ALERT_SOURCE:N''
    ).properties(height=300)
    st.altair_chart(line, use_container_width=True)

    st.subheader("Recent Alerts")
    recent = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI'') AS SENT,
            ALERT_SOURCE, ALERT_CATEGORY, SUBJECT
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_ALERTS_AND_NOTIFICATIONS
        ORDER BY SENT_AT DESC LIMIT 20
    '''''').to_pandas()
    st.dataframe(recent, use_container_width=True)

with tab2:
    st.subheader("High Importance & Unanswered Emails")

    stats = session.sql(''''''
        SELECT
            COUNT(CASE WHEN IS_HIGH_IMPORTANCE THEN 1 END) AS HIGH_IMP,
            COUNT(CASE WHEN IS_UNANSWERED THEN 1 END) AS UNANSWERED,
            COUNT(CASE WHEN IS_HIGH_IMPORTANCE AND IS_UNANSWERED THEN 1 END) AS HIGH_AND_UNANSWERED,
            COUNT(CASE WHEN IS_UNANSWERED AND NOT IS_READ THEN 1 END) AS UNREAD_UNANSWERED
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED
    '''''').to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("High Importance", f"{stats[''HIGH_IMP''][0]:,}")
    c2.metric("Unanswered", f"{stats[''UNANSWERED''][0]:,}")
    c3.metric("High + Unanswered", f"{stats[''HIGH_AND_UNANSWERED''][0]:,}")
    c4.metric("Unread + Unanswered", f"{stats[''UNREAD_UNANSWERED''][0]:,}")

    st.subheader("Unanswered by Category")
    ucat = session.sql(''''''
        SELECT CATEGORY, COUNT(*) AS COUNT
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED
        WHERE IS_UNANSWERED = TRUE
        GROUP BY CATEGORY ORDER BY COUNT DESC
    '''''').to_pandas()
    st.bar_chart(ucat, x="CATEGORY", y="COUNT")

    st.subheader("Longest Waiting (Unanswered)")
    waiting = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI'') AS RECEIVED,
            SUBJECT, SENDER_NAME, CATEGORY,
            ROUND(HOURS_WAITING / 24, 1) AS DAYS_WAITING
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED
        WHERE IS_UNANSWERED = TRUE AND HOURS_WAITING IS NOT NULL
        ORDER BY HOURS_WAITING DESC LIMIT 20
    '''''').to_pandas()
    st.dataframe(waiting, use_container_width=True)

    st.subheader("High Importance Emails")
    himp = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI'') AS SENT,
            SUBJECT, SENDER_NAME, IMPORTANCE,
            CASE WHEN IS_READ THEN ''Read'' ELSE ''Unread'' END AS STATUS,
            CASE WHEN IS_UNANSWERED THEN ''No'' ELSE ''Yes'' END AS RESPONDED
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_HIGH_IMPORTANCE_AND_UNANSWERED
        WHERE IS_HIGH_IMPORTANCE = TRUE
        ORDER BY SENT_AT DESC LIMIT 20
    '''''').to_pandas()
    st.dataframe(himp, use_container_width=True)

with tab3:
    st.subheader("Sensitive Data Detection")

    sens = session.sql(''''''
        SELECT COUNT(*) AS TOTAL,
            COUNT(CASE WHEN SENSITIVITY_LEVEL = ''Critical'' THEN 1 END) AS CRITICAL,
            COUNT(CASE WHEN SENSITIVITY_LEVEL = ''High'' THEN 1 END) AS HIGH_SENS,
            COUNT(CASE WHEN SENSITIVITY_LEVEL = ''Medium'' THEN 1 END) AS MEDIUM_SENS,
            COUNT(CASE WHEN HAS_WIRE_TRANSFER THEN 1 END) AS WIRE_TRANSFERS,
            COUNT(CASE WHEN HAS_BANK_INFO THEN 1 END) AS BANK_INFO_EMAILS,
            COUNT(CASE WHEN HAS_PASSWORD_MENTION THEN 1 END) AS PWD_MENTIONS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SENSITIVE_DATA_DETECTION
    '''''').to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Flagged", f"{sens[''TOTAL''][0]:,}")
    c2.metric("Critical", f"{sens[''CRITICAL''][0]:,}")
    c3.metric("High", f"{sens[''HIGH_SENS''][0]:,}")
    c4.metric("Wire Transfers", f"{sens[''WIRE_TRANSFERS''][0]:,}")

    st.subheader("Sensitive Data Types Found")
    types_data = session.sql(''''''
        SELECT
            COUNT(CASE WHEN HAS_SSN_PATTERN THEN 1 END) AS SSN,
            COUNT(CASE WHEN HAS_CREDIT_CARD_PATTERN THEN 1 END) AS CREDIT_CARD,
            COUNT(CASE WHEN HAS_PASSWORD_MENTION THEN 1 END) AS PASSWORDS,
            COUNT(CASE WHEN HAS_BANK_INFO THEN 1 END) AS BANK_INFO,
            COUNT(CASE WHEN HAS_API_KEY_PATTERN THEN 1 END) AS API_KEYS,
            COUNT(CASE WHEN HAS_CONFIDENTIAL_MARKER THEN 1 END) AS CONFIDENTIAL,
            COUNT(CASE WHEN HAS_WIRE_TRANSFER THEN 1 END) AS WIRE_TRANSFER
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SENSITIVE_DATA_DETECTION
    '''''').to_pandas()
    tdf = pd.DataFrame({
        ''Type'': [''SSN'', ''Credit Card'', ''Passwords'', ''Bank Info'', ''API Keys'', ''Confidential'', ''Wire Transfer''],
        ''Count'': [int(types_data[''SSN''][0]), int(types_data[''CREDIT_CARD''][0]),
                  int(types_data[''PASSWORDS''][0]), int(types_data[''BANK_INFO''][0]),
                  int(types_data[''API_KEYS''][0]), int(types_data[''CONFIDENTIAL''][0]),
                  int(types_data[''WIRE_TRANSFER''][0])]
    })
    st.bar_chart(tdf, x=''Type'', y=''Count'')

    st.subheader("Flagged Emails")
    flagged = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI'') AS SENT,
            SUBJECT, SENDER_NAME, SENSITIVITY_LEVEL,
            CASE WHEN IS_SUSPICIOUS THEN ''Yes'' ELSE ''No'' END AS SUSPICIOUS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SENSITIVE_DATA_DETECTION
        ORDER BY SENT_AT DESC LIMIT 20
    '''''').to_pandas()
    st.dataframe(flagged, use_container_width=True)

with tab4:
    st.subheader("Availability Analysis")

    period = st.selectbox("Time Period", ["Today", "This Week", "This Month", "All Time"])

    if period == "All Time":
        where_clause = "1=1"
    else:
        where_clause = f"TIME_BUCKET = ''{period}''"

    avail_stats = session.sql(f''''''
        SELECT
            COUNT(*) AS TOTAL_EMAILS,
            COUNT(CASE WHEN ACTIVITY_TYPE = ''Meeting'' THEN 1 END) AS MEETINGS,
            COUNT(CASE WHEN ACTIVITY_TYPE = ''Calendar Event'' THEN 1 END) AS EVENTS,
            COUNT(CASE WHEN ACTIVITY_TYPE = ''Deadline/Review'' THEN 1 END) AS DEADLINES,
            COUNT(CASE WHEN ACTIVITY_TYPE = ''Ops Commitment'' THEN 1 END) AS OPS,
            COUNT(DISTINCT EMAIL_DATE) AS ACTIVE_DAYS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS
        WHERE {where_clause}
    '''''').to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emails", f"{avail_stats[''TOTAL_EMAILS''][0]:,}")
    c2.metric("Meetings", f"{avail_stats[''MEETINGS''][0]:,}")
    c3.metric("Calendar Events", f"{avail_stats[''EVENTS''][0]:,}")
    c4.metric("Deadlines", f"{avail_stats[''DEADLINES''][0]:,}")

    st.subheader("Activity by Type")
    act_type = session.sql(f''''''
        SELECT ACTIVITY_TYPE, COUNT(*) AS COUNT
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS
        WHERE {where_clause}
        GROUP BY ACTIVITY_TYPE ORDER BY COUNT DESC
    '''''').to_pandas()
    st.bar_chart(act_type, x="ACTIVITY_TYPE", y="COUNT")

    st.subheader("Hourly Activity Pattern")
    hourly = session.sql(f''''''
        SELECT HOUR_OF_DAY, COUNT(*) AS EMAILS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS
        WHERE {where_clause}
        GROUP BY HOUR_OF_DAY ORDER BY HOUR_OF_DAY
    '''''').to_pandas()
    st.bar_chart(hourly, x="HOUR_OF_DAY", y="EMAILS")

    st.subheader("Busiest Days")
    daily = session.sql(f''''''
        SELECT DAY_OF_WEEK, COUNT(*) AS EMAILS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_AVAILABILITY_ANALYSIS
        WHERE {where_clause}
        GROUP BY DAY_OF_WEEK ORDER BY EMAILS DESC
    '''''').to_pandas()
    st.bar_chart(daily, x="DAY_OF_WEEK", y="EMAILS")

with tab5:
    st.subheader("Executive Summary (Cortex AI)")
    st.caption("Uses Snowflake Cortex AI to summarize your emails by time period")

    period5 = st.selectbox("Summarize Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Month"], key="sum_period")

    if period5 == "Last 7 Days":
        days_back = 7
    elif period5 == "Last 30 Days":
        days_back = 30
    elif period5 == "Last 90 Days":
        days_back = 90
    else:
        days_back = 30

    cat_filter = st.multiselect("Filter Categories", ["business", "work", "personal", "alerts", "support", "finance", "promotions"],
        default=["business", "work"], key="sum_cats")

    if st.button("Generate Executive Summary", key="gen_summary"):
        with st.spinner("Cortex AI is analyzing your emails..."):
            cats = "'',''".join(cat_filter)
            summary_df = session.sql(f''''''
                SELECT SNOWFLAKE.CORTEX.SUMMARIZE(
                    (SELECT LISTAGG(
                        ''Subject: '' || SUBJECT || ''\\\\nFrom: '' || c.DISPLAY_NAME || ''\\\\nDate: '' || TO_CHAR(m.SENT_AT, ''YYYY-MM-DD'') || ''\\\\nSnippet: '' || LEFT(m.BODY_TEXT, 300),
                        ''\\\\n---\\\\n''
                    ) WITHIN GROUP (ORDER BY m.SENT_AT DESC)
                    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
                    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
                    WHERE m.SENT_AT >= DATEADD(''day'', -{days_back}, CURRENT_TIMESTAMP())
                    AND m.CATEGORY IN (''{cats}'')
                    LIMIT 50)
                ) AS EXEC_SUMMARY
            '''''').to_pandas()
            st.markdown("### Summary")
            st.write(summary_df[''EXEC_SUMMARY''][0])

    st.divider()
    st.subheader("Action Items Extraction")
    if st.button("Extract Action Items", key="gen_actions"):
        with st.spinner("Extracting action items..."):
            cats = "'',''".join(cat_filter)
            actions = session.sql(f''''''
                SELECT SNOWFLAKE.CORTEX.COMPLETE(''mistral-large2'',
                    ''You are an executive assistant. Extract all action items, deadlines, and decisions from these emails. Format as a numbered list with owner and due date if mentioned.\\\\n\\\\nEmails:\\\\n'' ||
                    (SELECT LISTAGG(
                        ''Subject: '' || SUBJECT || ''\\\\nFrom: '' || c.DISPLAY_NAME || ''\\\\nBody: '' || LEFT(m.BODY_TEXT, 300),
                        ''\\\\n---\\\\n''
                    ) WITHIN GROUP (ORDER BY m.SENT_AT DESC)
                    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
                    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
                    WHERE m.SENT_AT >= DATEADD(''day'', -{days_back}, CURRENT_TIMESTAMP())
                    AND m.CATEGORY IN (''{cats}'')
                    LIMIT 30)
                ) AS ACTION_ITEMS
            '''''').to_pandas()
            st.markdown("### Action Items")
            st.write(actions[''ACTION_ITEMS''][0])

with tab6:
    st.subheader("Ask Your Emails (Cortex AI)")
    st.caption("Ask questions about past discussions, decisions, and email content")

    question = st.text_input("Ask a question about your emails:", placeholder="e.g., What were the key decisions about Data Pipeline Optimization?")

    col1, col2 = st.columns(2)
    with col1:
        search_cats = st.multiselect("Search in categories",
            ["business","work","personal","alerts","support","finance","promotions"],
            default=["business","work","support"], key="qa_cats")
    with col2:
        search_days = st.selectbox("Time range", [30, 60, 90, 180, 365], index=4, key="qa_days")

    if st.button("Ask", key="ask_btn") and question:
        with st.spinner("Searching and analyzing emails..."):
            cats = "'',''".join(search_cats)

            relevant = session.sql(f''''''
                SELECT m.SUBJECT, c.DISPLAY_NAME AS SENDER,
                    TO_CHAR(m.SENT_AT, ''YYYY-MM-DD'') AS SENT_DATE,
                    LEFT(m.BODY_TEXT, 500) AS BODY_PREVIEW
                FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
                JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
                WHERE m.SENT_AT >= DATEADD(''day'', -{search_days}, CURRENT_TIMESTAMP())
                AND m.CATEGORY IN (''{cats}'')
                AND (m.SUBJECT ILIKE ''%'' || ''{question.split()[0] if question else ""}'' || ''%''
                     OR m.BODY_TEXT ILIKE ''%'' || ''{question.split()[0] if question else ""}'' || ''%'')
                ORDER BY m.SENT_AT DESC
                LIMIT 20
            '''''').to_pandas()

            if len(relevant) == 0:
                relevant = session.sql(f''''''
                    SELECT m.SUBJECT, c.DISPLAY_NAME AS SENDER,
                        TO_CHAR(m.SENT_AT, ''YYYY-MM-DD'') AS SENT_DATE,
                        LEFT(m.BODY_TEXT, 500) AS BODY_PREVIEW
                    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES m
                    JOIN GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS c ON m.SENDER_CONTACT_ID = c.CONTACT_ID
                    WHERE m.SENT_AT >= DATEADD(''day'', -{search_days}, CURRENT_TIMESTAMP())
                    AND m.CATEGORY IN (''{cats}'')
                    ORDER BY m.SENT_AT DESC
                    LIMIT 20
                '''''').to_pandas()

            email_context = ""
            for _, row in relevant.iterrows():
                email_context += f"Subject: {row[''SUBJECT'']}\\\\nFrom: {row[''SENDER'']}\\\\nDate: {row[''SENT_DATE'']}\\\\nBody: {row[''BODY_PREVIEW'']}\\\\n---\\\\n"

            answer = session.sql(f''''''
                SELECT SNOWFLAKE.CORTEX.COMPLETE(''mistral-large2'',
                    ''You are an intelligent email assistant. Answer the following question based ONLY on the email context provided. If the answer is not in the emails, say so.\\\\n\\\\nQuestion: {question}\\\\n\\\\nEmail Context:\\\\n{email_context}''
                ) AS ANSWER
            '''''').to_pandas()

            st.markdown("### Answer")
            st.write(answer[''ANSWER''][0])

            with st.expander("Source Emails Referenced"):
                st.dataframe(relevant[[''SENT_DATE'',''SENDER'',''SUBJECT'']], use_container_width=True)
"""

    with open(''/tmp/insights_app.py'', ''w'') as f:
        f.write(code)

    session.file.put(''/tmp/insights_app.py'', ''@GMAIL_ANALYTICS.CORE.STREAMLIT_STAGE'',
        auto_compress=False, overwrite=True)

    return "Insights dashboard deployed"
';