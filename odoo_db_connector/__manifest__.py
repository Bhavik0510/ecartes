# -*- coding: utf-8 -*- 

{
    'name': 'Odoo Cross-DB Sync',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Sync Invoices and Products to an external Odoo Database',
    'depends': ['account', 'stock', 'sale'],
    'data': [
        'data/cron.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
