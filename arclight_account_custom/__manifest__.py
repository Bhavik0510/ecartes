{
    'name': 'Arclight Account Custom',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Custom accounting tweaks for Arclight (Dynamic Reports, GST, etc.).',
    'depends': [
        'dynamic_accounts_report',
        'texbyte_gstr',
        'stock',
<<<<<<< Updated upstream
        'sale_management',
        'sale_stock',
=======
        'ecartes_report',
>>>>>>> Stashed changes
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/item_ledger_wizard_views.xml',
        'report/item_ledger_report.xml',
<<<<<<< Updated upstream
        'views/pending_dc_report_wizard_views.xml',
=======
        'report/tax_invoice_template.xml',
        'report/invoice_slip_inherit.xml',
        'report/account_tax_invoice_report_action.xml',
>>>>>>> Stashed changes
        'views/dynamic_accounts_menu.xml',
        'views/hsn_summary_views.xml',
        'views/stock_move_line_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
