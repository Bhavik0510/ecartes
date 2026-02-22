-- Run this on the database when Odoo fails to start with:
--   "Some modules are not loaded, some dependencies or manifest may be missing: [...]"
--
-- Use when the modules are in the DB but not in addons path (e.g. after removing OCA/addons).
-- Replace ecarts_staging with your database name.
--
-- psql -U odoo -d ecarts_staging -f project/ecartes/scripts/uninstall_missing_modules.sql

UPDATE ir_module_module
SET state = 'uninstalled'
WHERE name IN (
    'account_financial_report',
    'account_financial_report_sale',
    'account_tax_balance',
    'date_range',
    'helpdesk_mgmt_crm',
    'helpdesk_mgmt_project',
    'helpdesk_mgmt_rating',
    'helpdesk_mgmt_sale',
    'helpdesk_mgmt_sale_project',
    'helpdesk_product',
    'helpdesk_type',
    'partner_statement',
    'report_xlsx',
    'report_xlsx_helper'
)
AND state != 'uninstalled';
