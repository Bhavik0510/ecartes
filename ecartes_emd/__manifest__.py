{
    'name':'ecartes_emd',
    'summary':'ecartes_emd',
    'description': '''
        ecartes_emd
    ''',
    'category': 'base',
    'version': '18.0.0.1',
    'author': 'Virtual-X Solution',
    'company': 'Virtual-X Solution',
    'depends': ['base','ecartes_crm','web_notify'],
    'data': [
        'security/emd_group.xml',
        'security/ir.model.access.csv',
        'wizard/return_emd_view.xml',
        'wizard/issue.xml',
        'data/mail_data.xml',
        'views/emd.xml',
        'report/report.xml',
        'report/emd_report_template.xml',
        'wizard/reject_reason_view.xml',
        'data/mail_template.xml',
        'data/emd_validity_check_mail_cron.xml',
    ],
    'license': 'LGPL-3',
}
