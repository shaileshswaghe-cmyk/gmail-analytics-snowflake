CREATE OR REPLACE PROCEDURE GMAIL_ANALYTICS.CORE.DEPLOY_STREAMLIT_DASHBOARD()
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

st.title("Gmail Analytics Dashboard")
st.caption("Email intelligence across 1,100+ messages | 230 threads | 320 contacts | 12 months of synthetic data")

kpis = session.sql(''''''
    SELECT
        COUNT(*) AS MESSAGES,
        COUNT(DISTINCT THREAD_ID) AS THREADS,
        COUNT(CASE WHEN IS_SUSPICIOUS THEN 1 END) AS SUSPICIOUS,
        COUNT(CASE WHEN NOT IS_READ THEN 1 END) AS UNREAD,
        COUNT(CASE WHEN HAS_ATTACHMENTS THEN 1 END) AS WITH_ATT,
        COUNT(CASE WHEN SUBJECT LIKE ''%[Snowflake]%'' THEN 1 END) AS SF_ALERTS
    FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES
'''''').to_pandas()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Messages", f"{kpis[''MESSAGES''][0]:,}")
c2.metric("Threads", f"{kpis[''THREADS''][0]:,}")
c3.metric("Unread", f"{kpis[''UNREAD''][0]:,}")
c4.metric("Attachments", f"{kpis[''WITH_ATT''][0]:,}")
c5.metric("Suspicious", f"{kpis[''SUSPICIOUS''][0]:,}")
c6.metric("SF Alerts", f"{kpis[''SF_ALERTS''][0]:,}")

st.divider()

overview, threats, ops, contacts_tab, attach_tab, labels_tab = st.tabs([
    "Overview",
    "Threat Detection",
    "Snowflake Ops",
    "Contacts",
    "Attachments",
    "Labels"
])

