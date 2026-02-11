{
    'name': "HelpDesk Extend",
    'summary':'Extending the existing functionality',
    'description': '''
        Extending the functionality
    ''',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'category': 'HelpDesk',
    'version': '1.0',
    'depends': ['helpdesk_mgmt', 'sale', 'ecartes_amc', 'ecartes_product_warranty'],
    'data': [
        'views/helpdesk_ticket_view.xml',
        'views/product_warranty_view.xml',
        'views/amc_views.xml'
    ],
    'license': 'LGPL-3',
}
