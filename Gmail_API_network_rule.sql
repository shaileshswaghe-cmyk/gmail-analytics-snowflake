CREATE OR REPLACE NETWORK RULE GMAIL_ANALYTICS.CORE.GMAIL_API_NETWORK_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = ('gmail.googleapis.com', 'oauth2.googleapis.com', 'accounts.google.com')