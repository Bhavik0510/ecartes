{
    'name': "Ecarte Work From Home",

    'summary': """
        Manage Ecarte Work From Home""",

    'description': """
        Manage Ecarte Work From Home
    """,

    'version': '15.0',

    'author': "Virtual-X Solution",

    # any module necessary for this one to work correctly
    'depends': ['base','mail','portal','utm','hr_attendance','ecartes_leaves'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/ecarte_work_from_home_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'license': 'LGPL-3',
}
# -*- coding: utf-8 -*-
