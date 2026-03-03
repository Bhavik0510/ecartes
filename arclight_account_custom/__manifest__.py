{
    'name': 'Arclight Account Custom',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Custom accounting tweaks for Arclight (Dynamic Reports, GST, etc.).',
    'depends': [
        'dynamic_accounts_report',
        'texbyte_gstr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/item_ledger_wizard_views.xml',
        'report/item_ledger_report.xml',
        'views/dynamic_accounts_menu.xml',
        'views/hsn_summary_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
