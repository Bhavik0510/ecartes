#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uninstall modules that are in the database but not present in addons path.

Run with Odoo shell (replace ecarts_staging with your DB name):
  python odoo-bin shell -d ecarts_staging -c /path/to/odoo.conf --addons-path=...

Then in the shell:
  >>> exec(open('project/ecartes/scripts/uninstall_missing_modules.py').read())

Or run as a one-liner (from repo root, with correct addons-path and config):
  python odoo-bin shell -d ecarts_staging -c odoo.conf -c conf/test.conf --addons-path=addons,enterprise,project/ecartes,custom\ addons --no-http <<'PY'
from odoo import api, SUPERUSER_ID
MISSING = [
    'account_financial_report', 'account_financial_report_sale',
    'account_tax_balance', 'date_range',
    'helpdesk_mgmt_crm', 'helpdesk_mgmt_project', 'helpdesk_mgmt_rating',
    'helpdesk_mgmt_sale', 'helpdesk_mgmt_sale_project',
    'helpdesk_product', 'helpdesk_type',
    'partner_statement', 'report_xlsx', 'report_xlsx_helper',
]
with api.Environment.manage():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        Mod = env['ir.module.module']
        for name in MISSING:
            mod = Mod.search([('name', '=', name)], limit=1)
            if mod:
                print('Uninstalling:', name, '(state was: %s)' % mod.state)
                mod.button_immediate_uninstall()
            else:
                print('Not in DB:', name)
        cr.commit()
print('Done.')
PY
"""
from odoo import api, SUPERUSER_ID

# Modules that Odoo reports as "not loaded" (in DB but not in addons path)
MISSING_MODULES = [
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
    'report_xlsx_helper',
]

# Use env from shell (odoo-bin shell)
env = globals().get('env')
if not env:
    print("Run this script inside 'odoo-bin shell -d YOUR_DB' so that 'env' exists.")
else:
    Mod = env['ir.module.module']
    for name in MISSING_MODULES:
        mod = Mod.search([('name', '=', name)], limit=1)
        if mod:
            print('Uninstalling:', name, '(state: %s)' % mod.state)
            try:
                mod.button_immediate_uninstall()
            except Exception as e:
                print('  Error:', e)
        else:
            print('Not in DB:', name)
    env.cr.commit()
    print('Done. Restart Odoo and run the upgrade again.')
