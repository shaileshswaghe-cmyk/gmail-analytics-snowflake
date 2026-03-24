-- =============================================================================
-- Step 2: Create 6 normalized tables
-- All tables include Gmail API-compatible fields for future direct ingestion.
-- =============================================================================

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS (
    CONTACT_ID        NUMBER PRIMARY KEY,
    EMAIL             VARCHAR(255) NOT NULL,
    DISPLAY_NAME      VARCHAR(255),
    DOMAIN            VARCHAR(255),
    CONTACT_TYPE      VARCHAR(50) COMMENT 'personal, business, alert, promotion, support, finance, suspicious',
    IS_INTERNAL       BOOLEAN DEFAULT FALSE,
    CREATED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Contact directory. Maps to Gmail API People resource.';

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_THREADS (
    THREAD_ID         NUMBER PRIMARY KEY,
    SUBJECT           VARCHAR(1000),
    CATEGORY          VARCHAR(100) COMMENT 'business, work, personal, alerts, promotions, support, finance',
    STARTED_AT        TIMESTAMP_NTZ,
    LAST_MESSAGE_AT   TIMESTAMP_NTZ,
    MESSAGE_COUNT     NUMBER DEFAULT 0,
    IS_MUTED          BOOLEAN DEFAULT FALSE,
    CREATED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Conversation threads. Maps to Gmail API threads resource.';

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_LABELS (
    LABEL_ID          NUMBER PRIMARY KEY,
    LABEL_NAME        VARCHAR(255) NOT NULL,
    LABEL_TYPE        VARCHAR(50) COMMENT 'system or user',
    COLOR             VARCHAR(50),
    VISIBILITY        VARCHAR(50) DEFAULT 'show',
    GMAIL_LABEL_ID    VARCHAR(255) COMMENT 'Gmail API label ID',
    CREATED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Gmail labels. Maps to Gmail API labels resource.';

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES (
    MESSAGE_ID            NUMBER PRIMARY KEY,
    THREAD_ID             NUMBER REFERENCES GMAIL_ANALYTICS.CORE.EMAIL_THREADS(THREAD_ID),
    GMAIL_MESSAGE_ID      VARCHAR(255) COMMENT 'Gmail API message ID',
    SENDER_CONTACT_ID     NUMBER REFERENCES GMAIL_ANALYTICS.CORE.EMAIL_CONTACTS(CONTACT_ID),
    TO_CONTACT_IDS        VARCHAR(4000) COMMENT 'JSON array of recipient contact IDs',
    CC_CONTACT_IDS        VARCHAR(4000) COMMENT 'JSON array of CC contact IDs',
    BCC_CONTACT_IDS       VARCHAR(4000) COMMENT 'JSON array of BCC contact IDs',
    SUBJECT               VARCHAR(1000),
    SNIPPET               VARCHAR(500),
    BODY_TEXT             TEXT,
    BODY_HTML             TEXT,
    SENT_AT               TIMESTAMP_NTZ,
    RECEIVED_AT           TIMESTAMP_NTZ,
    IS_READ               BOOLEAN DEFAULT FALSE,
    IS_STARRED            BOOLEAN DEFAULT FALSE,
    IS_DRAFT              BOOLEAN DEFAULT FALSE,
    IS_SENT               BOOLEAN DEFAULT FALSE,
    IS_TRASH              BOOLEAN DEFAULT FALSE,
    IS_SPAM               BOOLEAN DEFAULT FALSE,
    HAS_ATTACHMENTS       BOOLEAN DEFAULT FALSE,
    CATEGORY              VARCHAR(100),
    IMPORTANCE            VARCHAR(20) DEFAULT 'normal',
    SPAM_SCORE            FLOAT DEFAULT 0.0,
    IS_SUSPICIOUS         BOOLEAN DEFAULT FALSE,
    PHISHING_INDICATORS   VARCHAR(4000) COMMENT 'JSON phishing signal flags',
    HEADERS               VARCHAR(8000) COMMENT 'JSON email headers',
    RAW_SIZE_BYTES        NUMBER,
    GMAIL_HISTORY_ID      VARCHAR(255) COMMENT 'Gmail API history ID for incremental sync',
    CREATED_AT            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Email messages. Maps to Gmail API messages resource.';

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_ATTACHMENTS (
    ATTACHMENT_ID         NUMBER PRIMARY KEY,
    MESSAGE_ID            NUMBER REFERENCES GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES(MESSAGE_ID),
    FILENAME              VARCHAR(500),
    CONTENT_TYPE          VARCHAR(255),
    SIZE_BYTES            NUMBER,
    IS_INLINE             BOOLEAN DEFAULT FALSE,
    GMAIL_ATTACHMENT_ID   VARCHAR(255) COMMENT 'Gmail API attachment ID',
    CREATED_AT            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Attachment metadata. Maps to Gmail API attachments.';

CREATE OR REPLACE TABLE GMAIL_ANALYTICS.CORE.EMAIL_MESSAGE_LABEL_MAP (
    MESSAGE_ID  NUMBER REFERENCES GMAIL_ANALYTICS.CORE.EMAIL_MESSAGES(MESSAGE_ID),
    LABEL_ID    NUMBER REFERENCES GMAIL_ANALYTICS.CORE.EMAIL_LABELS(LABEL_ID),
    APPLIED_AT  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (MESSAGE_ID, LABEL_ID)
) COMMENT = 'Message-to-label many-to-many mapping.';