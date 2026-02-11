{
    'name': 'Service Desk',
    'category': 'Service Desk',
    'summary': """
        Process addon for the Website Service Desk application.
    """,
    'author': 'Tecblic Pvt Ltd',
    'website': 'https://www.tecblic.com',
    'license': 'LGPL-3',
    'version': '15.0.1.4.0',
    'depends': [
        'generic_request',
    ],
    'data': [
        'data/init_data.xml',
        'data/request_type_incident.xml',
    ],
    'images': [''],
    'installable': True,
    'application': True,
    'auto_install': False,
}
