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
        'views/purchase_views.xml'
    ],
    'license': "LGPL-3"
}