with overview:
    monthly = session.sql(''''''
        SELECT DATE_TRUNC(''month'', SENT_AT)::DATE AS MONTH, CATEGORY, COUNT(*) AS MESSAGES
        FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES GROUP BY MONTH, CATEGORY ORDER BY MONTH
    '''''').to_pandas()

    st.subheader("Monthly volume by category")
    chart = alt.Chart(monthly).mark_bar().encode(
        x=alt.X(''MONTH:T'', title=''Month''),
        y=alt.Y(''MESSAGES:Q'', title=''Messages'', stack=''zero''),
        color=alt.Color(''CATEGORY:N'', scale=alt.Scale(scheme=''tableau10''))
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Messages by category")
        cat = session.sql(''''''
            SELECT CATEGORY, COUNT(*) AS COUNT
            FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES GROUP BY CATEGORY ORDER BY COUNT DESC
        '''''').to_pandas()
        st.bar_chart(cat, x="CATEGORY", y="COUNT")

    with right:
        st.subheader("Read rate by category (%)")
        rr = session.sql(''''''
            SELECT CATEGORY,
                ROUND(COUNT(CASE WHEN IS_READ THEN 1 END)*100.0/COUNT(*),1) AS READ_RATE
            FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES GROUP BY CATEGORY ORDER BY READ_RATE DESC
        '''''').to_pandas()
        st.bar_chart(rr, x="CATEGORY", y="READ_RATE")

    st.subheader("Activity heatmap (day x hour)")
    hm = session.sql(''''''
        SELECT DAYNAME(SENT_AT) AS DOW, HOUR(SENT_AT) AS HOUR, COUNT(*) AS EMAILS
        FROM GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES GROUP BY DOW, HOUR
    '''''').to_pandas()
    heat = alt.Chart(hm).mark_rect().encode(
        x=alt.X(''HOUR:O'', title=''Hour of day''),
        y=alt.Y(''DOW:N'', title=''Day'', sort=[''Mon'',''Tue'',''Wed'',''Thu'',''Fri'',''Sat'',''Sun'']),
        color=alt.Color(''EMAILS:Q'', scale=alt.Scale(scheme=''blues''))
    ).properties(height=220)
    st.altair_chart(heat, use_container_width=True)

with threats:
    st.subheader("Suspicious domains")
    sus = session.sql(''''''
        SELECT SENDER_DOMAIN, COUNT(*) AS COUNT,
            ROUND(AVG(SPAM_SCORE),3) AS AVG_SPAM,
            COUNT(CASE WHEN HAS_URGENCY THEN 1 END) AS URGENCY,
            COUNT(CASE WHEN HAS_SUSPICIOUS_LINKS THEN 1 END) AS SUS_LINKS,
            COUNT(CASE WHEN REQUESTS_CREDENTIALS THEN 1 END) AS CRED_REQ,
            COUNT(CASE WHEN HAS_IMPERSONATION THEN 1 END) AS IMPERSONATION
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SUSPICIOUS_EMAIL_ANALYSIS
        GROUP BY SENDER_DOMAIN ORDER BY COUNT DESC
    '''''').to_pandas()
    st.dataframe(sus, use_container_width=True)

    st.subheader("Latest suspicious emails")
    latest = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI:SS'') AS SENT, SUBJECT, SENDER_EMAIL,
            ROUND(SPAM_SCORE,3) AS SPAM_SCORE
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SUSPICIOUS_EMAIL_ANALYSIS
        ORDER BY SENT_AT DESC LIMIT 15
    '''''').to_pandas()
    st.dataframe(latest, use_container_width=True)

    st.subheader("Phishing tactic distribution")
    tactics = session.sql(''''''
        SELECT
            COUNT(CASE WHEN HAS_URGENCY THEN 1 END) AS URGENCY,
            COUNT(CASE WHEN HAS_SUSPICIOUS_LINKS THEN 1 END) AS SUSPICIOUS_LINKS,
            COUNT(CASE WHEN REQUESTS_CREDENTIALS THEN 1 END) AS CREDENTIAL_REQUESTS,
            COUNT(CASE WHEN HAS_IMPERSONATION THEN 1 END) AS IMPERSONATION
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SUSPICIOUS_EMAIL_ANALYSIS
    '''''').to_pandas()
    tdf = pd.DataFrame({
        ''Tactic'': [''Urgency'', ''Suspicious links'', ''Credential requests'', ''Impersonation''],
        ''Count'': [int(tactics[''URGENCY''][0]), int(tactics[''SUSPICIOUS_LINKS''][0]),
                  int(tactics[''CREDENTIAL_REQUESTS''][0]), int(tactics[''IMPERSONATION''][0])]
    })
    st.bar_chart(tdf, x=''Tactic'', y=''Count'')

with ops:
    st.subheader("Snowflake alert summary by type")
    asum = session.sql(''''''
        SELECT ALERT_TYPE, COUNT(*) AS ALERTS,
            TO_CHAR(MIN(SENT_AT), ''YYYY-MM-DD'') AS FIRST_SEEN,
            TO_CHAR(MAX(SENT_AT), ''YYYY-MM-DD'') AS LAST_SEEN,
            COUNT(DISTINCT DATE_TRUNC(''week'', SENT_AT)::DATE) AS WEEKS_ACTIVE
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SNOWFLAKE_ALERTS
        GROUP BY ALERT_TYPE ORDER BY ALERTS DESC
    '''''').to_pandas()
    st.dataframe(asum, use_container_width=True)

    st.subheader("Alert trend over time")
    atrend = session.sql(''''''
        SELECT DATE_TRUNC(''month'', SENT_AT)::DATE AS MONTH, ALERT_TYPE, COUNT(*) AS ALERTS
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SNOWFLAKE_ALERTS
        GROUP BY MONTH, ALERT_TYPE ORDER BY MONTH
    '''''').to_pandas()
    line = alt.Chart(atrend).mark_line(point=True).encode(
        x=alt.X(''MONTH:T'', title=''Month''),
        y=alt.Y(''ALERTS:Q'', title=''Alerts''),
        color=alt.Color(''ALERT_TYPE:N'', title=''Type'')
    ).properties(height=350)
    st.altair_chart(line, use_container_width=True)

    st.subheader("Recent Snowflake alerts")
    recent_alerts = session.sql(''''''
        SELECT TO_CHAR(SENT_AT, ''YYYY-MM-DD HH24:MI:SS'') AS SENT, ALERT_TYPE, SUBJECT
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_SNOWFLAKE_ALERTS
        ORDER BY SENT_AT DESC LIMIT 15
    '''''').to_pandas()
    st.dataframe(recent_alerts, use_container_width=True)

