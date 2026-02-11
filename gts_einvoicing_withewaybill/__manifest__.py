# -*- encoding: utf-8 -*-

{
    'name': 'GST E-Invoicing And E-way Bill with 5 hrs support',
    'version': '18.0.0.1',
    'category': 'Integration',
    'summary': """Generate E-invoice, E-invoice Generate, generate qr-code, generate E-invoice Eway bill,generate 
    E-invoice Eway bill with qr code, generate eway bill invoice, eway bill generate, E-invoice eway 
    bill generate, e-way bill generation, e-way bill generation with qr code, e-way bill PDF format, 
    e-way bill PDF format with qr code, generate invoice, Invoice, generate e-way bill, generate eway, 
    generate E-invoices, generate, E-Invoice, einvoice, Eway bill""",
    'live_test_url': 'https://www.youtube.com/watch?v=U9NfSEzM1hI',

    'author': 'Geo Technosoft',
    'description': 'This module Allows you to generate E-INVOICE',
    'sequence': 1,
    'website': 'https://www.geotechnosoft.com',
    'depends': ['account', 'stock',],
    'data': [
        'security/einvoice_user_groups.xml',
        'security/ir.model.access.csv',
        # 'data/res_country_state_data.xml',
        'data/uom_data.xml',
        'wizard/cancel_einvoice.xml',
        'wizard/cancel_eway.xml',
        'reports/invoice_report.xml',
        # 'views/einvoicing_configuration.xml',
        'views/account_invoice.xml',
        'views/stock_warehouse.xml',
    ],
    'images': ['static/description/banner.png'],
    'price': 99.00,
    'currency': 'USD',
    'license': 'OPL-1',
    'application': True,
    'installable': True,
}
