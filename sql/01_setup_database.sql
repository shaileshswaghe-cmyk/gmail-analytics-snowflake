-- =============================================================================
-- Step 1: Create database and schemas
-- =============================================================================

CREATE DATABASE IF NOT EXISTS GMAIL_ANALYTICS
    COMMENT = 'Gmail analytics platform for email metadata, threading, and engagement analysis';

CREATE SCHEMA IF NOT EXISTS GMAIL_ANALYTICS.CORE
    COMMENT = 'Core normalized tables for Gmail data';

CREATE SCHEMA IF NOT EXISTS GMAIL_ANALYTICS.ANALYTICS
    COMMENT = 'Analytics views and reporting layer';
