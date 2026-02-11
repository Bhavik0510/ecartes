{
    'name': "ecartes_product_warranty",
    'summary':'ecartes_product_warranty',
    'description': '''
        ecartes_product_warranty
    ''',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'category': 'Uncategorized',
    'version': '15.0.0',
    'depends': ['base','product','account','sale','ecartes_account',
        'mail','product','stock','ecartes_amc'],
    'data': [
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'security/warranty_group.xml',
        'wizard/warranty_renew_view.xml',
        'views/product_template_view.xml',
        'views/product_warranty_view.xml',
        'views/warranty_claim_view.xml',
        'views/warranty_terms_view.xml',
        'views/amc_view.xml',
        'views/account_move_view.xml',
        'report/product_warranty_template.xml',
        'wizard/warranty_status_view.xml'        
    ],
    'license': 'LGPL-3',
}
