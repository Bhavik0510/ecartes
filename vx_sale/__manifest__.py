# -*- coding: utf-8 -*-
{
    "name": "Sale Customisation",
    'summary': 'Sale Customisation',
    'description': """ To managae Sale related customisation """,
    "author": "Virtual-X Solution",
    "company": "Virtual-X Solution",
    "version": "1.0",
    'category': 'Sales/Sales',
    "depends": ["ecartes_sale", "purchase", "account"],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/change_dates_view.xml',
        'views/sale_views.xml',
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3'
}
