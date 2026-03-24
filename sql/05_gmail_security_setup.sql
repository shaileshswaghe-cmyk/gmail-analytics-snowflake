-- =============================================================================
-- Gmail API security objects (update with your credentials)
-- =============================================================================

CREATE OR REPLACE SECURITY INTEGRATION GMAIL_OAUTH_INTEGRATION
    TYPE = API_AUTHENTICATION
    AUTH_TYPE = OAUTH2
    OAUTH_CLIENT_ID = '<your-google-client-id>'
    OAUTH_CLIENT_SECRET = '<your-google-client-secret>'
    OAUTH_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
    OAUTH_AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
    OAUTH_ALLOWED_SCOPES = ('https://www.googleapis.com/auth/gmail.readonly')
    ENABLED = TRUE;

CREATE OR REPLACE NETWORK RULE GMAIL_ANALYTICS.CORE.GMAIL_API_NETWORK_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = ('gmail.googleapis.com', 'oauth2.googleapis.com', 'accounts.google.com');

CREATE OR REPLACE SECRET GMAIL_ANALYTICS.CORE.GMAIL_OAUTH_SECRET
    TYPE = OAUTH2
    API_AUTHENTICATION = GMAIL_OAUTH_INTEGRATION;

-- Requires non-trial account:
-- CREATE EXTERNAL ACCESS INTEGRATION GMAIL_API_ACCESS_INTEGRATION
--     ALLOWED_NETWORK_RULES = (GMAIL_ANALYTICS.CORE.GMAIL_API_NETWORK_RULE)
--     ALLOWED_AUTHENTICATION_SECRETS = (GMAIL_ANALYTICS.CORE.GMAIL_OAUTH_SECRET)
--     ENABLED = TRUE;