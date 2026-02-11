{
    'name': "Ecart Helpdesk ",

    'summary': """
        Help desk
    """,

    'author': 'Tecblic Pvt Ltd',
    'website': 'https://www.tecblic.com',
    'version': '15.0.1.5.0',
    'category': 'Helpdesk',

    # any module necessary for this one to work correctly
    'depends': [
        'generic_request',
        'crnd_service_desk',
        'crnd_wsd',
    ],

    # always loaded
    'data': [
    ],
    'images': [''],
    'demo': [],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',

    'price': 0.0,
    'currency': 'EUR',
    "live_test_url": "https://yodoo.systems/saas/"
                     "template/bureaucrat-helpdesk-lite-14-0-demo-246",
}
