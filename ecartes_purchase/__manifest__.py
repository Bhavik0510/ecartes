# -*- coding: utf-8 -*-
{
    'name': "Purchase Extend",

    'summary': """ Extending Purchase Features """,

    'description': """
        Apply Access rights of the purchase orders.
    """,
    'version': '18.0.0.1',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'category': 'Purchase',
    'depends': ['purchase'],
    'data': [
        'security/purchase_security.xml',
        'security/security.xml',
        'views/purchase_views.xml',
        'views/res_users_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecartes_purchase/static/src/xml/purchase_product_label_field.xml',
            'ecartes_purchase/static/src/js/purchase_product_label_field.js',
        ],
    },
    'license': "LGPL-3"
}

