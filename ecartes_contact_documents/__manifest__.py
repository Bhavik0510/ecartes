# -*- coding: utf-8 -*-

{
    'name': 'Contact Documents',
    'version': '15.0',
    'summary': """Manages Contact Documents With Expiry Notifications.""",
    'description': """Manages Contact Related Documents with Expiry Notifications.""",
    'category': 'Uncategorized',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'depends': ['base','contacts'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/renewed_documents.xml',
        'views/Contact_document_view.xml',
        'views/document_master.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
}
