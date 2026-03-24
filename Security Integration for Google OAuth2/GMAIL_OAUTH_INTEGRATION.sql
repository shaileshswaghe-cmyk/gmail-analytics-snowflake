CREATE OR REPLACE SECURITY INTEGRATION GMAIL_OAUTH_INTEGRATION
    TYPE = API_AUTHENTICATION
    AUTH_TYPE = OAUTH2
    OAUTH_CLIENT_ID = '<Your Client ID>'
    OAUTH_CLIENT_SECRET = '<Your Client Secrete>'
    OAUTH_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
    OAUTH_AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
    OAUTH_ALLOWED_SCOPES = ('https://www.googleapis.com/auth/gmail.readonly')
    ENABLED = TRUE