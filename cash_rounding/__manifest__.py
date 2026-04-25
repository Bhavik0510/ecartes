{
    'name': 'Cash Rounding',
    'version': '1.0',
    'category': 'cash rounding',
    'depends': ['sale', 'account', 'purchase', 'ecartes_sale'],
    'data': [
        'views/sale_order_view.xml',
        'views/purchase_order_views.xml',
        'views/account_move.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}