{
    'name': "Generic Tag",

    'summary': """
        Generic tag management.
    """,

    'author': 'Tecblic Pvt Ltd',
    'website': 'https://www.tecblic.com',

    'category': 'Generic Tags',
    'version': '15.0.2.7.0',

    "depends": [
        "base",
    ],

    "data": [
        'security/base_security.xml',
        'security/ir.model.access.csv',
        'views/generic_tag_view.xml',
        'views/generic_tag_category_view.xml',
        'views/generic_tag_model_view.xml',
        'wizard/wizard_manage_tags.xml',
    ],
    'images': [''],
    "installable": True,
    "application": True,
    'license': 'LGPL-3',
}
