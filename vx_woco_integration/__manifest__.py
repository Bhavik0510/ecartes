# -*- coding: utf-8 -*-
{
    "name": "WoCo Integration",
    'summary': 'WoCo Integration',
    'description': """ To Handle Request response of WoCo. """,
    "author": "Virtual-X Solution",
    "company": "Virtual-X Solution",
    "version": "1.0",
    'category': 'hr',
    "depends": ["hr"],
    "data": [
        'security/ir.model.access.csv',
        'views/woco_views.xml',
        'views/hr_views.xml',
        'data/data.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3'
}
