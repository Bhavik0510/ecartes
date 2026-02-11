# -*- coding: utf-8 -*-

{
    'name': 'Employee Documents',
    'version': '15.0',
    'summary': """Manages Employee Documents With Expiry Notifications.""",
    'description': """Manages Employee Related Documents with Expiry Notifications.""",
    'category': 'Documents',
    'author': "Virtual-X Solution",
    'maintainer': 'Virtual-X Solution',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_expired.xml',
        'wizard/renewed_documents.xml',
        'views/employee_check_list_view.xml',
        'views/employee_document_view.xml',
    ],
    'demo': ['data/data.xml'],
    'images': [],
    'license': 'LGPL-3',

}
