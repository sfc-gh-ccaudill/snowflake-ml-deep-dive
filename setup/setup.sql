-- ============================================================
-- Snowflake ML Deep Dive: Infrastructure Setup
-- ============================================================
-- This script creates the shared infrastructure needed for all
-- workshop sessions. All statements are idempotent (IF NOT EXISTS).
--
-- Prerequisites:
--   - SYSADMIN role (or equivalent with CREATE DATABASE, CREATE COMPUTE POOL)
--   - SPCS enabled on the account
-- ============================================================

USE ROLE SYSADMIN;

-- == Database & Schema ==
CREATE DATABASE IF NOT EXISTS ML_DEMO_PIPELINE_DB;
CREATE SCHEMA IF NOT EXISTS ML_DEMO_PIPELINE_DB.HEALTHCARE;

USE DATABASE ML_DEMO_PIPELINE_DB;
USE SCHEMA HEALTHCARE;

-- == Warehouse ==
CREATE WAREHOUSE IF NOT EXISTS ML_DEMO_WAREHOUSE
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- == Stages ==
CREATE STAGE IF NOT EXISTS JOB_PAYLOADS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- == Compute Pools ==
CREATE COMPUTE POOL IF NOT EXISTS ML_DEMO_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 6
  INSTANCE_FAMILY = CPU_X64_S;

CREATE COMPUTE POOL IF NOT EXISTS NOTEBOOK_GPU_S
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = GPU_NV_S;

CREATE COMPUTE POOL IF NOT EXISTS NOTEBOOK_CPU_S
  MIN_NODES = 1
  MAX_NODES = 4
  INSTANCE_FAMILY = CPU_X64_S;

-- == Network Rules (pip install in notebooks) ==
CREATE OR REPLACE NETWORK RULE pypi_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = (
    'pypi.org',
    'raw.githubusercontent.com',
    'pypi.python.org',
    'pythonhosted.org',
    'files.pythonhosted.org'
  );

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
  ALLOWED_NETWORK_RULES = (pypi_network_rule)
  ENABLED = TRUE;

GRANT USAGE ON INTEGRATION pypi_access_integration TO ROLE SYSADMIN;

-- == Git Integration (for pulling repo into Snowflake Notebooks) ==
CREATE OR REPLACE API INTEGRATION git_int
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com')
  ENABLED = TRUE
  ALLOWED_AUTHENTICATION_SECRETS = ALL;

GRANT USAGE ON INTEGRATION git_int TO ROLE SYSADMIN;

-- == Grants ==
GRANT USAGE ON COMPUTE POOL ML_DEMO_COMPUTE_POOL TO ROLE SYSADMIN;
GRANT USAGE ON COMPUTE POOL NOTEBOOK_GPU_S TO ROLE SYSADMIN;
GRANT USAGE ON COMPUTE POOL NOTEBOOK_CPU_S TO ROLE SYSADMIN;
