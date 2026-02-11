# -*- coding: utf-8 -*-
{
    'name':'Crm Customization',
    'summary':'This is using for customization in crm',
    'description': '''
        crm custom
    ''',
    'category': 'base',
    'version': '18.0.0.1',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'depends': [
        'crm','ecartes_contact', 'sale_crm'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/tender_pipeline_lost_views.xml',
        'views/crm.xml',
        'views/crm_stage_view.xml',
        'views/crm_team_views.xml',
        'views/sale_views.xml',
        'views/tender_pipeline_views.xml',
        'wizard/crm_lead2opportunity_partner_views.xml',
        'views/menu.xml'
    ],
    'license': 'LGPL-3',
}