with contacts_tab:
    st.subheader("Top 20 senders by volume")
    top = session.sql(''''''
        SELECT DISPLAY_NAME, EMAIL, CONTACT_TYPE, MESSAGES_SENT, THREADS_PARTICIPATED
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_CONTACT_ENGAGEMENT
        WHERE MESSAGES_SENT > 0 ORDER BY MESSAGES_SENT DESC LIMIT 20
    '''''').to_pandas()
    st.dataframe(top, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Contacts by type")
        ct = session.sql(''''''
            SELECT CONTACT_TYPE, COUNT(*) AS COUNT
            FROM GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS GROUP BY CONTACT_TYPE ORDER BY COUNT DESC
        '''''').to_pandas()
        st.bar_chart(ct, x="CONTACT_TYPE", y="COUNT")
    with right:
        st.subheader("Top 10 domains")
        dom = session.sql(''''''
            SELECT DOMAIN, COUNT(*) AS COUNT
            FROM GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS GROUP BY DOMAIN ORDER BY COUNT DESC LIMIT 10
        '''''').to_pandas()
        st.bar_chart(dom, x="DOMAIN", y="COUNT")

with attach_tab:
    st.subheader("File type summary")
    ft = session.sql(''''''
        SELECT FILE_TYPE_GROUP, COUNT(*) AS FILES,
            ROUND(SUM(SIZE_MB),1) AS TOTAL_MB, ROUND(AVG(SIZE_MB),2) AS AVG_MB
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_ATTACHMENT_ANALYTICS
        GROUP BY FILE_TYPE_GROUP ORDER BY TOTAL_MB DESC
    '''''').to_pandas()
    st.dataframe(ft, use_container_width=True)

    st.subheader("Attachments by category")
    ac = session.sql(''''''
        SELECT CATEGORY, FILE_TYPE_GROUP, COUNT(*) AS COUNT
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_ATTACHMENT_ANALYTICS
        GROUP BY CATEGORY, FILE_TYPE_GROUP ORDER BY COUNT DESC
    '''''').to_pandas()
    stacked = alt.Chart(ac).mark_bar().encode(
        x=alt.X(''CATEGORY:N'', title=''Category''),
        y=alt.Y(''COUNT:Q'', title=''Files'', stack=''zero''),
        color=alt.Color(''FILE_TYPE_GROUP:N'', title=''File type'')
    ).properties(height=350)
    st.altair_chart(stacked, use_container_width=True)

with labels_tab:
    st.subheader("Label usage")
    lbl = session.sql(''''''
        SELECT LABEL_NAME, LABEL_TYPE, MESSAGE_COUNT, THREAD_COUNT,
            ROUND(PCT_OF_ALL_MESSAGES, 1) AS PCT_OF_MESSAGES
        FROM GMAIL_ANALYTICS.ANALYTICS.VW_LABEL_DISTRIBUTION
        WHERE MESSAGE_COUNT > 0
        ORDER BY MESSAGE_COUNT DESC
    '''''').to_pandas()
    st.dataframe(lbl, use_container_width=True)

    st.subheader("System vs user labels")
    left, right = st.columns(2)
    with left:
        sys_lbl = lbl[lbl[''LABEL_TYPE''] == ''system''].head(10)
        st.bar_chart(sys_lbl, x="LABEL_NAME", y="MESSAGE_COUNT")
        st.caption("System labels")
    with right:
        usr_lbl = lbl[lbl[''LABEL_TYPE''] == ''user'']
        st.bar_chart(usr_lbl, x="LABEL_NAME", y="MESSAGE_COUNT")
        st.caption("User labels")
"""

    with open(''/tmp/streamlit_app.py'', ''w'') as f:
        f.write(code)

    session.file.put(''/tmp/streamlit_app.py'', ''@GMAIL_ANALYTICS.CORE.STREAMLIT_STAGE'',
        auto_compress=False, overwrite=True)

    return "Fixed dashboard deployed"
';