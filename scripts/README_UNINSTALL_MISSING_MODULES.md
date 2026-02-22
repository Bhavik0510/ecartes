# Fix: "Some modules are not loaded, some dependencies or manifest may be missing"

## Cause

The database has these modules registered as **installed** (or to upgrade), but the actual addon directories are **not** in your `addons_path`:

- `account_financial_report`, `account_financial_report_sale`, `account_tax_balance`
- `date_range`
- `helpdesk_mgmt_crm`, `helpdesk_mgmt_project`, `helpdesk_mgmt_rating`, `helpdesk_mgmt_sale`, `helpdesk_mgmt_sale_project`
- `helpdesk_product`, `helpdesk_type`
- `partner_statement`
- `report_xlsx`, `report_xlsx_helper`

That usually happens after:

- Migrating from another instance that had OCA/community addons.
- Removing an addons directory from `addons_path`.
- Upgrading Odoo and dropping addons that are not yet available for the new version.

Your **ecartes** project does **not** depend on these modules in code: `base_accounting_kit` implements its own financial reports; `helpdesk_mgmt` is the only helpdesk dependency and it is inside `project/ecartes`.

## Option 1: SQL (use when Odoo does not start)

If the server fails to load the registry, run this on the target database:

```bash
psql -U odoo -d ecarts_staging -f project/ecartes/scripts/uninstall_missing_modules.sql
```

Adjust `-U` and database name as needed. Then restart Odoo and run the upgrade again.

## Option 2: Odoo shell (when Odoo can start)

If the server starts but upgrade still complains, you can uninstall via shell:

```bash
# From repo root, with your config and addons_path
python odoo-bin shell -d ecarts_staging -c conf/test.conf
```

Then in the shell:

```python
exec(open('project/ecartes/scripts/uninstall_missing_modules.py').read())
```

## After running

Restart Odoo and run your upgrade again. If you later need any of these modules (e.g. OCA `report_xlsx`), add the corresponding addons to `addons_path` and install them again from the Apps menu.
